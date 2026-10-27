import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { solicitar } from '../api';
import { useAuth } from '../contexto/AuthContext';

const CENTRO = [-0.9406, -79.2344];

function icono(color) {
  return L.divIcon({
    className: 'pin-taxi',
    html: `<span style="background:${color}"></span>`,
    iconSize: [18, 18],
    iconAnchor: [9, 9],
  });
}

export default function Taxi() {
  const { token, usuario } = useAuth();
  const caja = useRef(null);
  const mapa = useRef(null);
  const marcas = useRef([]);
  const [origen, setOrigen] = useState({ lat: CENTRO[0], lng: CENTRO[1] });
  const [destino, setDestino] = useState(null);
  const [cercanos, setCercanos] = useState(null);
  const [cotizacion, setCotizacion] = useState(null);
  const [viaje, setViaje] = useState(null);
  const [aviso, setAviso] = useState('');
  const [consulta, setConsulta] = useState('');
  const [lugares, setLugares] = useState([]);
  const [metodo, setMetodo] = useState('efectivo');

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
    return undefined;
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
    solicitar(`/taxi/cercanos?lat=${origen.lat}&lng=${origen.lng}`, { token })
      .then(setCercanos)
      .catch((err) => setAviso(err.message));
    return undefined;
  }, [token, origen.lat, origen.lng]);

  useEffect(() => {
    if (!mapa.current) return;
    marcas.current.forEach((marca) => marca.remove());
    marcas.current = [];
    const origenMarca = L.marker([origen.lat, origen.lng], { icon: icono('#0c2f6b'), draggable: true }).addTo(mapa.current);
    origenMarca.on('dragend', () => {
      const punto = origenMarca.getLatLng();
      setOrigen({ lat: punto.lat, lng: punto.lng });
    });
    marcas.current.push(origenMarca);
    (cercanos?.taxis || []).forEach((taxi, indice) => {
      const marca = L.marker([taxi.lat, taxi.lng], { icon: icono(indice === 0 ? '#f2c200' : '#1497b8') }).addTo(mapa.current);
      marca.bindTooltip(`Unidad ${taxi.unidad} · ${taxi.distancia_km} km`);
      marcas.current.push(marca);
    });
    if (destino) {
      marcas.current.push(L.marker([destino.lat, destino.lng], { icon: icono('#2f9e3a') }).addTo(mapa.current));
    }
  }, [origen, cercanos, destino]);

  useEffect(() => {
    if (!token || !destino) return;
    const params = new URLSearchParams({
      origen_lat: origen.lat,
      origen_lng: origen.lng,
      destino_lat: destino.lat,
      destino_lng: destino.lng,
    });
    solicitar(`/taxi/cotizar?${params}`, { token }).then(setCotizacion).catch((err) => setAviso(err.message));
  }, [token, origen, destino]);

  useEffect(() => {
    if (!viaje?.id || !token || ['finalizado', 'cancelado'].includes(viaje.estado)) return undefined;
    const protocolo = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const socket = new WebSocket(`${protocolo}://${window.location.host}/ws/taxi/viajes/${viaje.id}?token=${encodeURIComponent(token)}`);
    socket.onmessage = (evento) => {
      const data = JSON.parse(evento.data);
      if (data.viaje) setViaje(data.viaje);
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
        <p className="sobrelinea">Taxi · La Maná</p>
        <h1>Pide un taxi</h1>
        {!usuario && (
          <p>Para ver unidades y pedir un viaje, <Link to="/ingresar?siguiente=/taxi">ingresa</Link>.</p>
        )}
        {usuario && (
          <>
            <button type="button" className="btn btn-portal" onClick={ubicar}>Usar mi ubicación</button>
            <p className="meta">Si el GPS no responde, arrastra el pin azul. El centro del mapa es la cabecera, cerca de -0.94, -79.23.</p>
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
            {cotizacion && (
              <p>
                Ruta {cotizacion.fuente === 'osrm' ? 'por calles' : 'estimada'}: {cotizacion.distancia_km} km · {cotizacion.duracion_min} min.
                Tarifa de ejemplo <strong>${Number(cotizacion.tarifa_estimada).toFixed(2)}</strong>. {cotizacion.aviso}
              </p>
            )}
            <label>Pago
              <select value={metodo} onChange={(e) => setMetodo(e.target.value)} aria-label="Método de pago del taxi">
                <option value="efectivo">Efectivo</option>
                <option value="deuna">DeUna! (prueba)</option>
                <option value="tarjeta">Tarjeta (prueba)</option>
                <option value="payphone">PayPhone (prueba)</option>
              </select>
            </label>
            <button type="button" className="btn btn-portal" disabled={!destino} onClick={pedir}>Solicitar taxi</button>
          </>
        )}
        {viaje && (
          <article>
            <h2>Viaje {viaje.estado.replace('_', ' ')}</h2>
            {viaje.conductor && <p>Unidad {viaje.conductor.unidad} · {viaje.conductor.nombre} · placa {viaje.conductor.placa}</p>}
            <p>Tarifa de ejemplo ${Number(viaje.tarifa_estimada).toFixed(2)} · pago {viaje.metodo_pago} ({viaje.pago_estado})</p>
            {viaje.estado === 'finalizado' && viaje.calificacion == null && (
              <button type="button" className="btn btn-portal" onClick={() => solicitar(`/taxi/viajes/${viaje.id}/calificar`, { method: 'POST', token, body: { estrellas: 5 } }).then(setViaje)}>
                Calificar con 5
              </button>
            )}
            {!['finalizado', 'cancelado', 'a_bordo'].includes(viaje.estado) && (
              <button type="button" onClick={() => solicitar(`/taxi/viajes/${viaje.id}/cancelar`, { method: 'POST', token }).then(setViaje)}>Cancelar</button>
            )}
          </article>
        )}
        {aviso && <p className="aviso" role="alert">{aviso}</p>}
      </aside>
    </section>
  );
}
