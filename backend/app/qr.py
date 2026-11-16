import base64
import io
import json

import qrcode


def png_base64(contenido: dict) -> str:
    imagen = qrcode.make(json.dumps(contenido, ensure_ascii=False))
    buffer = io.BytesIO()
    imagen.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")
