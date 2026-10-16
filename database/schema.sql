-- Cooperativa de Transporte La Maná: esquema de venta de boletos.
-- MySQL 8, InnoDB, utf8mb4. El reloj de negocio es hora de Ecuador (UTC-5),
-- configurada en el servidor (--default-time-zone=-05:00).

SET NAMES utf8mb4;
CREATE DATABASE IF NOT EXISTS boletos CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE boletos;

-- El servidor temporal de inicialización puede seguir en UTC. La sesión
-- de este script y el mysqld definitivo usan hora de Ecuador.
SET time_zone = '-05:00';

CREATE TABLE roles (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(50) NOT NULL,
  descripcion VARCHAR(255) NULL,
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_roles_nombre (nombre)
) ENGINE=InnoDB;

CREATE TABLE usuarios (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  rol_id INT UNSIGNED NOT NULL,
  nombre VARCHAR(120) NOT NULL,
  apellido VARCHAR(120) NOT NULL,
  documento VARCHAR(20) NOT NULL,
  email VARCHAR(180) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  telefono VARCHAR(30) NULL,
  activo TINYINT(1) NOT NULL DEFAULT 1,
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_usuarios_email (email),
  UNIQUE KEY uk_usuarios_documento (documento),
  CONSTRAINT fk_usuarios_rol FOREIGN KEY (rol_id) REFERENCES roles (id)
) ENGINE=InnoDB;

CREATE TABLE refresh_tokens (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  usuario_id INT UNSIGNED NOT NULL,
  token_hash CHAR(64) NOT NULL,
  expira_en DATETIME NOT NULL,
  revocado TINYINT(1) NOT NULL DEFAULT 0,
  revocado_en DATETIME NULL,
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_refresh_hash (token_hash),
  KEY idx_refresh_usuario (usuario_id),
  CONSTRAINT fk_refresh_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
) ENGINE=InnoDB;

CREATE TABLE buses (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  placa VARCHAR(10) NOT NULL,
  numero_disco VARCHAR(10) NOT NULL,
  capacidad TINYINT UNSIGNED NOT NULL,
  pisos TINYINT UNSIGNED NOT NULL,
  estado ENUM('operativo', 'mantenimiento', 'inactivo') NOT NULL DEFAULT 'operativo',
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_buses_placa (placa),
  UNIQUE KEY uk_buses_disco (numero_disco),
  CONSTRAINT chk_buses_capacidad CHECK (capacidad BETWEEN 1 AND 100),
  CONSTRAINT chk_buses_pisos CHECK (pisos BETWEEN 1 AND 2)
) ENGINE=InnoDB;

CREATE TABLE asientos (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  bus_id INT UNSIGNED NOT NULL,
  numero SMALLINT UNSIGNED NOT NULL,
  piso TINYINT UNSIGNED NOT NULL,
  fila TINYINT UNSIGNED NOT NULL,
  columna TINYINT UNSIGNED NOT NULL,
  tipo ENUM('ventana', 'pasillo', 'individual') NOT NULL DEFAULT 'ventana',
  CONSTRAINT fk_asientos_bus FOREIGN KEY (bus_id) REFERENCES buses (id),
  UNIQUE KEY uk_asiento_numero (bus_id, numero),
  UNIQUE KEY uk_asiento_posicion (bus_id, piso, fila, columna)
) ENGINE=InnoDB;

CREATE TABLE ciudades (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(120) NOT NULL,
  departamento VARCHAR(120) NOT NULL,
  UNIQUE KEY uk_ciudades_nombre_depto (nombre, departamento)
) ENGINE=InnoDB;

CREATE TABLE rutas (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  origen_id INT UNSIGNED NOT NULL,
  destino_id INT UNSIGNED NOT NULL,
  duracion_min INT UNSIGNED NOT NULL,
  precio_base DECIMAL(10, 2) NOT NULL,
  activa TINYINT(1) NOT NULL DEFAULT 1,
  CONSTRAINT fk_rutas_origen FOREIGN KEY (origen_id) REFERENCES ciudades (id),
  CONSTRAINT fk_rutas_destino FOREIGN KEY (destino_id) REFERENCES ciudades (id),
  CONSTRAINT chk_rutas_distintas CHECK (origen_id <> destino_id),
  CONSTRAINT chk_rutas_duracion CHECK (duracion_min > 0),
  CONSTRAINT chk_rutas_precio CHECK (precio_base > 0),
  UNIQUE KEY uk_rutas_par (origen_id, destino_id)
) ENGINE=InnoDB;

CREATE TABLE viajes (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  ruta_id INT UNSIGNED NOT NULL,
  bus_id INT UNSIGNED NOT NULL,
  salida DATETIME NOT NULL,
  llegada_est DATETIME NOT NULL,
  precio DECIMAL(10, 2) NOT NULL,
  estado ENUM('programado', 'abordando', 'en_ruta', 'finalizado', 'cancelado') NOT NULL DEFAULT 'programado',
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_viajes_ruta FOREIGN KEY (ruta_id) REFERENCES rutas (id),
  CONSTRAINT fk_viajes_bus FOREIGN KEY (bus_id) REFERENCES buses (id),
  CONSTRAINT chk_viajes_llegada CHECK (llegada_est > salida),
  CONSTRAINT chk_viajes_precio CHECK (precio > 0),
  KEY idx_viajes_busqueda (ruta_id, salida, estado),
  KEY idx_viajes_bus_horario (bus_id, salida, llegada_est)
) ENGINE=InnoDB;

CREATE TABLE boletos (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  codigo CHAR(12) NOT NULL,
  viaje_id INT UNSIGNED NOT NULL,
  asiento_id INT UNSIGNED NOT NULL,
  usuario_id INT UNSIGNED NOT NULL,
  pasajero_nombre VARCHAR(180) NOT NULL,
  pasajero_documento VARCHAR(20) NOT NULL,
  precio DECIMAL(10, 2) NOT NULL,
  estado ENUM('reservado', 'pagado', 'cancelado', 'expirado', 'usado') NOT NULL DEFAULT 'reservado',
  reservado_hasta DATETIME NULL,
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  ocupa_asiento TINYINT
    GENERATED ALWAYS AS (
      CASE
        WHEN estado IN ('reservado', 'pagado', 'usado') THEN 1
        ELSE NULL
      END
    ) STORED,
  UNIQUE KEY uk_boleto_codigo (codigo),
  UNIQUE KEY uk_boleto_asiento (viaje_id, asiento_id, ocupa_asiento),
  KEY idx_boletos_reserva (estado, reservado_hasta),
  KEY idx_boletos_usuario (usuario_id),
  CONSTRAINT fk_boletos_viaje FOREIGN KEY (viaje_id) REFERENCES viajes (id),
  CONSTRAINT fk_boletos_asiento FOREIGN KEY (asiento_id) REFERENCES asientos (id),
  CONSTRAINT fk_boletos_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
  CONSTRAINT chk_boletos_precio CHECK (precio > 0),
  CONSTRAINT chk_boletos_reserva_hasta CHECK (
    (estado = 'reservado' AND reservado_hasta IS NOT NULL)
    OR estado <> 'reservado'
  )
) ENGINE=InnoDB;

CREATE TABLE pagos (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  boleto_id BIGINT UNSIGNED NOT NULL,
  referencia_ext VARCHAR(64) NOT NULL,
  monto DECIMAL(10, 2) NOT NULL,
  metodo ENUM('tarjeta', 'transferencia', 'payphone', 'efectivo') NOT NULL DEFAULT 'efectivo',
  proveedor VARCHAR(40) NOT NULL DEFAULT 'simulado:efectivo',
  estado ENUM('pendiente', 'aprobado', 'rechazado') NOT NULL DEFAULT 'aprobado',
  pagado_en DATETIME NULL,
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_pago_ref (referencia_ext),
  UNIQUE KEY uk_pago_boleto (boleto_id),
  KEY idx_pagos_estado_fecha (estado, pagado_en),
  CONSTRAINT fk_pagos_boleto FOREIGN KEY (boleto_id) REFERENCES boletos (id),
  CONSTRAINT chk_pagos_monto CHECK (monto > 0)
) ENGINE=InnoDB;

CREATE TABLE auditoria (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  usuario_id INT UNSIGNED NULL,
  accion VARCHAR(80) NOT NULL,
  entidad VARCHAR(80) NOT NULL,
  entidad_id VARCHAR(64) NULL,
  detalle JSON NULL,
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_auditoria_entidad (entidad, entidad_id),
  CONSTRAINT fk_auditoria_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
) ENGINE=InnoDB;

CREATE TABLE blog_posts (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  slug VARCHAR(160) NOT NULL,
  titulo VARCHAR(180) NOT NULL,
  resumen VARCHAR(400) NOT NULL,
  cuerpo MEDIUMTEXT NOT NULL,
  categoria ENUM('noticia', 'destino') NOT NULL,
  imagen VARCHAR(255) NULL,
  publicado TINYINT(1) NOT NULL DEFAULT 1,
  publicado_en DATETIME NOT NULL,
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_blog_slug (slug),
  KEY idx_blog_publicados (publicado, publicado_en)
) ENGINE=InnoDB;

CREATE TABLE anuncios (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  titulo VARCHAR(140) NOT NULL,
  mensaje VARCHAR(500) NOT NULL,
  enlace VARCHAR(255) NULL,
  tipo ENUM('banner', 'modal') NOT NULL DEFAULT 'banner',
  activo TINYINT(1) NOT NULL DEFAULT 1,
  inicio DATE NOT NULL,
  fin DATE NOT NULL,
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT chk_anuncios_fechas CHECK (fin >= inicio),
  KEY idx_anuncios_vigencia (activo, inicio, fin)
) ENGINE=InnoDB;

CREATE TABLE galeria (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  titulo VARCHAR(140) NOT NULL,
  descripcion VARCHAR(300) NULL,
  categoria ENUM('buses', 'destinos', 'terminales') NOT NULL,
  archivo VARCHAR(255) NOT NULL,
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_galeria_archivo (archivo),
  KEY idx_galeria_categoria (categoria)
) ENGINE=InnoDB;

DELIMITER $$

CREATE TRIGGER trg_boletos_before_insert
BEFORE INSERT ON boletos
FOR EACH ROW
BEGIN
  DECLARE v_bus_viaje INT UNSIGNED;
  DECLARE v_bus_asiento INT UNSIGNED;
  DECLARE v_estado VARCHAR(20);
  DECLARE v_salida DATETIME;

  SELECT bus_id, estado, salida
    INTO v_bus_viaje, v_estado, v_salida
    FROM viajes
   WHERE id = NEW.viaje_id;

  SELECT bus_id
    INTO v_bus_asiento
    FROM asientos
   WHERE id = NEW.asiento_id;

  IF v_bus_viaje IS NULL OR v_bus_asiento IS NULL THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Viaje o asiento inexistente';
  END IF;

  IF v_bus_viaje <> v_bus_asiento THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'El asiento no pertenece al bus del viaje';
  END IF;

  IF v_estado <> 'programado' THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'El viaje no está programado';
  END IF;

  IF v_salida <= NOW() THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'El viaje ya no admite reservas';
  END IF;
END$$

CREATE TRIGGER trg_viajes_before_insert
BEFORE INSERT ON viajes
FOR EACH ROW
BEGIN
  DECLARE v_estado VARCHAR(20);
  DECLARE v_solapes INT DEFAULT 0;

  SELECT estado
    INTO v_estado
    FROM buses
   WHERE id = NEW.bus_id;

  IF v_estado IS NULL THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Bus inexistente';
  END IF;

  IF v_estado <> 'operativo' THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'El bus no está operativo';
  END IF;

  SELECT COUNT(*)
    INTO v_solapes
    FROM viajes
   WHERE bus_id = NEW.bus_id
     AND estado IN ('programado', 'abordando', 'en_ruta')
     AND NEW.salida < llegada_est
     AND NEW.llegada_est > salida;

  IF v_solapes > 0 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'El bus ya tiene un viaje en ese horario';
  END IF;
END$$

DELIMITER ;

CREATE EVENT ev_expirar_reservas
ON SCHEDULE EVERY 1 MINUTE
STARTS CURRENT_TIMESTAMP
ON COMPLETION PRESERVE
ENABLE
DO
  UPDATE boletos
     SET estado = 'expirado'
   WHERE estado = 'reservado'
     AND reservado_hasta IS NOT NULL
     AND reservado_hasta < NOW();

CREATE OR REPLACE VIEW v_disponibilidad AS
SELECT
  v.id AS viaje_id,
  a.id AS asiento_id,
  a.numero,
  a.piso,
  a.fila,
  a.columna,
  a.tipo,
  CASE
    WHEN b.estado IN ('pagado', 'usado') THEN 'ocupado'
    WHEN b.estado = 'reservado' AND b.reservado_hasta >= NOW() THEN 'ocupado'
    WHEN v.estado <> 'programado' OR v.salida <= NOW() THEN 'bloqueado'
    ELSE 'libre'
  END AS estado_asiento
FROM viajes v
JOIN asientos a ON a.bus_id = v.bus_id
LEFT JOIN boletos b
  ON b.viaje_id = v.id
 AND b.asiento_id = a.id
 AND b.ocupa_asiento = 1;

CREATE OR REPLACE VIEW v_ventas_dia AS
SELECT
  DATE(p.pagado_en) AS fecha,
  r.id AS ruta_id,
  co.nombre AS origen,
  cd.nombre AS destino,
  COUNT(p.id) AS boletos_pagados,
  SUM(p.monto) AS total
FROM pagos p
JOIN boletos b ON b.id = p.boleto_id
JOIN viajes v ON v.id = b.viaje_id
JOIN rutas r ON r.id = v.ruta_id
JOIN ciudades co ON co.id = r.origen_id
JOIN ciudades cd ON cd.id = r.destino_id
WHERE p.estado = 'aprobado'
GROUP BY DATE(p.pagado_en), r.id, co.nombre, cd.nombre;

-- Semilla -------------------------------------------------------------------

INSERT INTO roles (nombre, descripcion) VALUES
  ('administrador', 'Gestiona viajes, tarifas y el reporte de ventas'),
  ('cliente', 'Busca viajes y compra boletos');

-- Contraseña: Admin123! (bcrypt). Las credenciales están en el README.
INSERT INTO usuarios (rol_id, nombre, apellido, documento, email, password_hash, telefono)
SELECT r.id, 'Ana', 'Beltrán', '1000000001', 'admin@lamana.local',
       '$2b$12$0LBQd7cfqT4mme0J5F3ueO00UF4KUMbKjnLmuQVOz1Z07BCDavhly',
       '3000000001'
  FROM roles r
 WHERE r.nombre = 'administrador';

INSERT INTO ciudades (nombre, departamento) VALUES
  ('La Maná', 'Cotopaxi'),
  ('Quevedo', 'Los Ríos'),
  ('Latacunga', 'Cotopaxi'),
  ('Quito', 'Pichincha'),
  ('Santo Domingo', 'Santo Domingo de los Tsáchilas'),
  ('Ambato', 'Tungurahua'),
  ('Guayaquil', 'Guayas');

INSERT INTO rutas (origen_id, destino_id, duracion_min, precio_base)
SELECT o.id, d.id, x.duracion_min, x.precio_base
  FROM (
    SELECT 'La Maná' AS origen, 'Quevedo' AS destino, 75 AS duracion_min, 3.50 AS precio_base
    UNION ALL SELECT 'Quevedo', 'La Maná', 75, 3.50
    UNION ALL SELECT 'La Maná', 'Latacunga', 120, 5.00
    UNION ALL SELECT 'Latacunga', 'La Maná', 120, 5.00
    UNION ALL SELECT 'La Maná', 'Quito', 210, 8.00
    UNION ALL SELECT 'Quito', 'La Maná', 210, 8.00
    UNION ALL SELECT 'La Maná', 'Santo Domingo', 150, 6.00
    UNION ALL SELECT 'Santo Domingo', 'Quito', 180, 5.50
    UNION ALL SELECT 'La Maná', 'Ambato', 165, 6.50
    UNION ALL SELECT 'Quevedo', 'Guayaquil', 180, 7.00
    UNION ALL SELECT 'Guayaquil', 'Quevedo', 180, 7.00
  ) AS x
  JOIN ciudades o ON o.nombre = x.origen
  JOIN ciudades d ON d.nombre = x.destino;

INSERT INTO buses (placa, numero_disco, capacidad, pisos, estado) VALUES
  ('TLM0101', '101', 40, 1, 'operativo'),
  ('TLM0202', '202', 40, 2, 'operativo'),
  ('TLM0303', '303', 20, 1, 'mantenimiento');

-- Bus 101: un piso, 10 filas × 4 columnas (pasillo visual entre columna 2 y 3).
INSERT INTO asientos (bus_id, numero, piso, fila, columna, tipo)
WITH RECURSIVE seq AS (
  SELECT 1 AS n
  UNION ALL
  SELECT n + 1 FROM seq WHERE n < 40
)
SELECT b.id,
       seq.n,
       1,
       ((seq.n - 1) DIV 4) + 1,
       ((seq.n - 1) % 4) + 1,
       IF(((seq.n - 1) % 4) + 1 IN (1, 4), 'ventana', 'pasillo')
  FROM buses b
 CROSS JOIN seq
 WHERE b.numero_disco = '101';

-- Bus 202: dos pisos, 5 filas × 4 columnas cada uno.
INSERT INTO asientos (bus_id, numero, piso, fila, columna, tipo)
WITH RECURSIVE seq AS (
  SELECT 1 AS n
  UNION ALL
  SELECT n + 1 FROM seq WHERE n < 40
)
SELECT b.id,
       seq.n,
       IF(seq.n <= 20, 1, 2),
       (((seq.n - 1) % 20) DIV 4) + 1,
       ((seq.n - 1) % 4) + 1,
       IF(((seq.n - 1) % 4) + 1 IN (1, 4), 'ventana', 'pasillo')
  FROM buses b
 CROSS JOIN seq
 WHERE b.numero_disco = '202';

INSERT INTO viajes (ruta_id, bus_id, salida, llegada_est, precio, estado)
SELECT r.id,
       b.id,
       TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL x.dia DAY), x.hora),
       TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL x.dia DAY), x.hora) + INTERVAL r.duracion_min MINUTE,
       r.precio_base,
       'programado'
  FROM (
    SELECT 'La Maná' AS origen, 'Quevedo' AS destino, '101' AS disco, 1 AS dia, '06:30:00' AS hora
    UNION ALL SELECT 'Quevedo', 'La Maná', '101', 1, '09:00:00'
    UNION ALL SELECT 'La Maná', 'Latacunga', '101', 1, '12:00:00'
    UNION ALL SELECT 'Latacunga', 'La Maná', '101', 1, '15:30:00'
    UNION ALL SELECT 'La Maná', 'Quito', '101', 2, '06:00:00'
    UNION ALL SELECT 'Quito', 'La Maná', '101', 2, '12:00:00'
    UNION ALL SELECT 'La Maná', 'Ambato', '101', 3, '08:00:00'
    UNION ALL SELECT 'La Maná', 'Quevedo', '202', 1, '06:00:00'
    UNION ALL SELECT 'Quevedo', 'Guayaquil', '202', 1, '08:30:00'
    UNION ALL SELECT 'Guayaquil', 'Quevedo', '202', 1, '14:00:00'
    UNION ALL SELECT 'Quevedo', 'La Maná', '202', 2, '08:00:00'
    UNION ALL SELECT 'La Maná', 'Santo Domingo', '202', 2, '11:00:00'
    UNION ALL SELECT 'Santo Domingo', 'Quito', '202', 3, '08:00:00'
  ) AS x
  JOIN ciudades o ON o.nombre = x.origen
  JOIN ciudades d ON d.nombre = x.destino
  JOIN rutas r ON r.origen_id = o.id AND r.destino_id = d.id
  JOIN buses b ON b.numero_disco = x.disco;

INSERT INTO blog_posts (slug, titulo, resumen, cuerpo, categoria, imagen, publicado, publicado_en) VALUES
(
  'salida-extra-quito-en-feriado',
  'Salida extra a Quito en feriado',
  'Los viernes y domingos de feriado sumamos un turno de madrugada desde el terminal de La Maná hasta Quitumbe.',
  'La Cooperativa de Transporte La Maná habilita una salida adicional hacia Quito cuando el feriado cae en viernes o domingo. El bus parte del terminal a las 05:30 y el tiempo habitual hasta Quitumbe es de tres horas y media, según el tráfico de la vía Alóag.\n\nEl pasaje se reserva en esta boletería o en ventanilla. Recomendamos llegar veinte minutos antes: la taquilla cierra el abordaje cuando el disco enciende las luces de salida.\n\nSi viaja con equipaje de bodega, etiquételo con su nombre y el número de asiento. La unidad de dos pisos no acepta carga suelta en el pasillo.',
  'noticia',
  'noticia-horario.jpg',
  1,
  DATE_SUB(NOW(), INTERVAL 2 DAY)
),
(
  'martes-2x1-quevedo',
  'Martes 2x1 en la ruta a Quevedo',
  'El segundo pasaje de la misma compra, en las salidas de la mañana hacia Quevedo, sale a mitad de precio.',
  'De martes a martes, la ruta corta entre La Maná y Quevedo tiene una promoción sencilla: en una misma compra, el segundo boleto de las salidas de la mañana paga la mitad.\n\nAplica para los turnos de las 06:30 y las 09:00, mientras haya asientos libres. No se acumula con el descuento de estudiantes y el segundo pasajero debe viajar en el mismo bus.\n\nPuede pagarlo con tarjeta, transferencia, PayPhone o en efectivo en ventanilla. La reserva en línea sigue durando diez minutos.',
  'noticia',
  'bus-costa.jpg',
  1,
  DATE_SUB(NOW(), INTERVAL 6 DAY)
),
(
  'quevedo-rio-y-mercado',
  'Quevedo: río, mercado y una hora de camino',
  'La salida más corta de la cooperativa deja en el centro de Quevedo, a pocas cuadras del malecón.',
  'Quevedo queda a unos setenta y cinco minutos de La Maná por una vía plana, entre banano y cacao. El bus entra al terminal y, si lo prefiere, puede bajarse en el centro, cerca del mercado.\n\nVale la pena caminar el malecón al final de la tarde, cuando baja el calor, y probar el pescado de río. Si sigue hacia Guayaquil, hay combinación el mismo día en nuestra unidad de la costa: pregunte en taquilla por el turno de las 07:00.\n\nLleve efectivo menudo si va a comprar en el mercado. El pasaje de regreso a La Maná se agota los domingos por la noche.',
  'destino',
  'destino-quevedo.jpg',
  1,
  DATE_SUB(NOW(), INTERVAL 12 DAY)
),
(
  'latacunga-y-la-sierra',
  'Latacunga y la subida a la sierra',
  'En dos horas el paisaje cambia: de la humedad de La Maná al frío claro de Latacunga, con el Cotopaxi al fondo.',
  'La ruta a Latacunga sube desde el subtrópico cotopaxense hasta el valle interandino. Son dos horas si la vía está despejada, y el bus para en Saquisilí cuando hay pasajeros.\n\nEn Latacunga el terminal queda cerca del centro. Si el día está abierto, el Cotopaxi se ve desde la plaza. Muchos pasajeros siguen a Quito con nosotros al día siguiente; también puede comprar el tramo seguido Latacunga–Quito, de una hora y cuarenta y cinco minutos.\n\nLleve una chaqueta. La diferencia de temperatura con La Maná es fuerte, sobre todo en la salida de las 06:00.',
  'destino',
  'destino-latacunga.jpg',
  1,
  DATE_SUB(NOW(), INTERVAL 20 DAY)
);

INSERT INTO anuncios (titulo, mensaje, enlace, tipo, activo, inicio, fin) VALUES
(
  'Martes 2x1 a Quevedo',
  'En las salidas de la mañana, el segundo pasaje a Quevedo de la misma compra sale a mitad de precio.',
  '/noticias/martes-2x1-quevedo',
  'banner',
  1,
  CURDATE(),
  DATE_ADD(CURDATE(), INTERVAL 90 DAY)
),
(
  'Estudiantes a Quito',
  'Con cédula y carné vigente, el pasaje La Maná–Quito tiene dos dólares de descuento en ventanilla. Reserve su asiento en línea y presente el carné al abordar.',
  '/noticias/salida-extra-quito-en-feriado',
  'modal',
  1,
  CURDATE(),
  DATE_ADD(CURDATE(), INTERVAL 90 DAY)
);

INSERT INTO galeria (titulo, descripcion, categoria, archivo) VALUES
  ('Unidad La Maná', 'Librea naranja y negra de la cooperativa.', 'buses', 'bus-lamana.jpg'),
  ('Unidad de la costa', 'Disco 101, un piso, cuarenta puestos. Cubre La Maná, Quevedo y Latacunga.', 'buses', 'bus-costa.jpg'),
  ('Salón de pasajeros', 'Butacas de tela y pasillo central. Las ventanas son los asientos de columna 1 y 4.', 'buses', 'bus-interior.jpg'),
  ('Unidad de dos pisos', 'Disco 202. Sube a Santo Domingo, Ambato y la ruta larga a Guayaquil.', 'buses', 'bus-dos-pisos.jpg'),
  ('En la vía a la costa', 'Tramo habitual entre La Maná y Quevedo, al final de la tarde.', 'destinos', 'hero-ruta.jpg'),
  ('Río en Quevedo', 'Llegada a la llanura de Los Ríos.', 'destinos', 'destino-quevedo.jpg'),
  ('Latacunga y el Cotopaxi', 'El valle se abre después de la subida desde La Maná.', 'destinos', 'destino-latacunga.jpg'),
  ('Malecón de Guayaquil', 'Conexión desde Quevedo en la unidad de la tarde.', 'destinos', 'destino-guayaquil.jpg'),
  ('Terminal de La Maná', 'Andén de salida. Taquilla abierta de 05:00 a 21:00.', 'terminales', 'terminal-lamana.jpg'),
  ('Terminal en Quito', 'Llegada a Quitumbe en el turno de la madrugada.', 'terminales', 'terminal-quito.jpg'),
  ('Abordaje de madrugada', 'Pasajeros del turno extra de feriado.', 'terminales', 'noticia-horario.jpg');
