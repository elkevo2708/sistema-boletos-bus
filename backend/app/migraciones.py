"""Ajustes de esquema para bases que ya estaban creadas."""

from pathlib import Path

from sqlalchemy import text

from app.database import engine

SQL_PAGOS = Path(__file__).parent / "sql" / "migracion_pagos_portada.sql"
SQL_TURISMO = Path(__file__).parent / "sql" / "migracion_turismo.sql"
SQL_PORTAL_TAXI = Path(__file__).parent / "sql" / "migracion_portal_taxi.sql"
SQL_IMAGENES = Path(__file__).parent / "sql" / "migracion_imagenes.sql"


async def _ejecutar(sql: str) -> None:
    async with engine.begin() as conexion:
        await conexion.execute(text(sql))


async def asegurar_esquema() -> None:
    async with engine.connect() as conexion:
        filas = (await conexion.execute(text("SHOW COLUMNS FROM anuncios"))).all()
    nombres = {fila[0] for fila in filas}
    if "texto_boton" not in nombres:
        await _ejecutar("ALTER TABLE anuncios ADD COLUMN texto_boton VARCHAR(80) NULL AFTER enlace")
    if "formato" not in nombres:
        await _ejecutar(
            "ALTER TABLE anuncios ADD COLUMN formato ENUM('texto', 'imagen') NOT NULL DEFAULT 'texto' AFTER texto_boton"
        )
    if "imagen" not in nombres:
        await _ejecutar("ALTER TABLE anuncios ADD COLUMN imagen VARCHAR(255) NULL AFTER formato")
    await _ejecutar("ALTER TABLE anuncios MODIFY mensaje VARCHAR(500) NULL")
    await _aplicar_archivo(SQL_PAGOS)
    await _ambito_portada()
    await _aplicar_archivo(SQL_TURISMO)
    await _aplicar_archivo(SQL_PORTAL_TAXI)
    await _ejemplo_taxi()
    await _aplicar_archivo(SQL_IMAGENES)
    from app.textos_semilla import asegurar_textos
    await asegurar_textos()
    from app.cursos_semilla import asegurar_cursos
    await asegurar_cursos()
    await _taxi_app()


def _sentencias(contenido: str) -> list[str]:
    """Parte el archivo por `;` fuera de textos. Un punto y coma dentro de una ficha no corta la sentencia."""
    lineas = []
    for linea in contenido.splitlines():
        if linea.strip().startswith("--"):
            continue
        lineas.append(linea)
    texto = "\n".join(lineas)
    partes: list[str] = []
    actual: list[str] = []
    en_texto = False
    indice = 0
    while indice < len(texto):
        caracter = texto[indice]
        if en_texto:
            actual.append(caracter)
            if caracter == "\\" and indice + 1 < len(texto):
                actual.append(texto[indice + 1])
                indice += 2
                continue
            if caracter == "'":
                if indice + 1 < len(texto) and texto[indice + 1] == "'":
                    actual.append("'")
                    indice += 2
                    continue
                en_texto = False
            indice += 1
            continue
        if caracter == "'":
            en_texto = True
            actual.append(caracter)
            indice += 1
            continue
        if caracter == ";":
            sentencia = "".join(actual).strip()
            if sentencia:
                partes.append(sentencia)
            actual = []
            indice += 1
            continue
        actual.append(caracter)
        indice += 1
    resto = "".join(actual).strip()
    if resto:
        partes.append(resto)
    return partes


async def _ambito_portada() -> None:
    async with engine.connect() as conexion:
        columnas = (await conexion.execute(text("SHOW COLUMNS FROM portada"))).all()
    if "ambito" not in {fila[0] for fila in columnas}:
        await _ejecutar(
            "ALTER TABLE portada ADD COLUMN ambito ENUM('portal', 'transporte') NOT NULL DEFAULT 'portal' AFTER activo"
        )
    await _ejecutar(
        """
        UPDATE portada
           SET ambito = 'transporte'
         WHERE enlace = '/bus-lamana.jpg'
            OR titulo LIKE '%asiento ya elegido%'
            OR titulo LIKE '%unidad naranja%'
        """
    )


async def _ejemplo_taxi() -> None:
    async with engine.connect() as conexion:
        tablas = (await conexion.execute(text("SHOW TABLES LIKE 'taxi_viajes'"))).first()
        if tablas is None:
            return
        columnas = (await conexion.execute(text("SHOW COLUMNS FROM taxi_viajes"))).all()
    if "ejemplo" not in {fila[0] for fila in columnas}:
        await _ejecutar("ALTER TABLE taxi_viajes ADD COLUMN ejemplo TINYINT(1) NOT NULL DEFAULT 0 AFTER comentario")
    async with engine.connect() as conexion:
        columnas_conductor = (await conexion.execute(text("SHOW COLUMNS FROM taxi_conductores"))).all()
    if "rumbo" not in {fila[0] for fila in columnas_conductor}:
        await _ejecutar("ALTER TABLE taxi_conductores ADD COLUMN rumbo SMALLINT NULL AFTER lng")


async def _taxi_app() -> None:
    """Columnas y tablas del viaje tipo app. No borra filas."""
    async with engine.connect() as conexion:
        if (await conexion.execute(text("SHOW TABLES LIKE 'taxi_viajes'"))).first() is None:
            return
        columnas = {fila[0] for fila in (await conexion.execute(text("SHOW COLUMNS FROM taxi_viajes"))).all()}
        estado = next((fila for fila in (await conexion.execute(text("SHOW COLUMNS FROM taxi_viajes"))).all() if fila[0] == "estado"), None)
    if "codigo" not in columnas:
        await _ejecutar("ALTER TABLE taxi_viajes ADD COLUMN codigo CHAR(4) NULL AFTER estado")
    if "pasajeros" not in columnas:
        await _ejecutar("ALTER TABLE taxi_viajes ADD COLUMN pasajeros TINYINT NOT NULL DEFAULT 1 AFTER codigo")
    if "nota" not in columnas:
        await _ejecutar("ALTER TABLE taxi_viajes ADD COLUMN nota VARCHAR(180) NOT NULL DEFAULT '' AFTER pasajeros")
    if "servicio" not in columnas:
        await _ejecutar("ALTER TABLE taxi_viajes ADD COLUMN servicio VARCHAR(40) NOT NULL DEFAULT 'estandar' AFTER nota")
    if "propina" not in columnas:
        await _ejecutar("ALTER TABLE taxi_viajes ADD COLUMN propina DECIMAL(8,2) NULL AFTER servicio")
    if "seguimiento" not in columnas:
        await _ejecutar("ALTER TABLE taxi_viajes ADD COLUMN seguimiento CHAR(8) NULL AFTER propina")
    if estado is not None and "llego" not in str(estado[1]):
        await _ejecutar(
            "ALTER TABLE taxi_viajes MODIFY estado ENUM('solicitado','asignado','en_camino','llego','a_bordo','finalizado','cancelado') NOT NULL DEFAULT 'solicitado'"
        )
    await _ejecutar(
        """
        CREATE TABLE IF NOT EXISTS taxi_lugares (
          id INT AUTO_INCREMENT PRIMARY KEY,
          nombre VARCHAR(120) NOT NULL,
          tipo VARCHAR(40) NOT NULL,
          lat DECIMAL(10,7) NOT NULL,
          lng DECIMAL(10,7) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )
    await _ejecutar(
        """
        CREATE TABLE IF NOT EXISTS taxi_guardados (
          id INT AUTO_INCREMENT PRIMARY KEY,
          usuario_id INT NOT NULL,
          etiqueta VARCHAR(20) NOT NULL,
          texto VARCHAR(120) NOT NULL,
          lat DECIMAL(10,7) NOT NULL,
          lng DECIMAL(10,7) NOT NULL,
          UNIQUE KEY uq_guardado (usuario_id, etiqueta)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )
    await _ejecutar(
        """
        CREATE TABLE IF NOT EXISTS taxi_sos (
          id INT AUTO_INCREMENT PRIMARY KEY,
          usuario_id INT NOT NULL,
          viaje_id INT NULL,
          lat DECIMAL(10,7) NOT NULL,
          lng DECIMAL(10,7) NOT NULL,
          creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )
    await _ejecutar(
        """
        INSERT INTO taxi_lugares (nombre, tipo, lat, lng)
        SELECT * FROM (
          SELECT 'Terminal terrestre' AS nombre, 'frecuente' AS tipo, -0.9418 AS lat, -79.2310 AS lng
          UNION ALL SELECT 'Parque central', 'frecuente', -0.9406, -79.2344
          UNION ALL SELECT 'Río San Pablo', 'atractivo', -0.9330, -79.2280
        ) semilla
        WHERE NOT EXISTS (SELECT 1 FROM taxi_lugares LIMIT 1)
        """
    )


async def _aplicar_archivo(ruta: Path) -> None:
    for sentencia in _sentencias(ruta.read_text(encoding="utf-8")):
        await _ejecutar(sentencia)
