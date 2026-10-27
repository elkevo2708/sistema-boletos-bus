from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.database import SesionLocal
from app.modelos import Rol, Usuario
from app.seguridad import JWTError, decodificar_token
from app.ws import gestor, gestor_taxi

router = APIRouter()


@router.websocket("/ws/viajes/{viaje_id}")
async def socket_viaje(websocket: WebSocket, viaje_id: int):
    await gestor.conectar(viaje_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await gestor.desconectar(viaje_id, websocket)


async def _usuario_ws(token: str) -> dict | None:
    if not token:
        return None
    try:
        payload = decodificar_token(token)
        usuario_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        return None
    async with SesionLocal() as sesion:
        fila = (
            await sesion.execute(
                select(Usuario, Rol.nombre).join(Rol, Rol.id == Usuario.rol_id).where(Usuario.id == usuario_id)
            )
        ).first()
    if fila is None or not fila[0].activo:
        return None
    return {"id": fila[0].id, "rol": fila[1]}


@router.websocket("/ws/taxi/flota")
async def socket_flota(websocket: WebSocket, token: str = ""):
    if await _usuario_ws(token) is None:
        await websocket.close(code=4401)
        return
    await gestor_taxi.conectar_flota(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await gestor_taxi.salir_flota(websocket)


@router.websocket("/ws/taxi/viajes/{viaje_id}")
async def socket_taxi(websocket: WebSocket, viaje_id: int, token: str = ""):
    if await _usuario_ws(token) is None:
        await websocket.close(code=4401)
        return
    await gestor_taxi.conectar_viaje(viaje_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await gestor_taxi.salir_viaje(viaje_id, websocket)
