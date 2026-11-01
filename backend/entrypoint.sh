#!/bin/sh
set -e
mkdir -p /app/medios
if [ ! -f /app/medios/.semilla ]; then
  cp -a /app/medios-semilla/. /app/medios/
  touch /app/medios/.semilla
fi
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
