# Referencia de estructura: tungurahuaturismo.com

Documento de estructura, no de contenido. Se revisó el HTML público el 27 de octubre de 2026 (inicio, menú, listados de Aprende, Vive, Descubre y Destinos turísticos, y la ficha de Ambato). No se copian logo, fotografías, textos, archivos de iconos ni hojas de estilo propietarias de ese sitio. Los iconos de su barra (`div.icon` con sprite propio) se describen por el concepto y se sustituyen con [Lucide](https://lucide.dev) (licencia ISC).

El sitio de referencia es la guía de una provincia. La Maná es un cantón, así que las piezas equivalentes son parroquias, atractivos y el apartado Transporte, no nueve cantones.

## Barra superior

Cabecera fija, fondo claro, marca a la izquierda.

1. Botón de menú (concepto: lista). En escritorio convive con la barra de iconos.
2. Logotipo del destino, enlace al inicio.
3. Buscador (concepto: lupa). Abre un campo con el texto «Search in Tungurahua Turismo» y chips de ámbito: Todo, Aprende, Emprendedores, Directorio, Vive, Descubre, Destinos turísticos, Ofertas.
4. Idioma (concepto: globo), con lista de idiomas y de otros portales del mismo editor.
5. Acceso (concepto: usuario). Es un modal de inicio de sesión, no una página.

## Menú de iconos

Segunda fila. Cada ítem es un enlace con icono, nombre y una pastilla numérica (cantidad de fichas).

| Clase | Etiqueta | Destino observado | Concepto del icono | Equivalente en La Maná |
| --- | --- | --- | --- | --- |
| `home` | Tungurahua | `/` | Lugar / casa del destino | La Maná, inicio del portal |
| `learn` | Aprende (142) | `/es-ec/tungurahua/aprende/all-articles-e9d64c833` | Estudio, memoria | Aprende |
| `manager` | Emprendedores (194) | `/es-ec/tungurahua/gestores/all-articles-egst4c833` | Oficio, gestión | No se replica como directorio comercial ajeno. El oficio local entra en gastronomía, hospedaje y fincas. |
| `directory` | Directorio (74) | `/es-ec/tungurahua/directorio/all-articles-edrt4c833` | Listado | Hospedaje y fichas editables |
| `live` | Vive (176) | `/es-ec/tungurahua/vive/all-articles-e2204c833` | Experiencia, día al aire | Vive / actividades |
| `discover` | Descubre (150) | `/es-ec/tungurahua/descubre/all-articles-e6824c833` | Brújula, explorar | Descubre / atractivos |
| `destination` | Destinos turísticos (25) | `/es-ec/tungurahua/destinos-turisticos/all-articles-epop4c833` | Mapa, destinos | Parroquias |

## Orden de la portada

1. Carrusel a sangre (Slick). Cada diapositiva tiene foto de fondo, título (`line-1`) y bajada (`line-2`), y enlaza a una ficha. En la revisión había seis: geoparque, corredor ecológico, lugares, provincia, aventura y cocina.
2. Columna lateral de filtros del destino: Provincias (1), Ciudades (9), Rurales (15).
3. Carrusel de tarjetas. Tres columnas en escritorio (`col-md-4`): imagen arriba, título en el cuerpo. Al cargar, varias vienen vacías y el script las rellena.
4. Texto largo de presentación.
5. «¿Qué debes saber…?»: bloques de pregunta y viñetas (qué es, dónde está, división, capital, clima, cómo llegar, qué hacer, qué comer).
6. «¿Para quién es ideal…?»: tres perfiles (naturaleza, cultura, aventura), cada uno con un consejo.
7. «Cantones»: un título y, debajo, un bloque por cantón (Ambato, Baños, Cevallos, Mocha, Patate, Pelileo, Píllaro, Quero, Tisaleo) con atractivos enlazados.
8. Otros atractivos.
9. Comida típica, en fichas cortas.
10. Cultura.
11. Historia.
12. Descargas (enlaces a PDF de mapas). No hay mapa embebido en el HTML de inicio: el mapa turístico es un archivo descargable y la página guarda una coordenada en `data-pos`.
13. «Sigue explorando las ciudades»: tarjetas con nombre y conteo.
14. Contacto: datos del centro turístico, redes y formulario «Enviar un mensaje».
15. Pie: dirección y horario, redes (Facebook, Twitter), logotipo de pie.

Iconos sueltos del pie práctico, por el nombre de la clase: `icon-faq` (ayuda), `icon-electricity` (energía), `icon-weather` (clima), `icon-money` (dinero), `icon-documents` (papeles), `icon-howtoget` (cómo llegar). Esos temas viven en páginas propias enlazadas desde el final del artículo.

## Páginas internas

Listado (`all-articles`): título «{sección} en Provincia de Tungurahua», filtros con conteo y rejilla de tarjetas.

Filtros vistos:

- Aprende: Memorias, Artes, Gastronomías, Artesanales, Tradiciones, Conocimientos.
- Vive: Naturaleza, Relax, Fiestas, Aventuras.
- Descubre: Áreas protegidas, Cultura, Naturaleza, Información turística.
- Destinos turísticos: Provincias, Ciudades, Rurales.

Ficha de ciudad (Ambato), en este orden: título, «qué debes saber», «para quién», turismo, gastronomía, cultura, historia, punto de partida, ruralidad, «te puede interesar» y contacto. La ficha repite el patrón de la portada en pequeño.

Cantones enlazados desde el inicio: Ambato, Baños, Cevallos, Mocha, Patate, Pelileo, Píllaro, Quero y Tisaleo.

## Qué se tomó para La Maná

Misma pieza visual: cabecera clara, fila de iconos con conteo, carrusel con título y bajada, buscador con chips, tarjetas de tres columnas, bloques «qué debes saber» y «para quién», fichas por territorio, gastronomía, agenda, galería, mapa, contacto y pie.

El territorio equivalente al cantón de la referencia es la parroquia. El sistema de boletos no se mezcla con esas fichas: queda en `/transporte`, con la marca de la cooperativa. El hero editable de taquilla alimenta la portada del portal (`ambito=portal`) y, por separado, la de Transporte (`ambito=transporte`).
