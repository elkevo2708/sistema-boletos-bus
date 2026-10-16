# Cooperativa de Transporte La Maná

Sistema de venta de boletos de la cooperativa, con sede en La Maná, Cotopaxi. La interfaz, la API y la base de datos están en español. Los precios se muestran en dólares de los Estados Unidos. Un asiento de un viaje solo puede estar ocupado por un boleto activo: la garantía es un índice único sobre la columna generada `ocupa_asiento`.

## Cómo ejecutarlo

Requisito: Docker con Compose v2.

```bash
docker compose up --build
```

- Aplicación: http://localhost:8080
- API y documentación: http://localhost:8000/docs
- MySQL: `localhost:3306`, base `boletos`, usuario `boletos`, contraseña `boletos`

La primera arrancada crea el esquema, los disparadores, el evento que expira reservas y los datos de prueba (ciudades del Ecuador, rutas, noticias, anuncios y fotos). Los horarios están en hora de Ecuador (UTC−5). Las imágenes de la galería viven en el volumen `medios`, montado en `/app/medios`, y se sirven en `/medios`.

Para volver a cargar la semilla hay que borrar también los volúmenes:

```bash
docker compose down -v
docker compose up --build
```

## Cuenta administradora

| Campo | Valor |
| --- | --- |
| Correo | `admin@lamana.local` |
| Contraseña | `Admin123!` |
| Documento | `1000000001` |

La contraseña se guarda con bcrypt. El cliente se registra desde **Ingresar → Crear cuenta**. El correo de prueba del administrador usa un dominio reservado: el alta pública exige un dominio real, por ejemplo `gmail.com`.

## Recorrido

1. En el inicio, elige origen, destino y fecha. Mañana hay salidas de prueba, por ejemplo La Maná → Quevedo y La Maná → Latacunga.
2. La franja y la ventana de promoción salen de los anuncios vigentes. Se pueden cerrar; quedan ocultas en esa pestaña del navegador.
3. **Noticias** lista las publicaciones y abre cada nota. **Galería** muestra la unidad real, destinos y terminales; al pulsar una foto se abre el visor. **Encomiendas** muestra la cobertura (La Maná, Quevedo, Quinsaloma, Moraspungo, Latacunga, Ambato, Quito, Guayaquil, Durán y Empalme) y los teléfonos: matriz 099 412 7992, Quevedo 098 040 5468, Guayaquil 099 117 5522, Durán 099 117 2085.
4. En el mapa, verde es libre, azul es el asiento elegido, gris es ocupado y el rayado es bloqueado. El mapa se actualiza en vivo por `/ws/viajes/{id}`.
5. Reserva (10 minutos) y elige el método: tarjeta, transferencia, PayPhone o efectivo en ventanilla. El cobro está simulado. El número de tarjeta no sale del navegador. El backend marca el boleto como pagado y devuelve el QR en PNG.
6. En **Taquilla**, la cuenta administradora crea viajes, cambia la tarifa (queda una fila en `auditoria`), consulta las ventas del día y administra noticias, anuncios e imágenes.

## Pagos

`app/pagos.py` define `ProveedorPago`. Cada método (`tarjeta`, `transferencia`, `payphone`, `efectivo`) tiene un adaptador en `REGISTRO`. Hoy todos son `PasarelaSimulada`: aprueban el cobro y devuelven el proveedor `simulado:<metodo>`. Una pasarela real reemplaza esa clase y se registra con la misma clave, sin tocar la reserva ni el QR.

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
| POST | `/boletos/{codigo}/pagar` | `SELECT FOR UPDATE`, método de pago, referencia única, QR |
| POST | `/boletos/{codigo}/cancelar` | Libera el asiento |
| GET | `/blog` y `/blog/{slug}` | Noticias y destinos publicados |
| GET | `/anuncios` | Promociones vigentes (franja o ventana) |
| GET | `/galeria` | Fotos públicas |
| POST | `/admin/viajes` | Crea un viaje (rol administrador) |
| PATCH | `/admin/rutas/{id}/tarifa` | Cambia la tarifa y audita |
| GET | `/admin/ventas?fecha` | Reporte diario |
| CRUD | `/admin/blog`, `/admin/anuncios`, `/admin/galeria` | Contenido. La galería recibe `multipart` (JPG, PNG o WebP, hasta 5 MB) |
| WS | `/ws/viajes/{id}` | Cambios de asiento |

Las consultas van parametrizadas. El frontend publicado en el puerto 8080 proxifica `/api`, `/ws` y `/medios` hacia el backend. CORS permite además `http://localhost:8080` y `http://localhost:5173`.

## Estructura

```
database/schema.sql      MySQL 8, InnoDB, utf8mb4
backend/                  FastAPI, SQLAlchemy 2 async, aiomysql
backend/medios-semilla/   Fotos que el contenedor copia al volumen la primera vez
frontend/                 React, Vite, react-router-dom
docker-compose.yml
```

Variables del backend: `DATABASE_URL`, `JWT_SECRET`, `JWT_ALGORITHM`, `ACCESS_TOKEN_MINUTOS`, `REFRESH_TOKEN_DIAS`, `CORS_ORIGINS`.
