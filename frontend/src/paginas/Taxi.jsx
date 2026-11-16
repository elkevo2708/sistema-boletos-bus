import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { solicitar } from '../api';
import { useTextos } from '../textos';
import { useAuth } from '../contexto/AuthContext';
import { iconoPin, iconoTaxi, limpiarMarcas, ponerMarca, recordarRumbo } from '../ui/mapaTaxi';

const CENTRO = [-0.9406, -79.2344];

export default function Taxi() {
  const { token, usuario } = useAuth();
  const t = useTextos('taxi');
  const caja = useRef(null);
  const mapa = useRef(null);
  const marcas = useRef(new Map());
  const rumbos = useRef(new Map());
  const [origen, setOrigen] = useState({ lat: CENTRO[0], lng: CENTRO[1] });
  const [destino, setDestino] = useState(null);
  const [cercanos, setCercanos] = useState(null);
  const [cotizacion, setCotizacion] = useState(null);
  const [viaje, setViaje] = useState(null);
  const [aviso, setAviso] = useState('');
  const [consulta, setConsulta] = useState('');
  const [lugares, setLugares] = useState([]);
  const [frecuentes, setFrecuentes] = useState([]);
  const [historial, setHistorial] = useState([]);
  const [metodo, setMetodo] = useState('efectivo');
  const [servicio, setServicio] = useState('estandar');
  const [pasajeros, setPasajeros] = useState(1);
  const [nota, setNota] = useState('');
  const [estrellas, setEstrellas] = useState(5);
  const ruta = useRef(null);

  useEffect(() => {
    if (!caja.current || mapa.current) return undefined;
    const m = L.map(caja.current, { zoomControl: false }).setView(CENTRO, 15);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap',
      maxZoom: 19,
    }).addTo(m);
    m.on('click', (evento) => {
      setDestino({ lat: evento.latlng.lat, lng: evento.latlng.lng, texto: 'Punto elegido en el mapa' });
    });
    mapa.current = m;
    const ajustar = () => m.invalidateSize();
    window.addEventListener('resize', ajustar);
    setTimeout(ajustar, 200);
    return () => window.removeEventListener('resize', ajustar);
  }, []);

  useEffect(() => {
    if (!token) return undefined;
    const mover = () => solicitar('/taxi/demo/simular', { method: 'POST', token }).catch(() => {});
    mover();
    const reloj = setInterval(mover, 5000);
    return () => clearInterval(reloj);
  }, [token]);

  useEffect(() => {
    if (!token) return undefined;
    const leer = () => solicitar(`/taxi/cercanos?lat=${origen.lat}&lng=${origen.lng}`, { token })
      .then(setCercanos)
      .catch((err) => { if (err.status !== 429) setAviso(err.message); });
    leer();
    const reloj = setInterval(leer, 5000);
    return () => clearInterval(reloj);
  }, [token, origen.lat, origen.lng]);

  useEffect(() => {
    if (!mapa.current) return;
    const vistos = new Set(['origen']);
    const origenMarca = ponerMarca(L, mapa.current, marcas.current, 'origen', [origen.lat, origen.lng], iconoPin(L, 'origen'), { draggable: true });
    if (!origenMarca._lamana) {
      origenMarca._lamana = true;
      origenMarca.on('dragend', () => {
        const punto = origenMarca.getLatLng();
        setOrigen({ lat: punto.lat, lng: punto.lng });
      });
    }
    const asignado = viaje?.conductor?.id;
    (cercanos?.taxis || []).forEach((taxi) => {
      const clave = `taxi-${taxi.id}`;
      vistos.add(clave);
      const rumbo = recordarRumbo(rumbos.current, taxi.id, taxi, taxi.rumbo);
      const marca = ponerMarca(
        L, mapa.current, marcas.current, clave, [taxi.lat, taxi.lng],
        iconoTaxi(L, { estado: taxi.estado, rumbo, propio: asignado === taxi.id }),
      );
      marca.bindTooltip(`Unidad ${taxi.unidad} · ${taxi.distancia_km ?? ''} km`);
    });
    if (destino) {
      vistos.add('destino');
      ponerMarca(L, mapa.current, marcas.current, 'destino', [destino.lat, destino.lng], iconoPin(L, 'destino'));
    }
    limpiarMarcas(marcas.current, vistos);
  }, [origen, cercanos, destino, viaje]);

  useEffect(() => {
    if (!mapa.current) return;
    if (ruta.current) {
      mapa.current.removeLayer(ruta.current);
      ruta.current = null;
    }
    if (!cotizacion?.geometria) return;
    ruta.current = L.geoJSON(cotizacion.geometria, { style: { color: '#1f8a32', weight: 5, opacity: 0.9 } }).addTo(mapa.current);
  }, [cotizacion]);

  useEffect(() => {
    if (!token) return;
    solicitar('/taxi/lugares', { token }).then(setFrecuentes).catch(() => {});
    solicitar('/taxi/mis-viajes', { token }).then(setHistorial).catch(() => {});
  }, [token, viaje?.estado]);

  useEffect(() => {
    if (!token || !destino) return;
    const params = new URLSearchParams({
      origen_lat: origen.lat,
      origen_lng: origen.lng,
      destino_lat: destino.lat,
      destino_lng: destino.lng,
      servicio,
    });
    solicitar(`/taxi/cotizar?${params}`, { token }).then(setCotizacion).catch((err) => setAviso(err.message));
  }, [token, origen, destino, servicio]);

  useEffect(() => {
    if (!viaje?.id || !token || ['finalizado', 'cancelado'].includes(viaje.estado)) return undefined;
    const protocolo = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const socket = new WebSocket(`${protocolo}://${window.location.host}/ws/taxi/viajes/${viaje.id}?token=${encodeURIComponent(token)}`);
    socket.onmessage = (evento) => {
      const data = JSON.parse(evento.data);
      if (data.viaje) setViaje((previo) => ({ ...data.viaje, codigo: data.viaje.codigo || previo?.codigo }));
    };
    const reloj = setInterval(() => {
      solicitar(`/taxi/viajes/${viaje.id}`, { token }).then(setViaje).catch(() => {});
    }, 4000);
    return () => {
      clearInterval(reloj);
      socket.close();
    };
  }, [viaje?.id, viaje?.estado, token]);

  function ubicar() {
    if (!navigator.geolocation) {
      setAviso('Este navegador no entrega la ubicación. Mueve el pin azul.');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const punto = { lat: pos.coords.latitude, lng: pos.coords.longitude };
        setOrigen(punto);
        mapa.current?.setView([punto.lat, punto.lng], 16);
      },
      () => setAviso('No se pudo leer el GPS. Mueve el pin azul.'),
      { enableHighAccuracy: true, timeout: 8000 },
    );
  }

  async function buscarLugar(event) {
    event.preventDefault();
    if (!token) return;
    try {
      setLugares(await solicitar(`/taxi/geocodificar?q=${encodeURIComponent(consulta)}`, { token }));
    } catch (err) {
      setAviso(err.message);
    }
  }

  async function pedir() {
    setAviso('');
    try {
      const creado = await solicitar('/taxi/viajes', {
        method: 'POST',
        token,
        body: {
          origen_lat: origen.lat,
          origen_lng: origen.lng,
          destino_lat: destino.lat,
          destino_lng: destino.lng,
          destino_texto: destino.texto,
          metodo_pago: metodo,
          servicio,
          pasajeros: Number(pasajeros),
          nota,
        },
      });
      setViaje(creado);
    } catch (err) {
      setAviso(err.message);
    }
  }

  const cercano = cercanos?.mas_cercano;

  return (
    <section className="taxi-pagina">
      <div ref={caja} className="taxi-mapa" role="application" aria-label="Mapa de taxis en La Maná" />
      <aside className="taxi-panel">
        <span className="taxi-asa" aria-hidden="true" />
        <p className="sobrelinea">{t('taxi.kicker', 'Taxi · La Maná')}</p>
        <h1>{viaje ? ({
          solicitado: 'Buscando conductor',
          asignado: 'Conductor asignado',
          en_camino: 'El conductor va hacia ti',
          llego: 'El conductor llegó',
          a_bordo: 'En viaje',
          finalizado: 'Viaje finalizado',
          cancelado: 'Viaje cancelado',
        }[viaje.estado] || 'Pide un taxi') : t('taxi.titulo', 'Pide un taxi')}</h1>
        {viaje && (
          <article className="taxi-estado">
            {viaje.codigo && <p className="taxi-codigo">Código para el conductor: <strong>{viaje.codigo}</strong></p>}
            {viaje.conductor && (
              <p>
                {viaje.conductor.nombre} · unidad {viaje.conductor.unidad} · placa {viaje.conductor.placa}
                {viaje.conductor.telefono && (
                  <>
                    {' '}<a href={`tel:${viaje.conductor.telefono}`}>Llamar</a>
                    {' '}<a href={`https://wa.me/${viaje.conductor.telefono.replace(/\D/g, '')}`} target="_blank" rel="noreferrer">WhatsApp</a>
                  </>
                )}
              </p>
            )}
            <p>Tarifa de ejemplo ${Number(viaje.tarifa_estimada).toFixed(2)} · pago {viaje.metodo_pago}</p>
            {viaje.seguimiento && (
              <p className="meta">Seguimiento: {window.location.origin}/taxi?seguimiento={viaje.seguimiento}</p>
            )}
            {viaje.estado === 'finalizado' && viaje.calificacion == null && (
              <div className="opciones-tarjeta" role="radiogroup" aria-label="Calificación">
                {[1, 2, 3, 4, 5].map((n) => (
                  <button key={n} type="button" className={estrellas === n ? 'activo' : ''} onClick={() => setEstrellas(n)}>{n}</button>
                ))}
                <button type="button" className="btn btn-portal" onClick={() => solicitar(`/taxi/viajes/${viaje.id}/calificar`, { method: 'POST', token, body: { estrellas } }).then(setViaje)}>
                  Enviar calificación
                </button>
              </div>
            )}
            {!['finalizado', 'cancelado', 'a_bordo'].includes(viaje.estado) && (
              <button type="button" className="btn btn-fantasma" onClick={() => solicitar(`/taxi/viajes/${viaje.id}/cancelar`, { method: 'POST', token }).then(setViaje)}>Cancelar</button>
            )}
            <button type="button" className="btn btn-fantasma" onClick={() => solicitar('/taxi/sos', { method: 'POST', token, body: { lat: origen.lat, lng: origen.lng, viaje_id: viaje.id } }).then((alerta) => setAviso(`Emergencia ${alerta.emergencia}. Ubicación compartida.`)).catch((err) => setAviso(err.message))}>
              SOS · 911
            </button>
          </article>
        )}
        {!usuario && (
          <p>Para ver unidades y pedir un viaje, <Link to="/ingresar?siguiente=/taxi">ingresa</Link>.</p>
        )}
        {usuario && !viaje && (
          <>
            <button type="button" className="btn btn-portal" onClick={ubicar}>Usar mi ubicación</button>
            <p className="meta">{t('taxi.ayuda', 'Si el GPS no responde, arrastra el pin azul. El centro del mapa es la cabecera, cerca de -0.94, -79.23.')}</p>
            {cercano ? (
              <p className="taxi-cerca">
                Más cercano: unidad <strong>{cercano.unidad}</strong>, placa {cercano.placa}, a {cercano.distancia_km} km · unos {cercano.eta_min} min.
              </p>
            ) : <p>Buscando taxis de ejemplo cerca del pin.</p>}
            <form onSubmit={buscarLugar} className="portal-buscar portal-buscar-pagina">
              <input value={consulta} onChange={(e) => setConsulta(e.target.value)} placeholder="Destino o lugar del portal" aria-label="Buscar destino" />
              <button type="submit" className="btn btn-portal">Buscar</button>
            </form>
            <ul className="lista-admin">
              {lugares.map((lugar) => (
                <li key={`${lugar.lat}-${lugar.nombre}`}>
                  <button type="button" onClick={() => setDestino({ lat: lugar.lat, lng: lugar.lng, texto: lugar.nombre })}>
                    {lugar.nombre}
                  </button>
                </li>
              ))}
            </ul>
            {frecuentes.length > 0 && (
              <div className="opciones-tarjeta" aria-label="Lugares frecuentes">
                {frecuentes.map((lugar) => (
                  <button key={lugar.id} type="button" onClick={() => setDestino({ lat: lugar.lat, lng: lugar.lng, texto: lugar.nombre })}>
                    {lugar.nombre}
                  </button>
                ))}
              </div>
            )}
            <div className="opciones-tarjeta" role="radiogroup" aria-label="Tipo de servicio">
              {[['estandar', 'Estándar'], ['camioneta', 'Camioneta']].map(([valor, etiqueta]) => (
                <button key={valor} type="button" role="radio" aria-checked={servicio === valor} className={servicio === valor ? 'activo' : ''} onClick={() => setServicio(valor)}>
                  {etiqueta}
                </button>
              ))}
            </div>
            <label>Pasajeros
              <input type="number" min="1" max="6" value={pasajeros} onChange={(e) => setPasajeros(e.target.value)} aria-label="Número de pasajeros" />
            </label>
            <label>Nota para el conductor
              <input value={nota} onChange={(e) => setNota(e.target.value)} maxLength={180} aria-label="Nota para el conductor" />
            </label>
            {cotizacion && (
              <p>
                Ruta {cotizacion.fuente === 'osrm' ? 'por calles' : 'estimada'}: {cotizacion.distancia_km} km · {cotizacion.duracion_min} min.
                Tarifa de ejemplo <strong>${Number(cotizacion.tarifa_estimada).toFixed(2)}</strong>
                {cotizacion.nocturno ? ` · recargo nocturno ${cotizacion.desglose?.recargo_nocturno_pct}%` : ''}.
                {' '}Arranque ${Number(cotizacion.desglose?.arranque || 0).toFixed(2)}, km ${Number(cotizacion.desglose?.por_km || 0).toFixed(2)}, minutos ${Number(cotizacion.desglose?.por_minuto || 0).toFixed(2)}. {cotizacion.aviso}
              </p>
            )}
            <div className="opciones-tarjeta" role="radiogroup" aria-label="Método de pago del taxi">
              {[
                ['efectivo', 'Efectivo'],
                ['deuna', 'DeUna!'],
                ['tarjeta', 'Tarjeta'],
                ['payphone', 'PayPhone'],
              ].map(([valor, etiqueta]) => (
                <button
                  key={valor}
                  type="button"
                  role="radio"
                  aria-checked={metodo === valor}
                  className={metodo === valor ? 'activo' : ''}
                  onClick={() => setMetodo(valor)}
                >
                  {etiqueta}
                </button>
              ))}
            </div>
            <button type="button" className="btn btn-portal" disabled={!destino} onClick={pedir}>Solicitar taxi</button>
          </>
        )}
        {historial.length > 0 && (
          <details>
            <summary>Mis viajes</summary>
            <ul className="lista-admin">
              {historial.map((item) => (
                <li key={item.id}>{item.destino_texto || 'Viaje'} · {item.estado} · ${Number(item.tarifa_final ?? item.tarifa_estimada).toFixed(2)}</li>
              ))}
            </ul>
          </details>
        )}
        {aviso && <p className="aviso" role="alert">{aviso}</p>}
      </aside>
    </section>
  );
}
