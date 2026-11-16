"""Tablas y cursos de ejemplo del portal Aprende. No pisa lo que ya existe."""

from sqlalchemy import text

from app.database import engine

TABLAS = [
    """
    CREATE TABLE IF NOT EXISTS cursos_categorias (
      id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
      nombre VARCHAR(120) NOT NULL,
      slug VARCHAR(140) NOT NULL,
      orden INT NOT NULL DEFAULT 0,
      activo TINYINT(1) NOT NULL DEFAULT 1,
      UNIQUE KEY uk_curso_cat (slug)
    ) ENGINE=InnoDB
    """,
    """
    CREATE TABLE IF NOT EXISTS cursos_instructores (
      id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
      nombre VARCHAR(160) NOT NULL,
      institucion VARCHAR(160) NOT NULL DEFAULT '',
      bio VARCHAR(500) NOT NULL DEFAULT '',
      ejemplo TINYINT(1) NOT NULL DEFAULT 0
    ) ENGINE=InnoDB
    """,
    """
    CREATE TABLE IF NOT EXISTS cursos (
      id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
      categoria_id INT UNSIGNED NULL,
      instructor_id INT UNSIGNED NULL,
      titulo VARCHAR(180) NOT NULL,
      slug VARCHAR(180) NOT NULL,
      resumen VARCHAR(400) NOT NULL,
      descripcion TEXT NOT NULL,
      objetivos TEXT NOT NULL,
      requisitos VARCHAR(400) NOT NULL DEFAULT '',
      nivel ENUM('basico', 'intermedio', 'avanzado') NOT NULL DEFAULT 'basico',
      duracion_horas INT NOT NULL DEFAULT 4,
      modalidad ENUM('presencial', 'virtual', 'mixta') NOT NULL DEFAULT 'presencial',
      gratis TINYINT(1) NOT NULL DEFAULT 1,
      costo DECIMAL(8, 2) NULL,
      cupos INT NOT NULL DEFAULT 20,
      imagen VARCHAR(255) NULL,
      lugar VARCHAR(180) NOT NULL DEFAULT '',
      enlace VARCHAR(300) NOT NULL DEFAULT '',
      inicio DATE NULL,
      fin DATE NULL,
      certificado TINYINT(1) NOT NULL DEFAULT 0,
      destacado TINYINT(1) NOT NULL DEFAULT 0,
      activo TINYINT(1) NOT NULL DEFAULT 1,
      ejemplo TINYINT(1) NOT NULL DEFAULT 0,
      UNIQUE KEY uk_curso_slug (slug)
    ) ENGINE=InnoDB
    """,
    """
    CREATE TABLE IF NOT EXISTS curso_modulos (
      id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
      curso_id INT UNSIGNED NOT NULL,
      titulo VARCHAR(180) NOT NULL,
      orden INT NOT NULL DEFAULT 0,
      KEY idx_modulo_curso (curso_id)
    ) ENGINE=InnoDB
    """,
    """
    CREATE TABLE IF NOT EXISTS curso_lecciones (
      id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
      modulo_id INT UNSIGNED NOT NULL,
      titulo VARCHAR(180) NOT NULL,
      orden INT NOT NULL DEFAULT 0,
      tipo ENUM('texto', 'video', 'pdf') NOT NULL DEFAULT 'texto',
      cuerpo TEXT NOT NULL,
      video_url VARCHAR(300) NOT NULL DEFAULT '',
      pdf_url VARCHAR(300) NOT NULL DEFAULT '',
      KEY idx_leccion_modulo (modulo_id)
    ) ENGINE=InnoDB
    """,
    """
    CREATE TABLE IF NOT EXISTS curso_inscripciones (
      id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
      curso_id INT UNSIGNED NOT NULL,
      nombre VARCHAR(180) NOT NULL,
      documento VARCHAR(20) NOT NULL,
      email VARCHAR(180) NOT NULL,
      telefono VARCHAR(30) NOT NULL DEFAULT '',
      estado ENUM('inscrito', 'confirmado', 'asistio', 'certificado', 'cancelado') NOT NULL DEFAULT 'inscrito',
      usuario_id INT UNSIGNED NULL,
      creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
      UNIQUE KEY uk_inscripcion (curso_id, documento),
      KEY idx_inscripcion_curso (curso_id)
    ) ENGINE=InnoDB
    """,
    """
    CREATE TABLE IF NOT EXISTS curso_progreso (
      usuario_id INT UNSIGNED NOT NULL,
      leccion_id INT UNSIGNED NOT NULL,
      completada_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY (usuario_id, leccion_id)
    ) ENGINE=InnoDB
    """,
    """
    CREATE TABLE IF NOT EXISTS cursos_articulos (
      id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
      titulo VARCHAR(180) NOT NULL,
      slug VARCHAR(180) NOT NULL,
      resumen VARCHAR(400) NOT NULL,
      cuerpo TEXT NOT NULL,
      categoria VARCHAR(80) NOT NULL DEFAULT 'ciudadania',
      destacado TINYINT(1) NOT NULL DEFAULT 0,
      activo TINYINT(1) NOT NULL DEFAULT 1,
      ejemplo TINYINT(1) NOT NULL DEFAULT 0,
      UNIQUE KEY uk_articulo_slug (slug)
    ) ENGINE=InnoDB
    """,
]


async def asegurar_cursos() -> None:
    async with engine.begin() as conexion:
        for sentencia in TABLAS:
            await conexion.execute(text(sentencia))
        await _semilla(conexion)


async def _id(conexion, sql: str, params: dict):
    fila = (await conexion.execute(text(sql), params)).first()
    return None if fila is None else int(fila[0])


async def _semilla(conexion) -> None:
    categorias = [
        ("Turismo y atención", "turismo-atencion", 1),
        ("Emprendimiento", "emprendimiento", 2),
        ("Gastronomía", "gastronomia", 3),
        ("Idiomas", "idiomas", 4),
        ("Tecnología", "tecnologia", 5),
        ("Cultura e historia", "cultura-historia", 6),
        ("Medio ambiente", "medio-ambiente", 7),
        ("Seguridad vial", "seguridad-vial", 8),
    ]
    for nombre, slug, orden in categorias:
        await conexion.execute(
            text(
                """
                INSERT INTO cursos_categorias (nombre, slug, orden)
                SELECT :nombre, :slug, :orden FROM DUAL
                 WHERE NOT EXISTS (SELECT 1 FROM cursos_categorias WHERE slug = :slug)
                """
            ),
            {"nombre": nombre, "slug": slug, "orden": orden},
        )
    if await _id(conexion, "SELECT id FROM cursos WHERE slug = 'ejemplo-atencion-al-visitante'", {}):
        return
    instructor = await conexion.execute(
        text(
            """
            INSERT INTO cursos_instructores (nombre, institucion, bio, ejemplo)
            VALUES ('Equipo de ejemplo', 'Portal La Maná Recorres',
                    'Perfil de demostración. No es un docente ni una institución real.', 1)
            """
        )
    )
    inst = instructor.lastrowid
    cursos = [
        {
            "cat": "turismo-atencion",
            "titulo": "Ejemplo: atender a quien visita La Maná",
            "slug": "ejemplo-atencion-al-visitante",
            "resumen": "Curso de muestra para practicar la inscripción. No es una oferta oficial.",
            "descripcion": "Este curso es de demostración. Enseña, con textos propios del portal, cómo orientar a una persona que llega a la cabecera: el parque, el río y dónde se compra el pasaje.",
            "objetivos": "Ubicar la cabecera.\nExplicar que el pasaje se compra en Transporte.\nNo inventar horarios ni tarifas.",
            "requisitos": "Saber leer y tener ganas de practicar.",
            "nivel": "basico",
            "horas": 6,
            "modalidad": "presencial",
            "gratis": 1,
            "costo": None,
            "cupos": 18,
            "lugar": "Ejemplo: salón del portal",
            "enlace": "",
            "inicio": "2026-12-02",
            "certificado": 1,
            "destacado": 1,
            "modulos": [
                ("Bienvenida", [("Qué es este curso", "texto", "Es un ejercicio del portal. No certifica un oficio ni reemplaza un taller municipal.")]),
                ("La cabecera", [("El parque y el río", "texto", "La Maná está en el subtrópico de Cotopaxi. El río San Pablo y el parque central son puntos fáciles de explicar sin inventar distancias.")]),
            ],
        },
        {
            "cat": "emprendimiento",
            "titulo": "Ejemplo: contar el cacao de la finca",
            "slug": "ejemplo-cacao-de-finca",
            "resumen": "Cómo presentar un producto de finca sin afirmar precios ni marcas que no existen.",
            "descripcion": "Curso de demostración sobre emprendimiento rural. Habla del cacao como cultivo del cantón, no de una marca concreta.",
            "objetivos": "Describir el producto.\nDecir qué falta para vender de verdad.",
            "requisitos": "Ninguno.",
            "nivel": "basico",
            "horas": 8,
            "modalidad": "mixta",
            "gratis": 0,
            "costo": 5,
            "cupos": 12,
            "lugar": "Ejemplo: mixto",
            "enlace": "",
            "inicio": "2026-12-09",
            "certificado": 0,
            "destacado": 1,
            "modulos": [
                ("El relato", [("Una ficha honesta", "texto", "Un emprendimiento de ejemplo no publica teléfono ni dirección de un negocio real.")]),
            ],
        },
        {
            "cat": "gastronomia",
            "titulo": "Ejemplo: la mesa del subtrópico",
            "slug": "ejemplo-mesa-del-subtropico",
            "resumen": "Productos de la zona, sin decretar un restaurante.",
            "descripcion": "Demostración de un curso de cocina ciudadana. No copia recetas de un local ni inventa un menú oficial.",
            "objetivos": "Nombrar ingredientes del cantón.",
            "requisitos": "Ninguno.",
            "nivel": "basico",
            "horas": 4,
            "modalidad": "presencial",
            "gratis": 1,
            "costo": None,
            "cupos": 16,
            "lugar": "Ejemplo: cocina compartida",
            "enlace": "",
            "inicio": "2026-12-16",
            "certificado": 0,
            "destacado": 0,
            "modulos": [
                ("Ingredientes", [("Cacao y verde", "texto", "El subtrópico da cacao, verde y frutas. Este texto no fija una receta única.")]),
            ],
        },
        {
            "cat": "idiomas",
            "titulo": "Ejemplo: inglés para el mostrador",
            "slug": "ejemplo-ingles-de-mostrador",
            "resumen": "Frases cortas para orientar a quien no habla español. Curso virtual de muestra.",
            "descripcion": "Demostración de un curso virtual. Las lecciones son texto del portal; el video se puede pegar después desde el panel.",
            "objetivos": "Saludar y indicar el parque y la parada.",
            "requisitos": "Conexión a internet si se usa el video.",
            "nivel": "basico",
            "horas": 10,
            "modalidad": "virtual",
            "gratis": 1,
            "costo": None,
            "cupos": 40,
            "lugar": "",
            "enlace": "",
            "inicio": "2026-12-01",
            "certificado": 1,
            "destacado": 1,
            "modulos": [
                ("Primeras frases", [
                    ("Hola y bienvenida", "texto", "Hello. This is La Maná, in Cotopaxi. The park is a good place to start."),
                    ("Un video cuando lo tengas", "video", "Cuando el equipo tenga un video propio o libre, se pega el enlace de YouTube o Vimeo en esta lección."),
                ]),
            ],
        },
        {
            "cat": "seguridad-vial",
            "titulo": "Ejemplo: seguridad al subir al bus",
            "slug": "ejemplo-seguridad-al-subir",
            "resumen": "Hábitos simples en la parada y a bordo. No es un reglamento de la cooperativa.",
            "descripcion": "Curso de demostración. Recuerda llegar con tiempo, no cruzar por delante del bus y guardar el pasaje.",
            "objetivos": "Llegar antes de la salida.\nCuidar el pasillo.",
            "requisitos": "Ninguno.",
            "nivel": "basico",
            "horas": 3,
            "modalidad": "presencial",
            "gratis": 1,
            "costo": None,
            "cupos": 25,
            "lugar": "Ejemplo: terminal",
            "enlace": "",
            "inicio": "2026-12-20",
            "certificado": 0,
            "destacado": 0,
            "modulos": [
                ("En la parada", [("El andén", "texto", "La taquilla de la cooperativa abre temprano. Este curso de ejemplo no cambia ese horario.")]),
            ],
        },
        {
            "cat": "medio-ambiente",
            "titulo": "Ejemplo: cuidar la orilla del río",
            "slug": "ejemplo-orilla-del-rio",
            "resumen": "Qué sí y qué no se deja en la orilla del San Pablo.",
            "descripcion": "Demostración de un curso ambiental. No publica mediciones ni prohíbe un balneario concreto.",
            "objetivos": "Llevarse la basura.\nMirar el caudal antes de entrar al agua.",
            "requisitos": "Ninguno.",
            "nivel": "basico",
            "horas": 4,
            "modalidad": "presencial",
            "gratis": 1,
            "costo": None,
            "cupos": 20,
            "lugar": "Ejemplo: orilla",
            "enlace": "",
            "inicio": "2027-01-10",
            "certificado": 0,
            "destacado": 0,
            "modulos": [
                ("La visita", [("Agua y basura", "texto", "El caudal cambia con la lluvia. La decisión de meterse al agua es de cada persona.")]),
            ],
        },
    ]
    for curso in cursos:
        cat_id = await _id(conexion, "SELECT id FROM cursos_categorias WHERE slug = :slug", {"slug": curso["cat"]})
        alta = await conexion.execute(
            text(
                """
                INSERT INTO cursos (
                  categoria_id, instructor_id, titulo, slug, resumen, descripcion, objetivos, requisitos,
                  nivel, duracion_horas, modalidad, gratis, costo, cupos, lugar, enlace, inicio,
                  certificado, destacado, activo, ejemplo
                ) VALUES (
                  :cat, :inst, :titulo, :slug, :resumen, :descripcion, :objetivos, :requisitos,
                  :nivel, :horas, :modalidad, :gratis, :costo, :cupos, :lugar, :enlace, :inicio,
                  :certificado, :destacado, 1, 1
                )
                """
            ),
            {
                "cat": cat_id,
                "inst": inst,
                "titulo": curso["titulo"],
                "slug": curso["slug"],
                "resumen": curso["resumen"],
                "descripcion": curso["descripcion"],
                "objetivos": curso["objetivos"],
                "requisitos": curso["requisitos"],
                "nivel": curso["nivel"],
                "horas": curso["horas"],
                "modalidad": curso["modalidad"],
                "gratis": curso["gratis"],
                "costo": curso["costo"],
                "cupos": curso["cupos"],
                "lugar": curso["lugar"],
                "enlace": curso["enlace"],
                "inicio": curso["inicio"],
                "certificado": curso["certificado"],
                "destacado": curso["destacado"],
            },
        )
        curso_id = alta.lastrowid
        for orden_m, (titulo_m, lecciones) in enumerate(curso["modulos"], start=1):
            modulo = await conexion.execute(
                text("INSERT INTO curso_modulos (curso_id, titulo, orden) VALUES (:curso, :titulo, :orden)"),
                {"curso": curso_id, "titulo": titulo_m, "orden": orden_m},
            )
            for orden_l, (titulo_l, tipo, cuerpo) in enumerate(lecciones, start=1):
                await conexion.execute(
                    text(
                        """
                        INSERT INTO curso_lecciones (modulo_id, titulo, orden, tipo, cuerpo, video_url, pdf_url)
                        VALUES (:modulo, :titulo, :orden, :tipo, :cuerpo, '', '')
                        """
                    ),
                    {"modulo": modulo.lastrowid, "titulo": titulo_l, "orden": orden_l, "tipo": tipo, "cuerpo": cuerpo},
                )
    articulos = [
        ("Ejemplo: de parroquia a cantón", "ejemplo-de-parroquia-a-canton", "historia",
         "La Maná recuerda el 19 de mayo como fecha de cantonización.",
         "Este artículo es de demostración. La cantonización se conmemora en torno al 19 de mayo. El programa de cada año lo fija el municipio; aquí no se inventan horas ni artistas.", 1),
        ("Ejemplo: servicios que se preguntan en el parque", "ejemplo-servicios-del-parque", "servicios",
         "Cómo orientar sin publicar un trámite que no verificamos.",
         "Este texto es de demostración. Para un trámite municipal hay que confirmar en la fuente oficial del día. El portal no inventa ventanillas.", 0),
        ("Ejemplo: convocatoria de un taller", "ejemplo-convocatoria-taller", "convocatoria",
         "Una convocatoria ficticia para ver cómo se anuncia un taller.",
         "No es una convocatoria real. Sirve para probar la sección de divulgación hasta que un operador publique una fecha verdadera.", 1),
    ]
    for titulo, slug, categoria, resumen, cuerpo, destacado in articulos:
        await conexion.execute(
            text(
                """
                INSERT INTO cursos_articulos (titulo, slug, resumen, cuerpo, categoria, destacado, ejemplo)
                SELECT :titulo, :slug, :resumen, :cuerpo, :categoria, :destacado, 1 FROM DUAL
                 WHERE NOT EXISTS (SELECT 1 FROM cursos_articulos WHERE slug = :slug)
                """
            ),
            {"titulo": titulo, "slug": slug, "resumen": resumen, "cuerpo": cuerpo, "categoria": categoria, "destacado": destacado},
        )
