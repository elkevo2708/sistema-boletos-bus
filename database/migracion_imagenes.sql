-- Imágenes subidas desde el panel. Idempotente: no borra boletos, viajes ni fotos viejas.
-- El binario vive en `imagenes`. El contenido guarda `bd/{id}` o una URL ya existente.

CREATE TABLE IF NOT EXISTS imagenes (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(255) NOT NULL,
  tipo_mime VARCHAR(64) NOT NULL,
  tamano INT UNSIGNED NOT NULL,
  contenido LONGBLOB NOT NULL,
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

ALTER TABLE anuncios MODIFY imagen VARCHAR(500) NULL;
ALTER TABLE blog_posts MODIFY imagen VARCHAR(500) NULL;
ALTER TABLE galeria MODIFY archivo VARCHAR(500) NOT NULL;
ALTER TABLE portada MODIFY poster VARCHAR(500) NULL;
ALTER TABLE turismo_fichas MODIFY imagen VARCHAR(500) NULL;
ALTER TABLE turismo_eventos MODIFY imagen VARCHAR(500) NULL;
ALTER TABLE turismo_galeria MODIFY archivo VARCHAR(500) NOT NULL;
