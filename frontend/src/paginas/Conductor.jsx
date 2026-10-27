import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { solicitar } from '../api';
import { useAuth } from '../contexto/AuthContext';

export default function Conductor() {
  const { token, usuario } = useAuth();
  const [viaje, setViaje] = useState(null);
  const [linea, setLinea] = useState(false);
  const [aviso, setAviso] = useState('');
  const [coords, setCoords] = useState(null);

  useEffect(() => {
    if (!token || usuario?.rol !== 'conductor') return undefined;
    const vigilar = navigator.geolocation?.watchPosition(
      (pos) => setCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      () => setCoords({ lat: -0.9406, lng: -79.2344 }),
      { enableHighAccuracy: true, maximumAge: 4000 },
    );
    return () => {
      if (vigilar != null) navigator.geolocation.clearWatch(vigilar);
    };
  }, [token, usuario]);

  useEffect(() => {
    if (!token || !coords || usuario?.rol !== 'conductor') return undefined;
    const enviar = () => solicitar('/taxi/conductor/ubicacion', { method: 'POST', token, body: coords }).catch((err) => {
      if (err.status !== 429) setAviso(err.message);
    });
    enviar();
    const reloj = setInterval(enviar, 4000);
    return () => clearInterval(reloj);
  }, [token, coords, usuario]);

  useEffect(() => {
    if (!token || usuario?.rol !== 'conductor') return undefined;
    const leer = () => solicitar('/taxi/conductor/viaje', { token }).then(setViaje).catch(() => {});
    leer();
    const reloj = setInterval(leer, 3000);
    return () => clearInterval(reloj);
  }, [token, usuario]);

  async function lineaToggle() {
    try {
      const respuesta = await solicitar('/taxi/conductor/estado', { method: 'POST', token, body: { en_linea: !linea } });
      setLinea(respuesta.estado === 'disponible');
      setAviso(respuesta.estado === 'disponible' ? 'Estás en línea.' : 'Quedaste fuera de línea.');
    } catch (err) {
      setAviso(err.message);
    }
  }

  async function accion(ruta, cuerpo) {
    try {
      setViaje(await solicitar(ruta, { method: 'POST', token, body: cuerpo }));
      setAviso('');
    } catch (err) {
      setAviso(err.message);
    }
  }

  if (!usuario) {
    return <section className="portal-bloque"><p><Link to="/ingresar?siguiente=/conductor">Ingresa</Link> con la cuenta de conductor.</p></section>;
  }
  if (usuario.rol !== 'conductor') {
    return <section className="portal-bloque"><p className="aviso">Esta vista es solo para conductores.</p></section>;
  }

  return (
    <section className="conductor-pagina">
      <p className="sobrelinea">Conductor</p>
      <h1>{usuario.nombre}</h1>
      <p className="meta">{coords ? `${coords.lat.toFixed(5)}, ${coords.lng.toFixed(5)}` : 'Esperando GPS. Si falla, se usa el centro de La Maná.'}</p>
      <button type="button" className="btn btn-portal btn-grande" onClick={lineaToggle} aria-label={linea ? 'Salir de línea' : 'Ponerme en línea'}>
        {linea ? 'Salir de línea' : 'Ponerme en línea'}
      </button>
      {viaje && (
        <article className="panel-form">
          <h2>{viaje.estado.replaceAll('_', ' ')}</h2>
          <p>Pasajero {viaje.pasajero_nombre}. Destino: {viaje.destino?.texto || 'punto en el mapa'}.</p>
          <p>Tarifa de ejemplo ${Number(viaje.tarifa_estimada).toFixed(2)}</p>
          {viaje.estado === 'solicitado' && (
            <div className="dos">
              <button type="button" className="btn btn-portal" onClick={() => accion(`/taxi/conductor/viajes/${viaje.id}/aceptar`)}>Aceptar</button>
              <button type="button" onClick={() => accion(`/taxi/conductor/viajes/${viaje.id}/rechazar`)}>Rechazar</button>
            </div>
          )}
          {viaje.estado === 'asignado' && <button type="button" className="btn btn-portal" onClick={() => accion(`/taxi/conductor/viajes/${viaje.id}/estado`, { estado: 'en_camino' })}>Voy en camino</button>}
          {viaje.estado === 'en_camino' && <button type="button" className="btn btn-portal" onClick={() => accion(`/taxi/conductor/viajes/${viaje.id}/estado`, { estado: 'a_bordo' })}>Pasajero a bordo</button>}
          {viaje.estado === 'a_bordo' && <button type="button" className="btn btn-portal" onClick={() => accion(`/taxi/conductor/viajes/${viaje.id}/estado`, { estado: 'finalizado' })}>Finalizar viaje</button>}
        </article>
      )}
      {!viaje && <p>No hay una solicitud para ti.</p>}
      {aviso && <p className="aviso" role="alert">{aviso}</p>}
    </section>
  );
}
