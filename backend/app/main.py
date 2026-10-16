import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database import engine
from app.routers import admin, auth, boletos, ciudades, tiempo_real, viajes

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("viaandina")


@asynccontextmanager
async def vida(_app: FastAPI):
    ultimo: Exception | None = None
    for intento in range(30):
        try:
            async with engine.connect() as conexion:
                await conexion.execute(text("SELECT 1"))
            log.info("Conexión a MySQL lista")
            break
        except Exception as exc:
            ultimo = exc
            log.warning("MySQL no disponible (%s/30): %s", intento + 1, exc)
            await asyncio.sleep(2)
    else:
        raise RuntimeError("No se pudo conectar a MySQL") from ultimo
    yield
    await engine.dispose()


app = FastAPI(title="VíaAndina", version="1.0.0", lifespan=vida)
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
app.include_router(tiempo_real.router)


@app.get("/salud")
async def salud():
    return {"estado": "ok"}
