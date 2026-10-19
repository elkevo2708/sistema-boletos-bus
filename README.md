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

La primera arrancada crea el esquema, los disparadores, el evento que expira reservas y los datos de prueba (ciudades del Ecuador, rutas, noticias, anuncios y fotos). Los horarios están en hora de Ecuador (UTC−5). Al arrancar, el backend aplica `database/migracion_horarios.sql` (la misma copia vive en `backend/app/sql/`): crea la tabla `horarios` y, sin borrar viajes ni ciudades, deja dos salidas diarias en ambos sentidos entre las ciudades de la semilla para los próximos 30 días. Se puede volver a ejecutar; solo inserta lo que falta. En taquilla, **Generar salidas** hace lo mismo. Las imágenes de la galería viven en el volumen `medios`, montado en `/app/medios`, y se sirven en `/medios`.

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

1. En el inicio, elige origen, destino y fecha. La fecha usa la hora de Ecuador (`America/Guayaquil`). Hay dos salidas al día, ida y vuelta, entre todas las ciudades de la semilla, durante los próximos 30 días. Si ese día no hay cupo, la página dice «No hay salidas para esa fecha» y propone los siguientes días y el regreso.
2. La franja y la ventana de promoción salen de los anuncios vigentes. En taquilla cada anuncio es de texto o de imagen, con fechas y un interruptor de activo. La ventana se cierra y queda oculta en esa pestaña del navegador. En taquilla no se muestra, para no tapar los formularios.
3. **Noticias** lista las publicaciones y abre cada nota. **Galería** muestra la unidad real, destinos y terminales; al pulsar una foto se abre el visor. **Encomiendas** muestra la cobertura (La Maná, Quevedo, Quinsaloma, Moraspungo, Latacunga, Ambato, Quito, Guayaquil, Durán y Empalme) y los teléfonos: matriz 099 412 7992, Quevedo 098 040 5468, Guayaquil 099 117 5522, Durán 099 117 2085.
4. En el mapa, verde es libre, azul es el asiento elegido, gris es ocupado y el rayado es bloqueado. El mapa se actualiza en vivo por `/ws/viajes/{id}`.
5. Reserva (10 minutos) y elige el método: tarjeta, transferencia, PayPhone o efectivo en ventanilla. El cobro está simulado. El número de tarjeta no sale del navegador. En el mismo paso se piden los datos de facturación. Si la cédula o el RUC ya se usaron, se completan los nombres. El backend marca el boleto como pagado, emite la factura y devuelve el QR en PNG junto con el RIDE.
6. **Mis facturas** lista los comprobantes de la cuenta y permite descargar el XML y el RIDE.
7. En **Taquilla**, la cuenta administradora crea ciudades, rutas y buses (con la disposición de asientos), programa y cancela viajes, cambia la tarifa (queda una fila en `auditoria`), consulta las ventas del día, filtra facturas, reenvía el RIDE, descarga XML y RIDE, edita el emisor y administra noticias, anuncios e imágenes. Si un dato falta, el formulario lo dice en la página y no se queda callado.

## Pagos

`app/pagos.py` define `ProveedorPago`. Cada método (`tarjeta`, `transferencia`, `payphone`, `efectivo`) tiene un adaptador en `REGISTRO`. Hoy todos son `PasarelaSimulada`: aprueban el cobro y devuelven el proveedor `simulado:<metodo>`. Una pasarela real reemplaza esa clase y se registra con la misma clave, sin tocar la reserva ni el QR.

## Facturación electrónica

Al aprobar el pago se emite una factura en la misma transacción. El secuencial sale de la fila única de `emisor` con `SELECT … FOR UPDATE`, así dos compras no toman el mismo número de establecimiento y punto de emisión. El comprobante es el XML de factura versión 1.1.0. La clave de acceso tiene 49 dígitos y cierra con el dígito módulo 11. El transporte terrestre de pasajeros dentro del país va con IVA 0 %; la tarifa queda guardada en cada línea de `factura_detalles` y se cambia en Taquilla → Emisor. Si la tarifa no es cero, el IVA se descuenta del valor ya cobrado para que el total de la factura coincida con el pasaje.

La firma es XAdES-BES con el certificado `.p12` de `FIRMA_P12_RUTA` y `FIRMA_P12_CLAVE`. Si esas variables están vacías, el paso se omite y la factura queda marcada con `firma_omitida`. El envío al SRI (recepción y autorización) vive detrás de una interfaz. Con `SRI_MODO=offline`, el valor de desarrollo, no se llama a ningún web service y la factura pasa a `autorizada` con el número de autorización igual a la clave de acceso. `SRI_MODO=en_linea` usa los servicios de pruebas (`celcer`) o producción (`cel`) según el ambiente del emisor, o las URL de `SRI_RECEPCION_URL` y `SRI_AUTORIZACION_URL`.

El RIDE en PDF lleva el logo de La Maná, el código de barras de la clave, el comprador, la ruta, la salida, el asiento, el pasajero y los totales. Se muestra al terminar el pago, se descarga desde Mis facturas y desde taquilla, y se envía por correo. Sin `SMTP_HOST` el mensaje se escribe en el log del backend.

El emisor de prueba es ficticio: RUC `1790012344001`, establecimiento `001`, punto `001`, dirección Matriz, La Maná, Cotopaxi, ambiente de pruebas. No está inscrito en el SRI.

## Consulta de cédula y RUC

La cédula se valida con el módulo 10 y el RUC de persona natural, sociedad privada y sociedad pública con sus coeficientes. El pasaporte admite de 5 a 20 letras o números. El consumidor final usa exactamente `9999999999999`.

La razón social se busca en este orden:

1. La tabla `clientes_facturacion`, que guarda identificación, tipo, razón social, dirección, correo y teléfono de compras anteriores.
2. Un proveedor externo opcional, solo si existen `IDENTIFICACION_LOOKUP_URL` y, si el servicio lo pide, `IDENTIFICACION_LOOKUP_API_KEY`. La llamada es `GET` con `tipo` e `identificacion` y el encabezado `Authorization: Bearer …`. La respuesta tiene que ser JSON con `razon_social` y, si vienen, `direccion`, `email` y `telefono`.
3. Si no hay datos, la persona los escribe a mano.

Hay que contratar un servicio de consulta de cédula o RUC para tener nombres que no estén ya en `clientes_facturacion`. Este sistema no descarga ni interpreta páginas del SRI ni del Registro Civil. La fila de ejemplo `1710034065` / María Cedeño Paredes es semilla de demostración, no una consulta a un registro público.

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
| GET | `/viajes?origen&destino&fecha` | Salidas que todavía no han partido |
| GET | `/viajes/proximas?origen&destino&desde` | Próximas fechas con cupo en esa ruta |
| POST | `/admin/horarios/generar` | Completa 30 días desde la tabla `horarios`, sin duplicar |
| GET | `/viajes/{id}/asientos` | Mapa leído de `v_disponibilidad` |
| POST | `/boletos/reservar` | Reserva 10 minutos |
| POST | `/boletos/{codigo}/pagar` | `SELECT FOR UPDATE`, método de pago, referencia única, factura, QR |
| POST | `/boletos/{codigo}/cancelar` | Libera el asiento |
| GET | `/blog` y `/blog/{slug}` | Noticias y destinos publicados |
| GET | `/anuncios` | Promociones vigentes. `formato` es `texto` o `imagen` |
| GET | `/galeria` | Fotos públicas |
| POST / DELETE | `/admin/ciudades`, `/admin/rutas` | Alta y baja de ciudades y rutas |
| POST / PATCH / DELETE | `/admin/buses` | Crea el bus y sus asientos (4 por fila), cambia el estado o lo elimina si no tiene viajes |
| POST / DELETE | `/admin/viajes` | Crea un viaje. Eliminar lo cancela si no hay pasajes vigentes |
| PATCH | `/admin/rutas/{id}/tarifa` | Cambia la tarifa y audita |
| GET | `/admin/ventas?fecha` | Reporte diario |
| CRUD | `/admin/blog`, `/admin/anuncios`, `/admin/galeria` | Contenido. Anuncios y galería reciben `multipart` (JPG, PNG o WebP, hasta 5 MB). El anuncio de imagen guarda el archivo; el de texto guarda título y mensaje |
| GET | `/facturacion/consulta?tipo&identificacion` | Razón social local o del proveedor contratado |
| GET | `/facturacion/mias` | Facturas del cliente |
| GET | `/facturacion/{id}/ride` y `/xml` | RIDE y XML, del dueño o de taquilla |
| GET | `/admin/facturas` | Listado con estado, identificación y fechas |
| POST | `/admin/facturas/{id}/reenviar` | Reintenta firma y SRI si falta, y reenvía el correo |
| GET / PUT | `/admin/emisor` | RUC, establecimiento, punto, dirección, ambiente e IVA del pasaje |
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

Variables del backend: `DATABASE_URL`, `JWT_SECRET`, `JWT_ALGORITHM`, `ACCESS_TOKEN_MINUTOS`, `REFRESH_TOKEN_DIAS`, `CORS_ORIGINS`, `IDENTIFICACION_LOOKUP_URL`, `IDENTIFICACION_LOOKUP_API_KEY`, `FIRMA_P12_RUTA`, `FIRMA_P12_CLAVE`, `SRI_MODO` (`offline` o `en_linea`), `SRI_RECEPCION_URL`, `SRI_AUTORIZACION_URL`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USUARIO`, `SMTP_CLAVE`, `SMTP_DESDE`.
