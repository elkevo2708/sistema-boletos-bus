import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { solicitar } from '../api';
import MarcaPortal from '../componentes/MarcaPortal';
import { useAuth } from '../contexto/AuthContext';
import { Aviso, Boton, EstadoVacio } from '../ui/ui';

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
    return (
      <section className="portal-bloque">
        <p><Link to="/ingresar?siguiente=/conductor">Ingresa</Link> con la cuenta de conductor.</p>
      </section>
    );
  }
  if (usuario.rol !== 'conductor') {
    return <section className="portal-bloque"><Aviso>Esta vista es solo para conductores.</Aviso></section>;
  }

  return (
    <div className="conductor-marco">
      <header className="conductor-barra">
        <MarcaPortal />
        <span className="conductor-enlaces">
          <Link to="/">Inicio</Link>
          <Link to="/taxi">Ver el mapa</Link>
        </span>
      </header>
      <section className="conductor-pagina">
        <p className="sobrelinea">Conductor</p>
        <h1>{usuario.nombre}</h1>
        <p className="meta">{coords ? `${coords.lat.toFixed(5)}, ${coords.lng.toFixed(5)}` : 'Esperando GPS. Si falla, se usa el centro de La Maná.'}</p>
        <Boton tamano="lg" onClick={lineaToggle} aria-label={linea ? 'Salir de línea' : 'Ponerme en línea'}>
          {linea ? 'Salir de línea' : 'Ponerme en línea'}
        </Boton>
        {viaje && (
          <article className="panel-form">
            <h2>{viaje.estado.replaceAll('_', ' ')}</h2>
            <p>Pasajero {viaje.pasajero_nombre}. Destino: {viaje.destino?.texto || 'punto en el mapa'}.</p>
            <p>Tarifa de ejemplo ${Number(viaje.tarifa_estimada).toFixed(2)}</p>
            {viaje.estado === 'solicitado' && (
              <div className="dos">
                <Boton onClick={() => accion(`/taxi/conductor/viajes/${viaje.id}/aceptar`)}>Aceptar</Boton>
                <Boton variante="peligro" onClick={() => accion(`/taxi/conductor/viajes/${viaje.id}/rechazar`)}>Rechazar</Boton>
              </div>
            )}
            {viaje.estado === 'asignado' && <Boton onClick={() => accion(`/taxi/conductor/viajes/${viaje.id}/estado`, { estado: 'en_camino' })}>Voy en camino</Boton>}
            {viaje.estado === 'en_camino' && <Boton onClick={() => accion(`/taxi/conductor/viajes/${viaje.id}/estado`, { estado: 'a_bordo' })}>Pasajero a bordo</Boton>}
            {viaje.estado === 'a_bordo' && <Boton onClick={() => accion(`/taxi/conductor/viajes/${viaje.id}/estado`, { estado: 'finalizado' })}>Finalizar viaje</Boton>}
          </article>
        )}
        {!viaje && <EstadoVacio titulo="Sin solicitudes" texto="Cuando un pasajero te elija, el viaje aparece aquí." />}
        {aviso && <Aviso tono={aviso.includes('línea') ? 'ok' : 'error'}>{aviso}</Aviso>}
      </section>
    </div>
  );
}
