-- Portal: emprendimientos, directorio, roles de operador y taxis de ejemplo.
-- Idempotente. No borra boletos, viajes ni fichas existentes.

ALTER TABLE turismo_categorias
  MODIFY tipo ENUM(
    'atractivo', 'gastronomia', 'hospedaje', 'actividad', 'ruta', 'parroquia', 'guia', 'evento', 'emprendimiento', 'directorio'
  ) NOT NULL;

ALTER TABLE turismo_fichas
  MODIFY tipo ENUM(
    'atractivo', 'gastronomia', 'hospedaje', 'actividad', 'ruta', 'parroquia', 'guia', 'emprendimiento', 'directorio'
  ) NOT NULL;

INSERT INTO roles (nombre, descripcion)
SELECT 'operador_turismo', 'Administra el portal de turismo'
WHERE NOT EXISTS (SELECT 1 FROM roles WHERE nombre = 'operador_turismo');
INSERT INTO roles (nombre, descripcion)
SELECT 'operador_transporte', 'Administra boletos, flota y facturación'
WHERE NOT EXISTS (SELECT 1 FROM roles WHERE nombre = 'operador_transporte');
INSERT INTO roles (nombre, descripcion)
SELECT 'operador_taxi', 'Administra compañías y viajes de taxi'
WHERE NOT EXISTS (SELECT 1 FROM roles WHERE nombre = 'operador_taxi');
INSERT INTO roles (nombre, descripcion)
SELECT 'conductor', 'Conduce un taxi y actualiza su ubicación'
WHERE NOT EXISTS (SELECT 1 FROM roles WHERE nombre = 'conductor');

INSERT INTO usuarios (rol_id, nombre, apellido, documento, email, password_hash, telefono)
SELECT r.id, 'Rosa', 'Ejemplo', '9000000001', 'operador.turismo@lamana.local',
       '$2b$12$myDmYv8sc7Um6CpsX4dx9eqPtkIvqzBtNpPdJUu94HtWaoMD.J8.O', '0990000001'
FROM roles r
WHERE r.nombre = 'operador_turismo'
  AND NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'operador.turismo@lamana.local');
INSERT INTO usuarios (rol_id, nombre, apellido, documento, email, password_hash, telefono)
SELECT r.id, 'Luis', 'Ejemplo', '9000000002', 'operador.transporte@lamana.local',
       '$2b$12$myDmYv8sc7Um6CpsX4dx9eqPtkIvqzBtNpPdJUu94HtWaoMD.J8.O', '0990000002'
FROM roles r
WHERE r.nombre = 'operador_transporte'
  AND NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'operador.transporte@lamana.local');
INSERT INTO usuarios (rol_id, nombre, apellido, documento, email, password_hash, telefono)
SELECT r.id, 'Marta', 'Ejemplo', '9000000003', 'operador.taxi@lamana.local',
       '$2b$12$myDmYv8sc7Um6CpsX4dx9eqPtkIvqzBtNpPdJUu94HtWaoMD.J8.O', '0990000003'
FROM roles r
WHERE r.nombre = 'operador_taxi'
  AND NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'operador.taxi@lamana.local');

INSERT INTO turismo_categorias (tipo, nombre, slug, resumen, orden)
SELECT 'emprendimiento', 'Ejemplos', 'ejemplos', 'Fichas de muestra. No son negocios reales.', 1
WHERE NOT EXISTS (SELECT 1 FROM turismo_categorias WHERE tipo = 'emprendimiento' AND slug = 'ejemplos');
INSERT INTO turismo_categorias (tipo, nombre, slug, resumen, orden)
SELECT 'directorio', 'Ejemplos', 'ejemplos', 'Servicios de muestra para el directorio.', 1
WHERE NOT EXISTS (SELECT 1 FROM turismo_categorias WHERE tipo = 'directorio' AND slug = 'ejemplos');

INSERT INTO turismo_fichas (tipo, categoria_id, nombre, slug, resumen, cuerpo, zona, orden)
SELECT 'emprendimiento', c.id, 'Ejemplo: cacao de finca familiar', 'ejemplo-cacao-de-finca',
       'Ejemplo, no es un negocio real. Sirve para ver la ficha de un emprendimiento.',
       'Esta ficha es de demostración. No identifica una marca ni una finca concreta de La Maná. Taquilla puede reemplazarla por un emprendimiento que haya autorizado su publicación.',
       'Ejemplo', 1
FROM turismo_categorias c
WHERE c.tipo = 'emprendimiento' AND c.slug = 'ejemplos'
  AND NOT EXISTS (SELECT 1 FROM turismo_fichas WHERE tipo = 'emprendimiento' AND slug = 'ejemplo-cacao-de-finca');
INSERT INTO turismo_fichas (tipo, categoria_id, nombre, slug, resumen, cuerpo, zona, orden)
SELECT 'directorio', c.id, 'Ejemplo: farmacia del parque', 'ejemplo-farmacia-del-parque',
       'Ejemplo, no es un local real. El directorio se llena desde el panel.',
       'Esta ficha es de demostración. No publica teléfono, horario ni dirección de un negocio existente. Sirve para probar el listado hasta que un operador cargue servicios reales.',
       'Ejemplo', 1
FROM turismo_categorias c
WHERE c.tipo = 'directorio' AND c.slug = 'ejemplos'
  AND NOT EXISTS (SELECT 1 FROM turismo_fichas WHERE tipo = 'directorio' AND slug = 'ejemplo-farmacia-del-parque');

CREATE TABLE IF NOT EXISTS taxi_companias (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(160) NOT NULL,
  telefono VARCHAR(40) NOT NULL DEFAULT '',
  activa TINYINT(1) NOT NULL DEFAULT 1,
  ejemplo TINYINT(1) NOT NULL DEFAULT 0,
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS taxi_tarifas (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  compania_id INT UNSIGNED NOT NULL,
  arranque DECIMAL(8, 2) NOT NULL,
  costo_km DECIMAL(8, 2) NOT NULL,
  costo_minuto DECIMAL(8, 2) NOT NULL,
  tarifa_minima DECIMAL(8, 2) NOT NULL,
  recargo_nocturno_pct DECIMAL(5, 2) NOT NULL DEFAULT 0,
  noche_desde TIME NOT NULL DEFAULT '22:00:00',
  noche_hasta TIME NOT NULL DEFAULT '06:00:00',
  ejemplo TINYINT(1) NOT NULL DEFAULT 0,
  activa TINYINT(1) NOT NULL DEFAULT 1,
  CONSTRAINT fk_tarifa_compania FOREIGN KEY (compania_id) REFERENCES taxi_companias (id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS taxi_conductores (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  usuario_id INT UNSIGNED NOT NULL,
  compania_id INT UNSIGNED NOT NULL,
  placa VARCHAR(12) NOT NULL,
  numero_unidad VARCHAR(12) NOT NULL,
  estado ENUM('disponible', 'ocupado', 'fuera') NOT NULL DEFAULT 'fuera',
  lat DECIMAL(9, 6) NULL,
  lng DECIMAL(9, 6) NULL,
  ubicacion_en DATETIME NULL,
  foto VARCHAR(255) NULL,
  activo TINYINT(1) NOT NULL DEFAULT 1,
  ejemplo TINYINT(1) NOT NULL DEFAULT 0,
  UNIQUE KEY uk_taxi_usuario (usuario_id),
  UNIQUE KEY uk_taxi_placa (placa),
  KEY idx_taxi_estado_pos (estado, lat, lng),
  CONSTRAINT fk_taxi_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
  CONSTRAINT fk_taxi_compania FOREIGN KEY (compania_id) REFERENCES taxi_companias (id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS taxi_viajes (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  pasajero_id INT UNSIGNED NOT NULL,
  compania_id INT UNSIGNED NULL,
  conductor_id INT UNSIGNED NULL,
  estado ENUM('solicitado', 'asignado', 'en_camino', 'a_bordo', 'finalizado', 'cancelado') NOT NULL DEFAULT 'solicitado',
  origen_lat DECIMAL(9, 6) NOT NULL,
  origen_lng DECIMAL(9, 6) NOT NULL,
  destino_lat DECIMAL(9, 6) NOT NULL,
  destino_lng DECIMAL(9, 6) NOT NULL,
  destino_texto VARCHAR(180) NOT NULL DEFAULT '',
  distancia_km DECIMAL(8, 3) NOT NULL DEFAULT 0,
  duracion_min INT NOT NULL DEFAULT 1,
  tarifa_estimada DECIMAL(8, 2) NOT NULL DEFAULT 0,
  tarifa_final DECIMAL(8, 2) NULL,
  metodo_pago ENUM('efectivo', 'deuna', 'tarjeta', 'payphone') NOT NULL DEFAULT 'efectivo',
  pago_estado ENUM('pendiente', 'aprobado', 'no_aplica') NOT NULL DEFAULT 'no_aplica',
  calificacion TINYINT NULL,
  comentario VARCHAR(300) NOT NULL DEFAULT '',
  ofrecido_conductor_id INT UNSIGNED NULL,
  ofrecido_hasta DATETIME NULL,
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_taxi_viaje_estado (estado),
  KEY idx_taxi_viaje_pasajero (pasajero_id),
  CONSTRAINT fk_taxi_viaje_pasajero FOREIGN KEY (pasajero_id) REFERENCES usuarios (id),
  CONSTRAINT fk_taxi_viaje_conductor FOREIGN KEY (conductor_id) REFERENCES taxi_conductores (id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS taxi_rechazos (
  viaje_id INT UNSIGNED NOT NULL,
  conductor_id INT UNSIGNED NOT NULL,
  PRIMARY KEY (viaje_id, conductor_id)
) ENGINE=InnoDB;

INSERT INTO taxi_companias (nombre, telefono, activa, ejemplo)
SELECT 'Ejemplo: Cooperativa de Taxis del Parque', '0990000099', 1, 1
WHERE NOT EXISTS (SELECT 1 FROM taxi_companias WHERE nombre = 'Ejemplo: Cooperativa de Taxis del Parque');

INSERT INTO taxi_tarifas (
  compania_id, arranque, costo_km, costo_minuto, tarifa_minima, recargo_nocturno_pct, noche_desde, noche_hasta, ejemplo, activa
)
SELECT c.id, 0.50, 0.45, 0.08, 1.25, 15, '22:00:00', '06:00:00', 1, 1
FROM taxi_companias c
WHERE c.nombre = 'Ejemplo: Cooperativa de Taxis del Parque'
  AND NOT EXISTS (
    SELECT 1 FROM taxi_tarifas t WHERE t.compania_id = c.id AND t.ejemplo = 1
  );

INSERT INTO usuarios (rol_id, nombre, apellido, documento, email, password_hash)
SELECT r.id, 'Ejemplo', CONCAT('Conductor ', n.num), CONCAT('910000000', n.num),
       CONCAT('conductor.ejemplo', n.num, '@lamana.local'),
       '$2b$12$VBKW17ytPJZBqEalHfT9c.i61CDw/vs864fBQArAg8gq7A.NLzcqi'
FROM roles r
JOIN (
  SELECT 1 AS num UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6
) n
WHERE r.nombre = 'conductor'
  AND NOT EXISTS (SELECT 1 FROM usuarios u WHERE u.email = CONCAT('conductor.ejemplo', n.num, '@lamana.local'));

INSERT INTO taxi_conductores (usuario_id, compania_id, placa, numero_unidad, estado, lat, lng, ubicacion_en, ejemplo, activo)
SELECT u.id, c.id, CONCAT('EJ-10', n.num), CONCAT('E', n.num), 'disponible',
       -0.940600 + (n.num * 0.0012), -79.234400 + (n.num * 0.0008), NOW(), 1, 1
FROM (
  SELECT 1 AS num UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6
) n
JOIN usuarios u ON u.email = CONCAT('conductor.ejemplo', n.num, '@lamana.local')
JOIN taxi_companias c ON c.nombre = 'Ejemplo: Cooperativa de Taxis del Parque'
WHERE NOT EXISTS (SELECT 1 FROM taxi_conductores tc WHERE tc.usuario_id = u.id);
