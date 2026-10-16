from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.ws import gestor

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
