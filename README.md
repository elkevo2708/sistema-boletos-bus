# VíaAndina

Sistema de venta de boletos de bus intermunicipal. La interfaz, la API y la base de datos están en español. Un asiento de un viaje solo puede estar ocupado por un boleto activo: la garantía es un índice único sobre la columna generada `ocupa_asiento`.

## Cómo ejecutarlo

Requisito: Docker con Compose v2.

```bash
docker compose up --build
```

- Aplicación: http://localhost:8080
- API y documentación: http://localhost:8000/docs
- MySQL: `localhost:3306`, base `boletos`, usuario `boletos`, contraseña `boletos`

La primera arrancada crea el esquema, los disparadores, el evento que expira reservas y los datos de prueba. Los horarios están en hora de Colombia (UTC−5).

Para volver a cargar la semilla:

```bash
docker compose down -v
docker compose up --build
```

## Cuenta administradora

| Campo | Valor |
| --- | --- |
| Correo | `admin@viaandina.local` |
| Contraseña | `Admin123!` |
| Documento | `1000000001` |

La contraseña se guarda con bcrypt. El cliente se registra desde **Ingresar → Crear cuenta**.

## Recorrido

1. En **Buscar**, elige origen, destino y fecha. Mañana hay salidas de prueba, por ejemplo Bogotá → Medellín y Bogotá → Cali.
2. Abre el mapa. Verde es libre, azul es el asiento elegido, gris es ocupado y el rayado es bloqueado.
3. Reserva (10 minutos) e indica una referencia de pago simulada. El backend marca el boleto como pagado y devuelve el QR en PNG.
4. En **Taquilla**, la cuenta administradora crea viajes (la llegada sale de la duración de la ruta), cambia la tarifa —queda una fila en `auditoria`— y consulta las ventas del día.

El mapa se actualiza en vivo por el WebSocket `/ws/viajes/{id}` después de reservar, pagar o cancelar.

## Qué garantiza que no se venda de más

`boletos.ocupa_asiento` vale `1` si el estado es `reservado`, `pagado` o `usado`, y `NULL` en otro caso. El índice `UNIQUE (viaje_id, asiento_id, ocupa_asiento)` admite varios boletos históricos del mismo asiento (el `NULL` no choca) y solo una ocupación vigente. Reservar es un `INSERT` directo: si dos compras llegan juntas, MySQL rechaza la segunda y la API responde `409` con el mensaje `Asiento no disponible`.

Un disparador exige que el asiento pertenezca al bus del viaje y que el viaje esté `programado` y en el futuro (`422` si no). Otro disparador impide programar un viaje con un bus que no esté `operativo` o que ya tenga un viaje solapado. Cada minuto, el evento `ev_expirar_reservas` pasa a `expirado` las reservas vencidas y así libera el asiento.

La vista `v_disponibilidad` clasifica cada puesto del viaje en `libre`, `bloqueado` u `ocupado`. `v_ventas_dia` suma los pagos `aprobado` por fecha y ruta.

## API

| Método | Ruta | Uso |
| --- | --- | --- |
| POST | `/auth/registro` | Alta de cliente y tokens |
| POST | `/auth/login` | Formulario OAuth2 (`username` = correo) |
| POST | `/auth/refresh` | Rota el refresh token (hash SHA-256, revocable) |
| POST | `/auth/logout` | Revoca el refresh token |
| GET | `/ciudades` | Origen y destino del buscador |
| GET | `/viajes?origen&destino&fecha` | Salidas con puestos libres |
| GET | `/viajes/{id}/asientos` | Mapa leído de `v_disponibilidad` |
| POST | `/boletos/reservar` | Reserva 10 minutos |
| POST | `/boletos/{codigo}/pagar` | `SELECT FOR UPDATE`, pago idempotente por `referencia_ext`, QR |
| POST | `/boletos/{codigo}/cancelar` | Libera el asiento |
| POST | `/admin/viajes` | Crea un viaje (rol administrador) |
| PATCH | `/admin/rutas/{id}/tarifa` | Cambia la tarifa y audita |
| GET | `/admin/ventas?fecha` | Reporte diario |
| WS | `/ws/viajes/{id}` | Cambios de asiento |

Las consultas van parametrizadas. El frontend publicado en el puerto 8080 proxifica `/api` y `/ws` hacia el backend; CORS permite además `http://localhost:8080` y `http://localhost:5173`.

## Estructura

```
database/schema.sql    MySQL 8, InnoDB, utf8mb4
backend/               FastAPI, SQLAlchemy 2 async, aiomysql
frontend/              React, Vite, react-router-dom
docker-compose.yml
```

Variables del backend: `DATABASE_URL`, `JWT_SECRET`, `JWT_ALGORITHM`, `ACCESS_TOKEN_MINUTOS`, `REFRESH_TOKEN_DIAS`, `CORS_ORIGINS`.
