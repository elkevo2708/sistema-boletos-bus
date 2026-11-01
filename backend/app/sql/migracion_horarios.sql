-- Horario recurrente de la cooperativa. Es idempotente: se puede correr
-- sobre una base que ya tiene ciudades, rutas y viajes, sin borrar nada.
-- Cubre cada par de ciudades de la semilla, en los dos sentidos, con dos
-- salidas al día durante los próximos 30 días.

CREATE TABLE IF NOT EXISTS horarios (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  ruta_id INT UNSIGNED NOT NULL,
  bus_id INT UNSIGNED NOT NULL,
  hora_salida TIME NOT NULL,
  dias_semana CHAR(7) NOT NULL,
  activo TINYINT(1) NOT NULL DEFAULT 1,
  CONSTRAINT fk_horarios_ruta FOREIGN KEY (ruta_id) REFERENCES rutas (id),
  CONSTRAINT fk_horarios_bus FOREIGN KEY (bus_id) REFERENCES buses (id),
  CONSTRAINT chk_horarios_dias CHECK (dias_semana REGEXP '^[01]{7}$'),
  UNIQUE KEY uk_horarios_salida (ruta_id, hora_salida)
) ENGINE=InnoDB;

INSERT INTO buses (placa, numero_disco, capacidad, pisos, estado)
SELECT CONCAT('TLM', disco), disco, 40, 1, 'operativo'
  FROM (
    SELECT '401' AS disco
    UNION ALL SELECT '402' AS disco
    UNION ALL SELECT '403' AS disco
    UNION ALL SELECT '404' AS disco
    UNION ALL SELECT '405' AS disco
    UNION ALL SELECT '406' AS disco
    UNION ALL SELECT '407' AS disco
    UNION ALL SELECT '408' AS disco
    UNION ALL SELECT '409' AS disco
    UNION ALL SELECT '410' AS disco
    UNION ALL SELECT '411' AS disco
    UNION ALL SELECT '412' AS disco
    UNION ALL SELECT '413' AS disco
    UNION ALL SELECT '414' AS disco
    UNION ALL SELECT '415' AS disco
    UNION ALL SELECT '416' AS disco
    UNION ALL SELECT '417' AS disco
    UNION ALL SELECT '418' AS disco
    UNION ALL SELECT '419' AS disco
    UNION ALL SELECT '420' AS disco
    UNION ALL SELECT '421' AS disco
  ) AS flota
 WHERE NOT EXISTS (SELECT 1 FROM buses b WHERE b.numero_disco = flota.disco);

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
 WHERE b.numero_disco BETWEEN '401' AND '499'
   AND NOT EXISTS (SELECT 1 FROM asientos a WHERE a.bus_id = b.id);

INSERT INTO rutas (origen_id, destino_id, duracion_min, precio_base, activa)
SELECT o.id, d.id, x.duracion_min, x.precio_base, 1
  FROM (
    SELECT 'Quito' AS origen, 'Guayaquil' AS destino, 420 AS duracion_min, 14.00 AS precio_base
    UNION ALL SELECT 'Guayaquil', 'Quito', 420, 14.00
    UNION ALL SELECT 'Ambato', 'Guayaquil', 360, 13.00
    UNION ALL SELECT 'Guayaquil', 'Ambato', 360, 13.00
    UNION ALL SELECT 'Latacunga', 'Guayaquil', 330, 12.00
    UNION ALL SELECT 'Guayaquil', 'Latacunga', 330, 12.00
    UNION ALL SELECT 'Santo Domingo', 'Guayaquil', 300, 11.00
    UNION ALL SELECT 'Guayaquil', 'Santo Domingo', 300, 11.00
    UNION ALL SELECT 'Quevedo', 'Quito', 270, 10.00
    UNION ALL SELECT 'Quito', 'Quevedo', 270, 10.00
    UNION ALL SELECT 'La Maná', 'Guayaquil', 255, 9.50
    UNION ALL SELECT 'Guayaquil', 'La Maná', 255, 9.50
    UNION ALL SELECT 'La Maná', 'Quito', 210, 8.00
    UNION ALL SELECT 'Quito', 'La Maná', 210, 8.00
    UNION ALL SELECT 'Quevedo', 'Ambato', 210, 8.00
    UNION ALL SELECT 'Ambato', 'Quevedo', 210, 8.00
    UNION ALL SELECT 'Quevedo', 'Latacunga', 180, 7.00
    UNION ALL SELECT 'Latacunga', 'Quevedo', 180, 7.00
    UNION ALL SELECT 'Quevedo', 'Guayaquil', 180, 7.00
    UNION ALL SELECT 'Guayaquil', 'Quevedo', 180, 7.00
    UNION ALL SELECT 'Quito', 'Santo Domingo', 180, 5.50
    UNION ALL SELECT 'Santo Domingo', 'Quito', 180, 5.50
    UNION ALL SELECT 'Santo Domingo', 'Ambato', 180, 7.00
    UNION ALL SELECT 'Ambato', 'Santo Domingo', 180, 7.00
    UNION ALL SELECT 'La Maná', 'Ambato', 165, 6.50
    UNION ALL SELECT 'Ambato', 'La Maná', 165, 6.50
    UNION ALL SELECT 'La Maná', 'Santo Domingo', 150, 6.00
    UNION ALL SELECT 'Santo Domingo', 'La Maná', 150, 6.00
    UNION ALL SELECT 'Latacunga', 'Santo Domingo', 150, 6.00
    UNION ALL SELECT 'Santo Domingo', 'Latacunga', 150, 6.00
    UNION ALL SELECT 'Quito', 'Ambato', 150, 6.00
    UNION ALL SELECT 'Ambato', 'Quito', 150, 6.00
    UNION ALL SELECT 'La Maná', 'Latacunga', 120, 5.00
    UNION ALL SELECT 'Latacunga', 'La Maná', 120, 5.00
    UNION ALL SELECT 'Quevedo', 'Santo Domingo', 120, 5.50
    UNION ALL SELECT 'Santo Domingo', 'Quevedo', 120, 5.50
    UNION ALL SELECT 'Latacunga', 'Quito', 105, 4.50
    UNION ALL SELECT 'Quito', 'Latacunga', 105, 4.50
    UNION ALL SELECT 'La Maná', 'Quevedo', 75, 3.50
    UNION ALL SELECT 'Quevedo', 'La Maná', 75, 3.50
    UNION ALL SELECT 'Latacunga', 'Ambato', 60, 3.00
    UNION ALL SELECT 'Ambato', 'Latacunga', 60, 3.00
  ) AS x
  JOIN ciudades o ON o.nombre = x.origen
  JOIN ciudades d ON d.nombre = x.destino
 WHERE NOT EXISTS (
       SELECT 1 FROM rutas r WHERE r.origen_id = o.id AND r.destino_id = d.id
 );

INSERT INTO horarios (ruta_id, bus_id, hora_salida, dias_semana, activo)
SELECT r.id, b.id, x.hora, '1111111', 1
  FROM (
    SELECT 'Quito' AS origen, 'Guayaquil' AS destino, '401' AS disco, '05:00:00' AS hora
    UNION ALL SELECT 'Quito', 'Guayaquil', '401', '12:30:00'
    UNION ALL SELECT 'Guayaquil', 'Quito', '402', '05:00:00'
    UNION ALL SELECT 'Guayaquil', 'Quito', '402', '12:30:00'
    UNION ALL SELECT 'Ambato', 'Guayaquil', '403', '05:00:00'
    UNION ALL SELECT 'Ambato', 'Guayaquil', '403', '12:00:00'
    UNION ALL SELECT 'Guayaquil', 'Ambato', '404', '05:00:00'
    UNION ALL SELECT 'Guayaquil', 'Ambato', '404', '12:00:00'
    UNION ALL SELECT 'Latacunga', 'Guayaquil', '405', '05:00:00'
    UNION ALL SELECT 'Latacunga', 'Guayaquil', '405', '12:00:00'
    UNION ALL SELECT 'Guayaquil', 'Latacunga', '406', '05:00:00'
    UNION ALL SELECT 'Guayaquil', 'Latacunga', '406', '12:00:00'
    UNION ALL SELECT 'Santo Domingo', 'Guayaquil', '405', '18:00:00'
    UNION ALL SELECT 'Santo Domingo', 'Guayaquil', '407', '05:00:00'
    UNION ALL SELECT 'Guayaquil', 'Santo Domingo', '407', '10:30:00'
    UNION ALL SELECT 'Guayaquil', 'Santo Domingo', '407', '16:00:00'
    UNION ALL SELECT 'Quevedo', 'Quito', '406', '18:00:00'
    UNION ALL SELECT 'Quevedo', 'Quito', '403', '18:30:00'
    UNION ALL SELECT 'Quito', 'Quevedo', '404', '18:30:00'
    UNION ALL SELECT 'Quito', 'Quevedo', '408', '05:00:00'
    UNION ALL SELECT 'La Maná', 'Guayaquil', '408', '10:00:00'
    UNION ALL SELECT 'La Maná', 'Guayaquil', '408', '14:45:00'
    UNION ALL SELECT 'Guayaquil', 'La Maná', '409', '05:00:00'
    UNION ALL SELECT 'Guayaquil', 'La Maná', '409', '12:00:00'
    UNION ALL SELECT 'La Maná', 'Quito', '409', '16:45:00'
    UNION ALL SELECT 'La Maná', 'Quito', '408', '19:30:00'
    UNION ALL SELECT 'Quito', 'La Maná', '410', '05:00:00'
    UNION ALL SELECT 'Quito', 'La Maná', '410', '12:00:00'
    UNION ALL SELECT 'Quevedo', 'Ambato', '410', '16:00:00'
    UNION ALL SELECT 'Quevedo', 'Ambato', '411', '19:00:00'
    UNION ALL SELECT 'Ambato', 'Quevedo', '412', '05:00:00'
    UNION ALL SELECT 'Ambato', 'Quevedo', '412', '12:00:00'
    UNION ALL SELECT 'Quevedo', 'Latacunga', '412', '16:00:00'
    UNION ALL SELECT 'Quevedo', 'Latacunga', '412', '19:30:00'
    UNION ALL SELECT 'Latacunga', 'Quevedo', '401', '20:00:00'
    UNION ALL SELECT 'Latacunga', 'Quevedo', '413', '05:00:00'
    UNION ALL SELECT 'Quevedo', 'Guayaquil', '413', '08:30:00'
    UNION ALL SELECT 'Quevedo', 'Guayaquil', '413', '12:00:00'
    UNION ALL SELECT 'Guayaquil', 'Quevedo', '413', '15:30:00'
    UNION ALL SELECT 'Guayaquil', 'Quevedo', '413', '19:00:00'
    UNION ALL SELECT 'Quito', 'Santo Domingo', '402', '20:00:00'
    UNION ALL SELECT 'Quito', 'Santo Domingo', '414', '05:00:00'
    UNION ALL SELECT 'Santo Domingo', 'Quito', '414', '08:30:00'
    UNION ALL SELECT 'Santo Domingo', 'Quito', '414', '12:00:00'
    UNION ALL SELECT 'Santo Domingo', 'Ambato', '414', '15:30:00'
    UNION ALL SELECT 'Santo Domingo', 'Ambato', '414', '19:00:00'
    UNION ALL SELECT 'Ambato', 'Santo Domingo', '410', '20:00:00'
    UNION ALL SELECT 'Ambato', 'Santo Domingo', '415', '05:00:00'
    UNION ALL SELECT 'La Maná', 'Ambato', '415', '08:30:00'
    UNION ALL SELECT 'La Maná', 'Ambato', '415', '12:00:00'
    UNION ALL SELECT 'Ambato', 'La Maná', '415', '15:15:00'
    UNION ALL SELECT 'Ambato', 'La Maná', '415', '18:30:00'
    UNION ALL SELECT 'La Maná', 'Santo Domingo', '416', '05:00:00'
    UNION ALL SELECT 'La Maná', 'Santo Domingo', '416', '12:00:00'
    UNION ALL SELECT 'Santo Domingo', 'La Maná', '416', '15:00:00'
    UNION ALL SELECT 'Santo Domingo', 'La Maná', '416', '18:00:00'
    UNION ALL SELECT 'Latacunga', 'Santo Domingo', '417', '05:00:00'
    UNION ALL SELECT 'Latacunga', 'Santo Domingo', '417', '12:00:00'
    UNION ALL SELECT 'Santo Domingo', 'Latacunga', '417', '15:00:00'
    UNION ALL SELECT 'Santo Domingo', 'Latacunga', '417', '18:00:00'
    UNION ALL SELECT 'Quito', 'Ambato', '418', '05:00:00'
    UNION ALL SELECT 'Quito', 'Ambato', '418', '12:00:00'
    UNION ALL SELECT 'Ambato', 'Quito', '418', '15:00:00'
    UNION ALL SELECT 'Ambato', 'Quito', '418', '18:00:00'
    UNION ALL SELECT 'La Maná', 'Latacunga', '409', '20:45:00'
    UNION ALL SELECT 'La Maná', 'Latacunga', '416', '21:00:00'
    UNION ALL SELECT 'Latacunga', 'La Maná', '417', '21:00:00'
    UNION ALL SELECT 'Latacunga', 'La Maná', '419', '05:00:00'
    UNION ALL SELECT 'Quevedo', 'Santo Domingo', '419', '07:30:00'
    UNION ALL SELECT 'Quevedo', 'Santo Domingo', '419', '12:00:00'
    UNION ALL SELECT 'Santo Domingo', 'Quevedo', '419', '14:30:00'
    UNION ALL SELECT 'Santo Domingo', 'Quevedo', '419', '17:30:00'
    UNION ALL SELECT 'Latacunga', 'Quito', '419', '20:00:00'
    UNION ALL SELECT 'Latacunga', 'Quito', '418', '21:00:00'
    UNION ALL SELECT 'Quito', 'Latacunga', '420', '05:00:00'
    UNION ALL SELECT 'Quito', 'Latacunga', '420', '12:00:00'
    UNION ALL SELECT 'La Maná', 'Quevedo', '420', '14:15:00'
    UNION ALL SELECT 'La Maná', 'Quevedo', '420', '17:15:00'
    UNION ALL SELECT 'Quevedo', 'La Maná', '420', '19:00:00'
    UNION ALL SELECT 'Quevedo', 'La Maná', '420', '20:45:00'
    UNION ALL SELECT 'Latacunga', 'Ambato', '407', '21:30:00'
    UNION ALL SELECT 'Latacunga', 'Ambato', '415', '21:45:00'
    UNION ALL SELECT 'Ambato', 'Latacunga', '421', '05:00:00'
    UNION ALL SELECT 'Ambato', 'Latacunga', '421', '12:00:00'
  ) AS x
  JOIN ciudades o ON o.nombre = x.origen
  JOIN ciudades d ON d.nombre = x.destino
  JOIN rutas r ON r.origen_id = o.id AND r.destino_id = d.id
  JOIN buses b ON b.numero_disco = x.disco
 WHERE NOT EXISTS (
       SELECT 1 FROM horarios h WHERE h.ruta_id = r.id AND h.hora_salida = x.hora
 );

INSERT INTO viajes (ruta_id, bus_id, salida, llegada_est, precio, estado)
WITH RECURSIVE dias AS (
  SELECT CURDATE() AS fecha
  UNION ALL
  SELECT DATE_ADD(fecha, INTERVAL 1 DAY) FROM dias
  WHERE fecha < DATE_ADD(CURDATE(), INTERVAL 29 DAY)
)
SELECT h.ruta_id,
       h.bus_id,
       TIMESTAMP(d.fecha, h.hora_salida),
       TIMESTAMP(d.fecha, h.hora_salida) + INTERVAL r.duracion_min MINUTE,
       r.precio_base,
       'programado'
  FROM horarios h
  JOIN rutas r ON r.id = h.ruta_id
  JOIN buses b ON b.id = h.bus_id
  JOIN dias d
 WHERE h.activo = 1
   AND r.activa = 1
   AND b.estado = 'operativo'
   AND SUBSTRING(h.dias_semana, WEEKDAY(d.fecha) + 1, 1) = '1'
   AND TIMESTAMP(d.fecha, h.hora_salida) > NOW()
   AND NOT EXISTS (
        SELECT 1
          FROM viajes v
         WHERE v.ruta_id = h.ruta_id
           AND v.salida = TIMESTAMP(d.fecha, h.hora_salida)
           AND v.estado <> 'cancelado'
   )
   AND NOT EXISTS (
        SELECT 1
          FROM viajes v
         WHERE v.bus_id = h.bus_id
           AND v.estado IN ('programado', 'abordando', 'en_ruta')
           AND TIMESTAMP(d.fecha, h.hora_salida) < v.llegada_est
           AND TIMESTAMP(d.fecha, h.hora_salida) + INTERVAL r.duracion_min MINUTE > v.salida
   );
