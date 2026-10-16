from datetime import datetime, timedelta, timezone

# Hora de Colombia, sin horario de verano. Coincide con default-time-zone=-05:00 de MySQL.
ZONA_COLOMBIA = timezone(timedelta(hours=-5))


def ahora_colombia() -> datetime:
    return datetime.now(ZONA_COLOMBIA).replace(tzinfo=None)
