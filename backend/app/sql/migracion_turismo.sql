-- Portal de turismo de La Maná. Idempotente: no toca boletos, viajes ni pagos.
-- La columna portada.ambito la agrega el arranque antes de este archivo.

CREATE TABLE IF NOT EXISTS turismo_categorias (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  tipo ENUM('atractivo', 'gastronomia', 'hospedaje', 'actividad', 'ruta', 'parroquia', 'guia', 'evento') NOT NULL,
  nombre VARCHAR(120) NOT NULL,
  slug VARCHAR(140) NOT NULL,
  resumen VARCHAR(400) NOT NULL DEFAULT '',
  orden INT NOT NULL DEFAULT 0,
  activo TINYINT(1) NOT NULL DEFAULT 1,
  UNIQUE KEY uk_turismo_cat (tipo, slug)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS turismo_fichas (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  tipo ENUM('atractivo', 'gastronomia', 'hospedaje', 'actividad', 'ruta', 'parroquia', 'guia') NOT NULL,
  categoria_id INT UNSIGNED NULL,
  nombre VARCHAR(160) NOT NULL,
  slug VARCHAR(160) NOT NULL,
  resumen VARCHAR(400) NOT NULL,
  cuerpo TEXT NOT NULL,
  zona VARCHAR(120) NOT NULL DEFAULT '',
  direccion VARCHAR(200) NOT NULL DEFAULT '',
  lat DECIMAL(9, 6) NULL,
  lng DECIMAL(9, 6) NULL,
  imagen VARCHAR(255) NULL,
  credito VARCHAR(255) NOT NULL DEFAULT '',
  destacado TINYINT(1) NOT NULL DEFAULT 0,
  orden INT NOT NULL DEFAULT 0,
  activo TINYINT(1) NOT NULL DEFAULT 1,
  UNIQUE KEY uk_turismo_ficha (tipo, slug),
  CONSTRAINT fk_turismo_ficha_cat FOREIGN KEY (categoria_id) REFERENCES turismo_categorias (id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS turismo_eventos (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  categoria_id INT UNSIGNED NULL,
  titulo VARCHAR(160) NOT NULL,
  slug VARCHAR(160) NOT NULL,
  resumen VARCHAR(400) NOT NULL,
  cuerpo TEXT NOT NULL,
  inicio DATE NOT NULL,
  fin DATE NULL,
  lugar VARCHAR(160) NOT NULL DEFAULT '',
  imagen VARCHAR(255) NULL,
  credito VARCHAR(255) NOT NULL DEFAULT '',
  activo TINYINT(1) NOT NULL DEFAULT 1,
  UNIQUE KEY uk_turismo_evento (slug),
  CONSTRAINT fk_turismo_evento_cat FOREIGN KEY (categoria_id) REFERENCES turismo_categorias (id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS turismo_galeria (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  titulo VARCHAR(160) NOT NULL,
  descripcion VARCHAR(300) NOT NULL DEFAULT '',
  archivo VARCHAR(255) NOT NULL,
  credito VARCHAR(255) NOT NULL DEFAULT '',
  orden INT NOT NULL DEFAULT 0,
  activo TINYINT(1) NOT NULL DEFAULT 1
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS turismo_mensajes (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(120) NOT NULL,
  email VARCHAR(180) NOT NULL,
  mensaje VARCHAR(1000) NOT NULL,
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

INSERT INTO turismo_categorias (tipo, nombre, slug, resumen, orden)
SELECT 'atractivo', 'Naturaleza', 'naturaleza', 'Río, cascadas y bosque de pie de monte.', 1
WHERE NOT EXISTS (SELECT 1 FROM turismo_categorias WHERE tipo = 'atractivo' AND slug = 'naturaleza');
INSERT INTO turismo_categorias (tipo, nombre, slug, resumen, orden)
SELECT 'atractivo', 'Pueblo', 'pueblo', 'Parque, calles y vida de la cabecera.', 2
WHERE NOT EXISTS (SELECT 1 FROM turismo_categorias WHERE tipo = 'atractivo' AND slug = 'pueblo');
INSERT INTO turismo_categorias (tipo, nombre, slug, resumen, orden)
SELECT 'atractivo', 'Agroturismo', 'agroturismo', 'Cacao, banano y fincas del subtrópico.', 3
WHERE NOT EXISTS (SELECT 1 FROM turismo_categorias WHERE tipo = 'atractivo' AND slug = 'agroturismo');
INSERT INTO turismo_categorias (tipo, nombre, slug, resumen, orden)
SELECT 'gastronomia', 'Mesa local', 'mesa-local', 'Verde, cacao, gallina y pescado de río.', 1
WHERE NOT EXISTS (SELECT 1 FROM turismo_categorias WHERE tipo = 'gastronomia' AND slug = 'mesa-local');
INSERT INTO turismo_categorias (tipo, nombre, slug, resumen, orden)
SELECT 'hospedaje', 'Cabecera', 'cabecera', 'Dónde dormir en el centro cantonal.', 1
WHERE NOT EXISTS (SELECT 1 FROM turismo_categorias WHERE tipo = 'hospedaje' AND slug = 'cabecera');
INSERT INTO turismo_categorias (tipo, nombre, slug, resumen, orden)
SELECT 'hospedaje', 'Fincas', 'fincas', 'Alojamiento ligado al campo.', 2
WHERE NOT EXISTS (SELECT 1 FROM turismo_categorias WHERE tipo = 'hospedaje' AND slug = 'fincas');
INSERT INTO turismo_categorias (tipo, nombre, slug, resumen, orden)
SELECT 'actividad', 'Caminata', 'caminata', 'Senderos hacia el agua.', 1
WHERE NOT EXISTS (SELECT 1 FROM turismo_categorias WHERE tipo = 'actividad' AND slug = 'caminata');
INSERT INTO turismo_categorias (tipo, nombre, slug, resumen, orden)
SELECT 'actividad', 'Río', 'rio', 'Balnearios y orillas del San Pablo.', 2
WHERE NOT EXISTS (SELECT 1 FROM turismo_categorias WHERE tipo = 'actividad' AND slug = 'rio');
INSERT INTO turismo_categorias (tipo, nombre, slug, resumen, orden)
SELECT 'actividad', 'Aves', 'aves', 'Observación en el bosque subtropical.', 3
WHERE NOT EXISTS (SELECT 1 FROM turismo_categorias WHERE tipo = 'actividad' AND slug = 'aves');
INSERT INTO turismo_categorias (tipo, nombre, slug, resumen, orden)
SELECT 'ruta', 'Una jornada', 'una-jornada', 'Recorridos de un día sin horarios inventados.', 1
WHERE NOT EXISTS (SELECT 1 FROM turismo_categorias WHERE tipo = 'ruta' AND slug = 'una-jornada');
INSERT INTO turismo_categorias (tipo, nombre, slug, resumen, orden)
SELECT 'parroquia', 'Urbana', 'urbana', 'La cabecera cantonal.', 1
WHERE NOT EXISTS (SELECT 1 FROM turismo_categorias WHERE tipo = 'parroquia' AND slug = 'urbana');
INSERT INTO turismo_categorias (tipo, nombre, slug, resumen, orden)
SELECT 'parroquia', 'Rural', 'rural', 'Guasaganda, Pucayacu y El Carmen.', 2
WHERE NOT EXISTS (SELECT 1 FROM turismo_categorias WHERE tipo = 'parroquia' AND slug = 'rural');
INSERT INTO turismo_categorias (tipo, nombre, slug, resumen, orden)
SELECT 'guia', 'Llegada', 'llegada', 'Cómo entrar al cantón.', 1
WHERE NOT EXISTS (SELECT 1 FROM turismo_categorias WHERE tipo = 'guia' AND slug = 'llegada');
INSERT INTO turismo_categorias (tipo, nombre, slug, resumen, orden)
SELECT 'guia', 'Práctico', 'practico', 'Clima, dinero y papeles, sin cifras dudosas.', 2
WHERE NOT EXISTS (SELECT 1 FROM turismo_categorias WHERE tipo = 'guia' AND slug = 'practico');
INSERT INTO turismo_categorias (tipo, nombre, slug, resumen, orden)
SELECT 'evento', 'Fiesta', 'fiesta', 'Cantonización y celebraciones del pueblo.', 1
WHERE NOT EXISTS (SELECT 1 FROM turismo_categorias WHERE tipo = 'evento' AND slug = 'fiesta');

INSERT INTO turismo_fichas (tipo, categoria_id, nombre, slug, resumen, cuerpo, zona, imagen, credito, destacado, orden, lat, lng)
SELECT 'parroquia', c.id, 'La Maná', 'la-mana',
       'Cabecera cantonal, puerta entre la sierra de Cotopaxi y la llanura costera.',
       'La Maná es la cabecera del cantón del mismo nombre, en el subtrópico de Cotopaxi. El parque central concentra la vida de día: sombra, comercio corto y el punto desde el que se sale hacia el río o hacia las parroquias rurales.\n\nDesde aquí se entiende el cantón: cacao y banano en las fincas, calor húmedo y una carretera que sube a Latacunga o baja hacia Quevedo. Los pasajes de la cooperativa están en el apartado Transporte.',
       'Cabecera', '/turismo/panoramica.jpg',
       'Panorámica de La Maná. Danny LM, CC BY-SA 3.0, Wikimedia Commons.',
       1, 1, -0.940600, -79.234400
FROM turismo_categorias c
WHERE c.tipo = 'parroquia' AND c.slug = 'urbana'
  AND NOT EXISTS (SELECT 1 FROM turismo_fichas WHERE tipo = 'parroquia' AND slug = 'la-mana');

INSERT INTO turismo_fichas (tipo, categoria_id, nombre, slug, resumen, cuerpo, zona, imagen, credito, destacado, orden)
SELECT 'parroquia', c.id, 'Guasaganda', 'guasaganda',
       'Parroquia rural de bosque húmedo, conocida por su vegetación cerrada.',
       'Guasaganda es una parroquia rural de La Maná. El paisaje es de bosque subtropical, más verde y más quieto que la cabecera. Se visita para caminar, mirar aves y entender la diversidad del pie de monte, sin esperar un malecón urbano.\n\nConviene ir con calzado que soporte barro y con tiempo de sobra: el clima cambia en la misma tarde. No hay en esta ficha un horario de guías ni una tarifa, porque cambian según quien reciba en el lugar.',
       'Parroquia rural', '/turismo/fauna.jpg',
       'Lagartija fotografiada en La Maná. Diego Tirira, CC BY-SA 2.0, Wikimedia Commons.',
       1, 2
FROM turismo_categorias c
WHERE c.tipo = 'parroquia' AND c.slug = 'rural'
  AND NOT EXISTS (SELECT 1 FROM turismo_fichas WHERE tipo = 'parroquia' AND slug = 'guasaganda');

INSERT INTO turismo_fichas (tipo, categoria_id, nombre, slug, resumen, cuerpo, zona, imagen, credito, orden)
SELECT 'parroquia', c.id, 'Pucayacu', 'pucayacu',
       'Parroquia rural de fincas, en el mismo piso cálido del cantón.',
       'Pucayacu es parroquia rural de La Maná. La vida gira en torno a las fincas: cacao, banano y potreros pequeños. No es un pueblo de vitrina; se recorre despacio y preguntando en el camino.\n\nUna visita corta alcanza para ver el verde del subtrópico y volver a la cabecera el mismo día. Las distancias exactas dependen del punto de partida y no se fijan aquí.',
       'Parroquia rural', '/turismo/banano.jpg',
       'Plantación de banano en Ecuador. Dave Lonsdale, CC BY 2.0, Wikimedia Commons.',
       3
FROM turismo_categorias c
WHERE c.tipo = 'parroquia' AND c.slug = 'rural'
  AND NOT EXISTS (SELECT 1 FROM turismo_fichas WHERE tipo = 'parroquia' AND slug = 'pucayacu');

INSERT INTO turismo_fichas (tipo, categoria_id, nombre, slug, resumen, cuerpo, zona, orden)
SELECT 'parroquia', c.id, 'El Carmen', 'el-carmen',
       'Parroquia rural del cantón, entre fincas y caminos de segundo orden.',
       'El Carmen es la otra parroquia rural de La Maná. Comparte el clima cálido y húmedo de la zona y una economía de finca. Sirve como salida de un día si ya se está en la cabecera y se quiere ver campo, no solo el parque.\n\nAntes de salir conviene confirmar el estado del camino con alguien del lugar. Esta guía no publica un estado de vía ni un tiempo de viaje cerrado.',
       'Parroquia rural', 4
FROM turismo_categorias c
WHERE c.tipo = 'parroquia' AND c.slug = 'rural'
  AND NOT EXISTS (SELECT 1 FROM turismo_fichas WHERE tipo = 'parroquia' AND slug = 'el-carmen');

INSERT INTO turismo_fichas (tipo, categoria_id, nombre, slug, resumen, cuerpo, zona, destacado, orden)
SELECT 'atractivo', c.id, 'Río San Pablo', 'rio-san-pablo',
       'El río que ordena el cantón y deja orillas para el baño de tarde.',
       'El San Pablo cruza la vida de La Maná. En sus orillas hay balnearios sencillos, sombras y gente que baja a pasar el calor. No es un parque cerrado: el caudal y la limpieza cambian con la lluvia, así que la decisión de meterse al agua es de cada visita.\n\nDesde la cabecera se llega a varios puntos de orilla. Pregunte en el parque cuál está tranquilo ese día. Esta ficha no trae foto del río a propósito: la imagen se sube desde taquilla cuando haya una toma libre o propia.',
       'Cabecera y parroquias', 1, 1
FROM turismo_categorias c
WHERE c.tipo = 'atractivo' AND c.slug = 'naturaleza'
  AND NOT EXISTS (SELECT 1 FROM turismo_fichas WHERE tipo = 'atractivo' AND slug = 'rio-san-pablo');

INSERT INTO turismo_fichas (tipo, categoria_id, nombre, slug, resumen, cuerpo, zona, destacado, orden)
SELECT 'atractivo', c.id, 'Cascadas de Zapanal, Tilipulo y Manguilita', 'cascadas-de-la-mana',
       'Caídas de agua del entorno subtropical, para una caminata de día.',
       'En el entorno de La Maná se visitan cascadas como las de Zapanal, Tilipulo y Manguilita. Son salidas de campo, no miradores urbanos: hay tramo a pie, humedad y piso que resbala después de llover.\n\nNo se publican aquí altura ni tiempo de caminata. Quien recibe en cada acceso indica por dónde subir y si el sendero está abierto. Lleve agua y zapatos cerrados. La foto se deja vacía hasta tener una imagen de estas cascadas, no de otro cantón.',
       'Entorno del cantón', 1, 2
FROM turismo_categorias c
WHERE c.tipo = 'atractivo' AND c.slug = 'naturaleza'
  AND NOT EXISTS (SELECT 1 FROM turismo_fichas WHERE tipo = 'atractivo' AND slug = 'cascadas-de-la-mana');

INSERT INTO turismo_fichas (tipo, categoria_id, nombre, slug, resumen, cuerpo, zona, imagen, credito, destacado, orden)
SELECT 'atractivo', c.id, 'Cacao de pie de monte', 'cacao-de-pie-de-monte',
       'El fruto que marca las fincas del subtrópico de Cotopaxi.',
       'El cacao se ve en las fincas de La Maná y de sus parroquias: mazorcas en el árbol, secado al sol y, en algunas casas, una taza espesa. Visitar una finca es preguntar primero. No toda propiedad recibe extraños y no hay una tarifa única.\n\nLa foto de esta ficha es un fruto de cacao, no una hacienda con nombre. Si una finca quiere aparecer con su propio nombre y su imagen, se carga desde taquilla.',
       'Fincas del cantón', '/turismo/cacao.jpg',
       'Fruto del cacao. Bernard Gagnon, CC BY-SA 3.0, Wikimedia Commons.',
       1, 3
FROM turismo_categorias c
WHERE c.tipo = 'atractivo' AND c.slug = 'agroturismo'
  AND NOT EXISTS (SELECT 1 FROM turismo_fichas WHERE tipo = 'atractivo' AND slug = 'cacao-de-pie-de-monte');

INSERT INTO turismo_fichas (tipo, categoria_id, nombre, slug, resumen, cuerpo, zona, imagen, credito, orden)
SELECT 'atractivo', c.id, 'Banano del cantón', 'banano-del-canton',
       'Hileras de banano en el piso cálido, parte del paisaje cotidiano.',
       'El banano acompaña al cacao en el paisaje de La Maná. Las plantaciones se ven desde la vía y desde los caminos de finca. No es un parque temático: es cultivo, con gente trabajando.\n\nLa imagen es una plantación ecuatoriana de uso libre, útil como referencia visual hasta que taquilla suba una toma del cantón.',
       'Fincas del cantón', '/turismo/banano.jpg',
       'Plantación de banano en Ecuador. Dave Lonsdale, CC BY 2.0, Wikimedia Commons.',
       4
FROM turismo_categorias c
WHERE c.tipo = 'atractivo' AND c.slug = 'agroturismo'
  AND NOT EXISTS (SELECT 1 FROM turismo_fichas WHERE tipo = 'atractivo' AND slug = 'banano-del-canton');

INSERT INTO turismo_fichas (tipo, categoria_id, nombre, slug, resumen, cuerpo, zona, imagen, credito, destacado, orden, lat, lng, direccion)
SELECT 'atractivo', c.id, 'Parque central', 'parque-central',
       'Sombra, encuentro y el punto fácil para empezar la visita.',
       'El parque central de La Maná es el lugar claro para orientarse. Alrededor están el comercio corto, la gente que espera un carro y el punto desde el que se pregunta cómo llegar al río.\n\nSirve de inicio y de cierre de una jornada. Los fines de semana se llena más, sobre todo cuando hay fiesta de cantonización.',
       'Cabecera', '/turismo/parque.jpg',
       'Parque central de La Maná. Danny LM, CC BY-SA 3.0, Wikimedia Commons.',
       1, 5, -0.940600, -79.234400, 'Centro de la cabecera cantonal'
FROM turismo_categorias c
WHERE c.tipo = 'atractivo' AND c.slug = 'pueblo'
  AND NOT EXISTS (SELECT 1 FROM turismo_fichas WHERE tipo = 'atractivo' AND slug = 'parque-central');

INSERT INTO turismo_fichas (tipo, categoria_id, nombre, slug, resumen, cuerpo, zona, imagen, credito, destacado, orden)
SELECT 'gastronomia', c.id, 'Mesa del subtrópico', 'mesa-del-subtropico',
       'Verde, cacao, gallina criolla y maduro, sin un plato único decretado.',
       'En La Maná se come de subtrópico y de costa cercana: verde en bolón o patacón, maduro, gallina criolla y, cuando hay, un dulce o una bebida de cacao. No existe en esta guía un ranking ni un local oficial.\n\nPregunte en el parque qué olla está prendida ese día. Los nombres de restaurantes se agregan desde taquilla cuando el local quiera figurar.',
       'Cabecera', '/turismo/cacao.jpg',
       'Fruto del cacao. Bernard Gagnon, CC BY-SA 3.0, Wikimedia Commons.',
       1, 1
FROM turismo_categorias c
WHERE c.tipo = 'gastronomia' AND c.slug = 'mesa-local'
  AND NOT EXISTS (SELECT 1 FROM turismo_fichas WHERE tipo = 'gastronomia' AND slug = 'mesa-del-subtropico');

INSERT INTO turismo_fichas (tipo, categoria_id, nombre, slug, resumen, cuerpo, zona, orden)
SELECT 'gastronomia', c.id, 'Pescado de río', 'pescado-de-rio',
       'Tilapia y otros pescados de agua dulce, según la temporada y el local.',
       'Cerca del San Pablo es habitual encontrar pescado de río, a menudo tilapia, preparado sencillo: frito o en sopa, con arroz y ensalada. La oferta depende del día y de quien abra la cocina.\n\nNo se lista aquí un comedor concreto. Si un local quiere su ficha, se crea en taquilla con su nombre y su foto.',
       'Orillas del San Pablo', 2
FROM turismo_categorias c
WHERE c.tipo = 'gastronomia' AND c.slug = 'mesa-local'
  AND NOT EXISTS (SELECT 1 FROM turismo_fichas WHERE tipo = 'gastronomia' AND slug = 'pescado-de-rio');

INSERT INTO turismo_fichas (tipo, categoria_id, nombre, slug, resumen, cuerpo, zona, orden)
SELECT 'hospedaje', c.id, 'Alojamiento en la cabecera', 'alojamiento-en-la-cabecera',
       'Habitaciones de paso en el centro, útiles si se llega en bus.',
       'En la cabecera hay alojamiento sencillo para quien llega en la tarde y sale al día siguiente hacia el río o hacia una parroquia. Esta ficha describe el tipo de oferta, no un hotel con nombre inventado.\n\nLos nombres, teléfonos y precios se cargan en taquilla cuando el hospedaje confirme sus datos. Hasta entonces, pregunte al bajar del bus o en el parque.',
       'Cabecera', 1
FROM turismo_categorias c
WHERE c.tipo = 'hospedaje' AND c.slug = 'cabecera'
  AND NOT EXISTS (SELECT 1 FROM turismo_fichas WHERE tipo = 'hospedaje' AND slug = 'alojamiento-en-la-cabecera');

INSERT INTO turismo_fichas (tipo, categoria_id, nombre, slug, resumen, cuerpo, zona, imagen, credito, orden)
SELECT 'hospedaje', c.id, 'Fincas que reciben', 'fincas-que-reciben',
       'Algunas fincas de cacao o banano aceptan visitantes con aviso previo.',
       'Hay fincas del cantón que reciben gente para ver el cultivo y, a veces, para dormir. No es una red con reserva en línea dentro de este portal. Se acuerda directo con la finca.\n\nSi una finca quiere publicar cupo, foto y contacto, taquilla crea su ficha. La imagen de apoyo es una plantación, no la fachada de un hostal.',
       'Parroquias rurales', '/turismo/banano.jpg',
       'Plantación de banano en Ecuador. Dave Lonsdale, CC BY 2.0, Wikimedia Commons.',
       2
FROM turismo_categorias c
WHERE c.tipo = 'hospedaje' AND c.slug = 'fincas'
  AND NOT EXISTS (SELECT 1 FROM turismo_fichas WHERE tipo = 'hospedaje' AND slug = 'fincas-que-reciben');

INSERT INTO turismo_fichas (tipo, categoria_id, nombre, slug, resumen, cuerpo, zona, destacado, orden)
SELECT 'actividad', c.id, 'Caminata a las cascadas', 'caminata-a-las-cascadas',
       'Salida de día hacia Zapanal, Tilipulo, Manguilita u otra caída cercana.',
       'La caminata típica sale de un punto de acceso rural y sube hasta una cascada. El piso es húmedo. No hay en esta guía un mapa de curvas ni un tiempo estándar: quien conoce el sendero ese mes es quien debe indicarlo.\n\nCombine esta actividad con la ficha de cascadas y vuelva con luz. De noche el camino no está pensado para visita.',
       'Entorno del cantón', 1, 1
FROM turismo_categorias c
WHERE c.tipo = 'actividad' AND c.slug = 'caminata'
  AND NOT EXISTS (SELECT 1 FROM turismo_fichas WHERE tipo = 'actividad' AND slug = 'caminata-a-las-cascadas');

INSERT INTO turismo_fichas (tipo, categoria_id, nombre, slug, resumen, cuerpo, zona, orden)
SELECT 'actividad', c.id, 'Tarde de río', 'tarde-de-rio',
       'Orilla del San Pablo para bajar el calor, con juicio sobre el caudal.',
       'Pasar la tarde en una orilla del San Pablo es el plan más simple de La Maná. Lleve lo que vaya a consumir, recoja lo que lleve y no entre al agua si la creciente viene sucia o fuerte.\n\nLos balnearios cambian de nombre y de cuidado. Esta ficha no fija una entrada ni un precio.',
       'Río San Pablo', 2
FROM turismo_categorias c
WHERE c.tipo = 'actividad' AND c.slug = 'rio'
  AND NOT EXISTS (SELECT 1 FROM turismo_fichas WHERE tipo = 'actividad' AND slug = 'tarde-de-rio');

INSERT INTO turismo_fichas (tipo, categoria_id, nombre, slug, resumen, cuerpo, zona, imagen, credito, orden)
SELECT 'actividad', c.id, 'Aves y bosque en Guasaganda', 'aves-en-guasaganda',
       'Mirar fauna en la parroquia más boscosa del cantón.',
       'Guasaganda invita a ir despacio: el bosque húmedo concentra más vida que el centro cantonal. Lleve prismáticos si los tiene y no salga del camino marcado por quien recibe.\n\nLa foto de apoyo es una lagartija tomada en La Maná. No pretende ser el inventario de aves de la parroquia.',
       'Guasaganda', '/turismo/fauna.jpg',
       'Lagartija fotografiada en La Maná. Diego Tirira, CC BY-SA 2.0, Wikimedia Commons.',
       3
FROM turismo_categorias c
WHERE c.tipo = 'actividad' AND c.slug = 'aves'
  AND NOT EXISTS (SELECT 1 FROM turismo_fichas WHERE tipo = 'actividad' AND slug = 'aves-en-guasaganda');

INSERT INTO turismo_fichas (tipo, categoria_id, nombre, slug, resumen, cuerpo, zona, destacado, orden)
SELECT 'ruta', c.id, 'Jornada en el cantón', 'jornada-en-el-canton',
       'Parque, una orilla del río y, si alcanza, una finca o una cascada.',
       'Un día razonable empieza en el parque central, sigue hacia una orilla del San Pablo y deja la tarde para una sola salida larga: finca de cacao o caminata a una cascada, no las dos si se llega tarde.\n\nRegrese a la cabecera con luz. Si sigue de viaje, los buses de la cooperativa salen hacia Quevedo, Latacunga y, por conexión, a la costa o a la sierra. Ese horario vive en Transporte, no en esta ficha.',
       'Cabecera y alrededores', 1, 1
FROM turismo_categorias c
WHERE c.tipo = 'ruta' AND c.slug = 'una-jornada'
  AND NOT EXISTS (SELECT 1 FROM turismo_fichas WHERE tipo = 'ruta' AND slug = 'jornada-en-el-canton');

INSERT INTO turismo_fichas (tipo, categoria_id, nombre, slug, resumen, cuerpo, zona, orden)
SELECT 'ruta', c.id, 'Bajar desde la sierra o subir desde Quevedo', 'bajar-desde-la-sierra',
       'La Maná queda en la bajada de Cotopaxi hacia la llanura.',
       'Desde la sierra se baja de Latacunga hacia el calor. Desde la costa cercana se llega por Quevedo y la vía que sube al cantón. Los dos movimientos los hace a diario la cooperativa de transporte, con asiento elegido antes de pagar.\n\nNo se anota aquí un kilometraje ni una duración cerrada: el tráfico y la parada cambian el reloj. El buscador de Transporte muestra las salidas del día.',
       'Vías de acceso', 2
FROM turismo_categorias c
WHERE c.tipo = 'ruta' AND c.slug = 'una-jornada'
  AND NOT EXISTS (SELECT 1 FROM turismo_fichas WHERE tipo = 'ruta' AND slug = 'bajar-desde-la-sierra');

INSERT INTO turismo_fichas (tipo, categoria_id, nombre, slug, resumen, cuerpo, zona, orden)
SELECT 'guia', c.id, 'Cómo llegar', 'como-llegar',
       'Por tierra, desde la sierra de Cotopaxi o desde Quevedo.',
       'La Maná no se presenta en esta guía como destino de aeropuerto propio. Se llega por carretera: bajando desde Latacunga o viniendo de Quevedo y la red costera. La cooperativa publica esas salidas en Transporte.\n\nDentro del cantón, de la cabecera a las parroquias se sigue en bus local, camioneta o carro de finca. El modo exacto se confirma el día de la visita.',
       'Accesos', 1
FROM turismo_categorias c
WHERE c.tipo = 'guia' AND c.slug = 'llegada'
  AND NOT EXISTS (SELECT 1 FROM turismo_fichas WHERE tipo = 'guia' AND slug = 'como-llegar');

INSERT INTO turismo_fichas (tipo, categoria_id, nombre, slug, resumen, cuerpo, zona, orden)
SELECT 'guia', c.id, 'Clima del cantón', 'clima-del-canton',
       'Calor húmedo de subtrópico, con tardes que pueden llover.',
       'La Maná está en el piso cálido y húmedo, distinto del páramo de la sierra de Cotopaxi. De día abriga poco. La lluvia puede aparecer en la tarde y volver resbaloso un sendero de cascada.\n\nNo se publica una tabla de temperaturas ni un mes perfecto. Lleve ropa ligera, una capa para el agua y zapatos que se puedan ensuciar.',
       'Todo el cantón', 2
FROM turismo_categorias c
WHERE c.tipo = 'guia' AND c.slug = 'practico'
  AND NOT EXISTS (SELECT 1 FROM turismo_fichas WHERE tipo = 'guia' AND slug = 'clima-del-canton');

INSERT INTO turismo_fichas (tipo, categoria_id, nombre, slug, resumen, cuerpo, zona, orden)
SELECT 'guia', c.id, 'Antes de salir', 'antes-de-salir',
       'Dinero, papeles y energía, en los términos generales del Ecuador.',
       'Se paga en dólares de los Estados Unidos, la moneda en uso en el Ecuador. Un documento de identidad basta para los trámites cotidianos de un viaje nacional. La red eléctrica es la del país; un cargador corriente suele servir.\n\nEsta nota no reemplaza un requisito migratorio ni una norma de un área protegida. Si la salida entra a un predio privado, pida permiso. El correo del portal recibe preguntas, no reservas de finca.',
       'Datos prácticos', 3
FROM turismo_categorias c
WHERE c.tipo = 'guia' AND c.slug = 'practico'
  AND NOT EXISTS (SELECT 1 FROM turismo_fichas WHERE tipo = 'guia' AND slug = 'antes-de-salir');

INSERT INTO turismo_eventos (categoria_id, titulo, slug, resumen, cuerpo, inicio, fin, lugar, imagen, credito)
SELECT c.id, 'Fiestas de cantonización', 'fiestas-de-cantonizacion',
       'La ciudad recuerda el 19 de mayo, fecha en que La Maná pasó a ser cantón.',
       'La cantonización de La Maná se conmemora en torno al 19 de mayo. En la cabecera suele haber desfile, tarima y más movimiento en el parque. El programa de cada año lo fija el municipio; esta ficha no inventa horas ni artistas.\n\nLa fecha guardada es el 19 de mayo de 2026 como referencia del calendario. Cuando salga el programa oficial, taquilla puede editar el texto, las fechas y la foto.',
       '2026-05-19', '2026-05-19', 'Parque central y calles de la cabecera',
       '/turismo/parque.jpg',
       'Parque central de La Maná. Danny LM, CC BY-SA 3.0, Wikimedia Commons.'
FROM turismo_categorias c
WHERE c.tipo = 'evento' AND c.slug = 'fiesta'
  AND NOT EXISTS (SELECT 1 FROM turismo_eventos WHERE slug = 'fiestas-de-cantonizacion');

INSERT INTO turismo_galeria (titulo, descripcion, archivo, credito, orden)
SELECT 'Cabecera de La Maná', 'Vista amplia de la ciudad.', '/turismo/panoramica.jpg',
       'Danny LM, CC BY-SA 3.0, Wikimedia Commons.', 1
WHERE NOT EXISTS (SELECT 1 FROM turismo_galeria WHERE archivo = '/turismo/panoramica.jpg');
INSERT INTO turismo_galeria (titulo, descripcion, archivo, credito, orden)
SELECT 'Parque central', 'Punto de encuentro de la cabecera.', '/turismo/parque.jpg',
       'Danny LM, CC BY-SA 3.0, Wikimedia Commons.', 2
WHERE NOT EXISTS (SELECT 1 FROM turismo_galeria WHERE archivo = '/turismo/parque.jpg');
INSERT INTO turismo_galeria (titulo, descripcion, archivo, credito, orden)
SELECT 'Cacao', 'El fruto de las fincas del subtrópico.', '/turismo/cacao.jpg',
       'Bernard Gagnon, CC BY-SA 3.0, Wikimedia Commons.', 3
WHERE NOT EXISTS (SELECT 1 FROM turismo_galeria WHERE archivo = '/turismo/cacao.jpg');
INSERT INTO turismo_galeria (titulo, descripcion, archivo, credito, orden)
SELECT 'Banano', 'Plantación ecuatoriana, como referencia del cultivo.', '/turismo/banano.jpg',
       'Dave Lonsdale, CC BY 2.0, Wikimedia Commons.', 4
WHERE NOT EXISTS (SELECT 1 FROM turismo_galeria WHERE archivo = '/turismo/banano.jpg');
INSERT INTO turismo_galeria (titulo, descripcion, archivo, credito, orden)
SELECT 'Fauna del cantón', 'Lagartija fotografiada en La Maná.', '/turismo/fauna.jpg',
       'Diego Tirira, CC BY-SA 2.0, Wikimedia Commons.', 5
WHERE NOT EXISTS (SELECT 1 FROM turismo_galeria WHERE archivo = '/turismo/fauna.jpg');

INSERT INTO portada (tipo, origen, enlace, titulo, subtitulo, texto_boton, enlace_boton, orden, activo, ambito)
SELECT 'imagen', 'enlace', '/turismo/panoramica.jpg',
       'La Maná abre el subtrópico de Cotopaxi.',
       'Río, cascadas, cacao y banano. El bus de la cooperativa sigue en Transporte.',
       'Ver atractivos', '/atractivos', 0, 1, 'portal'
WHERE NOT EXISTS (SELECT 1 FROM portada WHERE titulo = 'La Maná abre el subtrópico de Cotopaxi.');
INSERT INTO portada (tipo, origen, enlace, titulo, subtitulo, texto_boton, enlace_boton, orden, activo, ambito)
SELECT 'imagen', 'enlace', '/turismo/banano.jpg',
       'Fincas de calor húmedo.',
       'Cacao y banano en el pie de monte, entre la sierra y la llanura.',
       'Ver parroquias', '/parroquias', 1, 1, 'portal'
WHERE NOT EXISTS (SELECT 1 FROM portada WHERE titulo = 'Fincas de calor húmedo.');
INSERT INTO portada (tipo, origen, enlace, titulo, subtitulo, texto_boton, enlace_boton, orden, activo, ambito)
SELECT 'imagen', 'enlace', '/turismo/parque.jpg',
       'Empiece por el parque.',
       'De ahí se pregunta por el río, por una finca o por el bus de regreso.',
       'Cómo llegar', '/aprende', 2, 1, 'portal'
WHERE NOT EXISTS (SELECT 1 FROM portada WHERE titulo = 'Empiece por el parque.');
