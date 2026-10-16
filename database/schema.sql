-- VíaAndina: esquema de venta de boletos de bus.
-- MySQL 8, InnoDB, utf8mb4. El reloj de negocio es hora de Colombia (UTC-5),
-- configurada en el servidor (--default-time-zone=-05:00).

SET NAMES utf8mb4;
CREATE DATABASE IF NOT EXISTS boletos CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE boletos;

-- El servidor temporal de inicialización puede seguir en UTC. La sesión
-- de este script y el mysqld definitivo usan hora de Colombia.
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
SELECT r.id, 'Ana', 'Beltrán', '1000000001', 'admin@viaandina.local',
       '$2b$12$0LBQd7cfqT4mme0J5F3ueO00UF4KUMbKjnLmuQVOz1Z07BCDavhly',
       '3000000001'
  FROM roles r
 WHERE r.nombre = 'administrador';

INSERT INTO ciudades (nombre, departamento) VALUES
  ('Bogotá', 'Cundinamarca'),
  ('Medellín', 'Antioquia'),
  ('Cali', 'Valle del Cauca'),
  ('Bucaramanga', 'Santander'),
  ('Barranquilla', 'Atlántico'),
  ('Cartagena', 'Bolívar');

INSERT INTO rutas (origen_id, destino_id, duracion_min, precio_base)
SELECT o.id, d.id, x.duracion_min, x.precio_base
  FROM (
    SELECT 'Bogotá' AS origen, 'Medellín' AS destino, 480 AS duracion_min, 89000.00 AS precio_base
    UNION ALL SELECT 'Medellín', 'Bogotá', 480, 89000.00
    UNION ALL SELECT 'Bogotá', 'Cali', 540, 95000.00
    UNION ALL SELECT 'Cali', 'Bogotá', 540, 95000.00
    UNION ALL SELECT 'Medellín', 'Cali', 480, 82000.00
    UNION ALL SELECT 'Cali', 'Medellín', 480, 82000.00
    UNION ALL SELECT 'Bogotá', 'Bucaramanga', 420, 76000.00
    UNION ALL SELECT 'Bucaramanga', 'Bogotá', 420, 76000.00
    UNION ALL SELECT 'Barranquilla', 'Cartagena', 150, 32000.00
    UNION ALL SELECT 'Cartagena', 'Barranquilla', 150, 32000.00
  ) AS x
  JOIN ciudades o ON o.nombre = x.origen
  JOIN ciudades d ON d.nombre = x.destino;

INSERT INTO buses (placa, numero_disco, capacidad, pisos, estado) VALUES
  ('RUA101', '101', 40, 1, 'operativo'),
  ('RUA202', '202', 40, 2, 'operativo'),
  ('MNT303', '303', 20, 1, 'mantenimiento');

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
    SELECT 'Bogotá' AS origen, 'Medellín' AS destino, '101' AS disco, 1 AS dia, '06:00:00' AS hora
    UNION ALL SELECT 'Medellín', 'Bogotá', '101', 1, '15:00:00'
    UNION ALL SELECT 'Bogotá', 'Bucaramanga', '101', 2, '06:00:00'
    UNION ALL SELECT 'Bucaramanga', 'Bogotá', '101', 2, '14:00:00'
    UNION ALL SELECT 'Bogotá', 'Cali', '202', 1, '07:00:00'
    UNION ALL SELECT 'Cali', 'Bogotá', '202', 1, '17:00:00'
    UNION ALL SELECT 'Barranquilla', 'Cartagena', '202', 2, '08:00:00'
    UNION ALL SELECT 'Cartagena', 'Barranquilla', '202', 2, '11:00:00'
    UNION ALL SELECT 'Medellín', 'Cali', '202', 2, '14:00:00'
    UNION ALL SELECT 'Cali', 'Medellín', '202', 3, '06:00:00'
  ) AS x
  JOIN ciudades o ON o.nombre = x.origen
  JOIN ciudades d ON d.nombre = x.destino
  JOIN rutas r ON r.origen_id = o.id AND r.destino_id = d.id
  JOIN buses b ON b.numero_disco = x.disco;
