"""Tope sencillo en memoria para solicitudes y GPS."""

import time

_marcas: dict[str, list[float]] = {}


def permitir(clave: str, cantidad: int, ventana_seg: float) -> bool:
    ahora = time.monotonic()
    marcas = [marca for marca in _marcas.get(clave, []) if ahora - marca < ventana_seg]
    if len(marcas) >= cantidad:
        _marcas[clave] = marcas
        return False
    marcas.append(ahora)
    _marcas[clave] = marcas
    return True
