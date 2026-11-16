"""Textos editables del sitio. La semilla solo inserta claves que aún no existen."""

from sqlalchemy import text

from app.database import engine

CREAR = """
CREATE TABLE IF NOT EXISTS sitio_textos (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  espacio ENUM('portal', 'transporte', 'taxi', 'sitio') NOT NULL,
  clave VARCHAR(80) NOT NULL,
  etiqueta VARCHAR(140) NOT NULL,
  ayuda VARCHAR(300) NOT NULL DEFAULT '',
  aparece VARCHAR(220) NOT NULL DEFAULT '',
  valor TEXT NOT NULL,
  maximo SMALLINT UNSIGNED NOT NULL DEFAULT 400,
  orden INT NOT NULL DEFAULT 0,
  UNIQUE KEY uk_sitio_texto (espacio, clave)
) ENGINE=InnoDB
"""

# espacio, clave, etiqueta, ayuda, aparece, valor, maximo, orden
SEMILLA = [
    ("portal", "portal.recorrer.titulo", "Título de destacados", "El encabezado de la primera franja de tarjetas.", "Inicio del portal, debajo de la portada.", "Qué puedes recorrer", 80, 10),
    ("portal", "portal.saber.titulo", "Título de la sección práctica", "Encabezado de las tres notas sobre el cantón.", "Inicio del portal, sección clara.", "Qué debes saber sobre La Maná", 120, 20),
    ("portal", "portal.saber.donde.titulo", "Nota: dónde queda", "Título de la primera nota.", "Inicio del portal, bloque Qué debes saber.", "Dónde queda", 80, 21),
    ("portal", "portal.saber.donde.texto", "Texto: dónde queda", "Párrafo visible bajo ese título. No invente cifras.", "Inicio del portal, bloque Qué debes saber.", "La Maná es un cantón de Cotopaxi en el piso cálido, entre la sierra y la llanura que sigue hacia Quevedo. No es el páramo del volcán: es subtrópico húmedo, de finca y de río.", 500, 22),
    ("portal", "portal.saber.divide.titulo", "Nota: cómo se divide", "Título de la segunda nota.", "Inicio del portal, bloque Qué debes saber.", "Cómo se divide", 80, 23),
    ("portal", "portal.saber.divide.texto", "Texto: cómo se divide", "Mencione solo parroquias reales.", "Inicio del portal, bloque Qué debes saber.", "La cabecera lleva el nombre del cantón. Las parroquias rurales son Guasaganda, Pucayacu y El Carmen. Cada una tiene su ficha, editable desde el panel.", 500, 24),
    ("portal", "portal.saber.hacer.titulo", "Nota: qué hacer", "Título de la tercera nota.", "Inicio del portal, bloque Qué debes saber.", "Qué hacer", 80, 25),
    ("portal", "portal.saber.hacer.texto", "Texto: qué hacer", "Describa el plan sin tarifas ni horarios inventados.", "Inicio del portal, bloque Qué debes saber.", "Bajar al río San Pablo, caminar hacia cascadas como Zapanal, Tilipulo o Manguilita, y ver cacao o banano en una finca que acepte visita. El bus de la cooperativa está aparte, en Transporte.", 500, 26),
    ("portal", "portal.perfiles.titulo", "Título de perfiles", "Encabezado de «para quién es el viaje».", "Inicio del portal.", "Para quién es el viaje", 120, 30),
    ("portal", "portal.perfiles.rio.titulo", "Perfil del río", "Título de la primera tarjeta.", "Inicio del portal, perfiles.", "Quien busca río y sombra", 80, 31),
    ("portal", "portal.perfiles.rio.texto", "Texto del río", "Consejo breve, sin datos inventados.", "Inicio del portal, perfiles.", "La tarde en una orilla del San Pablo alcanza si el plan es simple. Mire el caudal antes de entrar al agua.", 400, 32),
    ("portal", "portal.perfiles.camina.titulo", "Perfil de quien camina", "Título de la segunda tarjeta.", "Inicio del portal, perfiles.", "Quien camina", 80, 33),
    ("portal", "portal.perfiles.camina.texto", "Texto de quien camina", "Sin tiempos de sendero inventados.", "Inicio del portal, perfiles.", "Las cascadas del entorno piden calzado cerrado y tiempo de sobra. No hay aquí un horario único de sendero.", 400, 34),
    ("portal", "portal.perfiles.paso.titulo", "Perfil de quien viene de paso", "Título de la tercera tarjeta.", "Inicio del portal, perfiles.", "Quien viene de paso", 80, 35),
    ("portal", "portal.perfiles.paso.texto", "Texto de quien viene de paso", "Indique que el pasaje se compra en Transporte.", "Inicio del portal, perfiles.", "La cabecera sirve de escala entre Latacunga y Quevedo. El pasaje se compra en Transporte, con el asiento ya elegido.", 400, 36),
    ("portal", "portal.contacto.titulo", "Título de contacto", "El título grande de la página.", "Página Contacto, arriba.", "Contacto", 80, 40),
    ("portal", "portal.contacto.bajada", "Bajada de contacto", "La frase bajo el título.", "Página Contacto, encabezado.", "Este buzón es del portal de turismo. No confirma una reserva de finca ni un pasaje.", 240, 41),
    ("portal", "portal.contacto.nota", "Aviso junto al formulario", "Texto a la izquierda del formulario.", "Página Contacto.", "Los pasajes se compran en Transporte.", 200, 42),
    ("portal", "portal.contacto.correo", "Correo del portal", "Se muestra como enlace mailto.", "Página Contacto y pie del portal.", "turismo@lamana.ec", 120, 43),
    ("portal", "portal.pie.frase", "Frase del pie", "El párrafo bajo el logo en el pie.", "Pie de todas las páginas del portal.", "Guía del cantón La Maná, en el subtrópico de Cotopaxi. Los textos se editan en el panel.", 240, 50),
    ("sitio", "sitio.nombre", "Nombre del sitio", "Cómo se llama el portal en el título del navegador.", "Pestaña del navegador en el portal.", "La Maná Recorres", 80, 1),
    ("transporte", "transporte.intro", "Frase de los servicios", "Un párrafo de la página de boletos.", "Página Transporte, junto a la búsqueda.", "Elige origen, destino y fecha. El asiento se aparta diez minutos y el pasaje se paga en línea.", 240, 10),
    ("transporte", "transporte.pie.frase", "Frase del pie de Transporte", "El texto bajo el logo de la cooperativa.", "Pie de las páginas de Transporte.", "Salidas diarias desde La Maná hacia la costa y la sierra. El asiento se elige antes de pagar.", 240, 20),
    ("taxi", "taxi.kicker", "Rótulo de taxi", "La línea pequeña sobre el título.", "Página /taxi, hoja del pedido.", "Taxi · La Maná", 60, 10),
    ("taxi", "taxi.titulo", "Título de taxi", "El título principal del pedido.", "Página /taxi, hoja del pedido.", "Pide un taxi", 80, 11),
    ("taxi", "taxi.ayuda", "Ayuda del mapa", "Explica el pin y el GPS.", "Página /taxi, bajo el botón de ubicación.", "Si el GPS no responde, arrastra el pin azul. El centro del mapa es la cabecera.", 240, 12),
]


async def asegurar_textos() -> None:
    async with engine.begin() as conexion:
        await conexion.execute(text(CREAR))
        for espacio, clave, etiqueta, ayuda, aparece, valor, maximo, orden in SEMILLA:
            await conexion.execute(
                text(
                    """
                    INSERT INTO sitio_textos (espacio, clave, etiqueta, ayuda, aparece, valor, maximo, orden)
                    SELECT :espacio, :clave, :etiqueta, :ayuda, :aparece, :valor, :maximo, :orden
                      FROM DUAL
                     WHERE NOT EXISTS (
                       SELECT 1 FROM sitio_textos WHERE espacio = :espacio AND clave = :clave
                     )
                    """
                ),
                {
                    "espacio": espacio,
                    "clave": clave,
                    "etiqueta": etiqueta,
                    "ayuda": ayuda,
                    "aparece": aparece,
                    "valor": valor,
                    "maximo": maximo,
                    "orden": orden,
                },
            )
