-- Métodos de pago, intenciones y portada. Idempotente: no borra boletos ni viajes.
-- Las filas viejas de transferencia o efectivo pasan a payphone; el proveedor
-- original (por ejemplo simulado:efectivo) se conserva en la columna proveedor.

ALTER TABLE pagos MODIFY metodo VARCHAR(20) NOT NULL;
UPDATE pagos SET metodo = 'payphone' WHERE metodo IN ('transferencia', 'efectivo');
ALTER TABLE pagos MODIFY metodo ENUM('deuna', 'tarjeta', 'payphone') NOT NULL DEFAULT 'payphone';
ALTER TABLE pagos MODIFY proveedor VARCHAR(80) NOT NULL DEFAULT 'sandbox:payphone';

CREATE TABLE IF NOT EXISTS metodos_pago (
  codigo VARCHAR(20) PRIMARY KEY,
  activo TINYINT(1) NOT NULL DEFAULT 1,
  actualizado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

INSERT INTO metodos_pago (codigo, activo)
SELECT 'deuna', 1 FROM DUAL
 WHERE NOT EXISTS (SELECT 1 FROM metodos_pago WHERE codigo = 'deuna');
INSERT INTO metodos_pago (codigo, activo)
SELECT 'tarjeta', 1 FROM DUAL
 WHERE NOT EXISTS (SELECT 1 FROM metodos_pago WHERE codigo = 'tarjeta');
INSERT INTO metodos_pago (codigo, activo)
SELECT 'payphone', 1 FROM DUAL
 WHERE NOT EXISTS (SELECT 1 FROM metodos_pago WHERE codigo = 'payphone');

CREATE TABLE IF NOT EXISTS intenciones_pago (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  boleto_id BIGINT UNSIGNED NOT NULL,
  usuario_id INT UNSIGNED NOT NULL,
  metodo ENUM('deuna', 'tarjeta', 'payphone') NOT NULL,
  client_tx_id VARCHAR(64) NOT NULL,
  id_externo VARCHAR(80) NULL,
  monto DECIMAL(10, 2) NOT NULL,
  estado ENUM('pendiente', 'aprobado', 'rechazado') NOT NULL DEFAULT 'pendiente',
  proveedor VARCHAR(80) NOT NULL,
  facturacion JSON NOT NULL,
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_intencion_tx (client_tx_id),
  KEY idx_intencion_boleto (boleto_id),
  CONSTRAINT fk_intencion_boleto FOREIGN KEY (boleto_id) REFERENCES boletos (id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS portada (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  tipo ENUM('imagen', 'video') NOT NULL DEFAULT 'imagen',
  origen ENUM('archivo', 'enlace') NOT NULL DEFAULT 'enlace',
  archivo VARCHAR(255) NULL,
  enlace VARCHAR(500) NULL,
  poster VARCHAR(255) NULL,
  titulo VARCHAR(160) NOT NULL,
  subtitulo VARCHAR(300) NULL,
  texto_boton VARCHAR(80) NULL,
  enlace_boton VARCHAR(300) NULL,
  orden INT NOT NULL DEFAULT 0,
  activo TINYINT(1) NOT NULL DEFAULT 1,
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

INSERT INTO portada (tipo, origen, enlace, titulo, subtitulo, orden, activo)
SELECT 'imagen', 'enlace', '/bus-lamana.jpg',
       'Viaja desde La Maná con el asiento ya elegido.',
       'Salidas a Quevedo, Latacunga, Quito, Ambato y Guayaquil. Reserva en línea y aborda con tu código QR.',
       0, 1
 WHERE NOT EXISTS (SELECT 1 FROM portada);

UPDATE blog_posts
   SET cuerpo = REPLACE(
         cuerpo,
         'Puede pagarlo con tarjeta, transferencia, PayPhone o en efectivo en ventanilla.',
         'Puede pagarlo con DeUna!, tarjeta o PayPhone.'
       )
 WHERE cuerpo LIKE '%efectivo en ventanilla%';
