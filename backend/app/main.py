import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.config import settings
from app.database import engine
from app.horarios import generar_salidas
from app.migraciones import asegurar_esquema
from app.routers import admin, admin_contenido, auth, boletos, ciudades, contenido, facturacion, pagos_publico, portada, tiempo_real, viajes

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("lamana")


@asynccontextmanager
async def vida(_app: FastAPI):
    ultimo: Exception | None = None
    for intento in range(30):
        try:
            async with engine.connect() as conexion:
                await conexion.execute(text("SELECT 1"))
            await asegurar_esquema()
            creados = await generar_salidas()
            log.info("Conexión a MySQL lista. Salidas nuevas del horario: %s", creados)
            break
        except Exception as exc:
            ultimo = exc
            log.warning("MySQL no disponible (%s/30): %s", intento + 1, exc)
            await asyncio.sleep(2)
    else:
        raise RuntimeError("No se pudo conectar a MySQL") from ultimo
    yield
    await engine.dispose()


app = FastAPI(title="Cooperativa de Transporte La Maná", version="1.0.0", lifespan=vida)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origenes_cors,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(ciudades.router, prefix="/ciudades", tags=["ciudades"])
app.include_router(viajes.router, prefix="/viajes", tags=["viajes"])
app.include_router(boletos.router, prefix="/boletos", tags=["boletos"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(admin_contenido.router, prefix="/admin", tags=["admin"])
app.include_router(contenido.router)
app.include_router(facturacion.router)
app.include_router(pagos_publico.router)
app.include_router(portada.router)
app.include_router(tiempo_real.router)
Path("/app/medios").mkdir(parents=True, exist_ok=True)
app.mount("/medios", StaticFiles(directory="/app/medios"), name="medios")


@app.get("/salud")
async def salud():
    return {"estado": "ok"}
