import asyncio
import logging

from fastapi import WebSocket
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

log = logging.getLogger("viaandina")


class GestorAsientos:
    def __init__(self) -> None:
        self._salas: dict[int, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def conectar(self, viaje_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._salas.setdefault(viaje_id, set()).add(websocket)

    async def desconectar(self, viaje_id: int, websocket: WebSocket) -> None:
        async with self._lock:
            sala = self._salas.get(viaje_id)
            if sala is not None:
                sala.discard(websocket)
                if not sala:
                    self._salas.pop(viaje_id, None)

    async def emitir(self, viaje_id: int, mensaje: dict) -> None:
        async with self._lock:
            sala = list(self._salas.get(viaje_id, ()))
        muertos: list[WebSocket] = []
        for websocket in sala:
            try:
                await websocket.send_json(mensaje)
            except Exception:
                muertos.append(websocket)
        if muertos:
            async with self._lock:
                sala_viva = self._salas.get(viaje_id)
                if sala_viva is not None:
                    for websocket in muertos:
                        sala_viva.discard(websocket)


gestor = GestorAsientos()


class GestorTaxi:
    def __init__(self) -> None:
        self.flota: set[WebSocket] = set()
        self.viajes: dict[int, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def conectar_flota(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self.flota.add(websocket)

    async def conectar_viaje(self, viaje_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self.viajes.setdefault(viaje_id, set()).add(websocket)

    async def salir_flota(self, websocket: WebSocket) -> None:
        async with self._lock:
            self.flota.discard(websocket)

    async def salir_viaje(self, viaje_id: int, websocket: WebSocket) -> None:
        async with self._lock:
            sala = self.viajes.get(viaje_id)
            if sala is not None:
                sala.discard(websocket)
                if not sala:
                    self.viajes.pop(viaje_id, None)

    async def _enviar(self, sockets: list[WebSocket], mensaje: dict) -> None:
        for websocket in sockets:
            try:
                await websocket.send_json(mensaje)
            except Exception:
                log.debug("Socket de taxi cerrado")

    async def emitir_flota(self, mensaje: dict) -> None:
        async with self._lock:
            sockets = list(self.flota)
        await self._enviar(sockets, mensaje)

    async def emitir_viaje(self, viaje_id: int, mensaje: dict) -> None:
        async with self._lock:
            sockets = list(self.viajes.get(viaje_id, ()))
        await self._enviar(sockets, mensaje)


gestor_taxi = GestorTaxi()


async def publicar_asiento(sesion: AsyncSession, viaje_id: int, asiento_id: int) -> None:
    fila = (
        await sesion.execute(
            text(
                """
                SELECT asiento_id, numero, estado_asiento
                  FROM v_disponibilidad
                 WHERE viaje_id = :viaje_id
                   AND asiento_id = :asiento_id
                """
            ),
            {"viaje_id": viaje_id, "asiento_id": asiento_id},
        )
    ).mappings().first()
    if fila is None:
        return
    try:
        await gestor.emitir(
            viaje_id,
            {
                "tipo": "asiento",
                "viaje_id": viaje_id,
                "asiento_id": int(fila["asiento_id"]),
                "numero": int(fila["numero"]),
                "estado": fila["estado_asiento"],
            },
        )
    except Exception:
        log.exception("No se pudo publicar el cambio del asiento %s", asiento_id)
