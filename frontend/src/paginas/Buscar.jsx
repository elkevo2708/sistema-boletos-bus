import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { solicitar } from '../api';
import { fechaBogota, formatearFechaHora, formatearDinero } from '../formato';

export default function Buscar() {
  const [ciudades, setCiudades] = useState([]);
  const [origen, setOrigen] = useState('');
  const [destino, setDestino] = useState('');
  const [fecha, setFecha] = useState(fechaBogota(1));
  const [viajes, setViajes] = useState(null);
  const [error, setError] = useState('');
  const [cargando, setCargando] = useState(false);
  const [auto, setAuto] = useState(true);

  useEffect(() => {
    solicitar('/ciudades')
      .then((lista) => {
        setCiudades(lista);
        const origenBase = lista.find((ciudad) => ciudad.nombre === 'La Maná');
        const destinoBase = lista.find((ciudad) => ciudad.nombre === 'Quevedo');
        if (origenBase && destinoBase) {
          setOrigen(String(origenBase.id));
          setDestino(String(destinoBase.id));
        } else if (lista.length > 1) {
          setOrigen(String(lista[0].id));
          setDestino(String(lista[1].id));
        }
      })
      .catch((err) => setError(err.message));
  }, []);

  async function buscar(event, valores) {
    event?.preventDefault();
    const o = valores?.origen ?? origen;
    const d = valores?.destino ?? destino;
    const f = valores?.fecha ?? fecha;
    if (!o || !d || !f) return;
    if (o === d) {
      setError('Elige un destino distinto al origen.');
      setViajes([]);
      return;
    }
    setCargando(true);
    setError('');
    try {
      const data = await solicitar(`/viajes?origen=${o}&destino=${d}&fecha=${f}`);
      setViajes(data);
    } catch (err) {
      setViajes([]);
      setError(err.message);
    } finally {
      setCargando(false);
    }
  }

  useEffect(() => {
    if (!auto || !origen || !destino) return;
    setAuto(false);
    buscar(null, { origen, destino, fecha });
  }, [auto, origen, destino, fecha]);

  const nombre = (id) => ciudades.find((ciudad) => String(ciudad.id) === String(id));

  return (
    <div>
      <section className="hero" style={{ backgroundImage: 'linear-gradient(90deg, rgba(15,28,24,.82), rgba(15,28,24,.28)), url(/medios/hero-ruta.jpg)' }}>
        <div className="hero-texto">
          <p className="sobrelinea">Cotopaxi · Los Ríos · Sierra y costa</p>
          <h1>De La Maná al país, con el asiento ya elegido.</h1>
          <p className="lead">
            Salidas diarias a Quevedo, Latacunga, Quito, Ambato y Guayaquil.
            Reserve diez minutos y pague con tarjeta, transferencia, PayPhone o en ventanilla.
          </p>
        </div>
      </section>

      <form className="panel-busqueda" onSubmit={buscar}>
        <label>
          Origen
          <select value={origen} onChange={(e) => setOrigen(e.target.value)} required aria-label="Ciudad de origen">
            <option value="">Selecciona</option>
            {ciudades.map((ciudad) => (
              <option key={ciudad.id} value={ciudad.id}>
                {ciudad.nombre} · {ciudad.departamento}
              </option>
            ))}
          </select>
        </label>
        <label>
          Destino
          <select value={destino} onChange={(e) => setDestino(e.target.value)} required aria-label="Ciudad de destino">
            <option value="">Selecciona</option>
            {ciudades.map((ciudad) => (
              <option key={ciudad.id} value={ciudad.id} disabled={String(ciudad.id) === origen}>
                {ciudad.nombre} · {ciudad.departamento}
              </option>
            ))}
          </select>
        </label>
        <label>
          Fecha
          <input
            type="date"
            value={fecha}
            min={fechaBogota(0)}
            onChange={(e) => setFecha(e.target.value)}
            required
            aria-label="Fecha de salida"
          />
        </label>
        <button type="submit" className="btn btn-arcilla" aria-label="Buscar viajes" disabled={cargando}>
          {cargando ? 'Buscando…' : 'Buscar viajes'}
        </button>
      </form>

      {error && <p className="aviso" role="alert">{error}</p>}

      <section className="resultados" aria-live="polite">
        {viajes && (
          <h2>
            {viajes.length
              ? `${viajes.length} salida${viajes.length === 1 ? '' : 's'} · ${nombre(origen)?.nombre ?? ''} → ${nombre(destino)?.nombre ?? ''}`
              : 'No hay salidas para esa ruta y fecha'}
          </h2>
        )}
        <div className="lista-viajes">
          {viajes?.map((viaje) => (
            <article className="tiquete" key={viaje.id}>
              <div>
                <p className="ruta">{viaje.origen} → {viaje.destino}</p>
                <p className="horas">
                  <time dateTime={viaje.salida}>{formatearFechaHora(viaje.salida)}</time>
                  <span aria-hidden="true"> → </span>
                  <time dateTime={viaje.llegada_est}>{formatearFechaHora(viaje.llegada_est)}</time>
                </p>
                <p className="meta">Disco {viaje.numero_disco} · placa {viaje.placa} · {viaje.pisos === 2 ? 'dos pisos' : 'un piso'}</p>
              </div>
              <div className="tiquete-lado">
                <p className="precio">{formatearDinero(viaje.precio)}</p>
                <p className={viaje.asientos_libres > 0 ? 'libres' : 'agotado'}>
                  {viaje.asientos_libres} libres de {viaje.capacidad}
                </p>
                <Link
                  className="btn btn-pino"
                  to={`/viajes/${viaje.id}`}
                  aria-label={`Elegir asientos del viaje de ${viaje.origen} a ${viaje.destino} a las ${formatearFechaHora(viaje.salida)}`}
                >
                  Elegir asientos
                </Link>
              </div>
            </article>
          ))}
        </div>
      </section>
      <Destacados />
    </div>
  );
}

function Destacados() {
  const [notas, setNotas] = useState([]);
  const [fotos, setFotos] = useState([]);

  useEffect(() => {
    solicitar('/blog').then((data) => setNotas(data.slice(0, 3))).catch(() => {});
    solicitar('/galeria').then((data) => setFotos(data.slice(0, 4))).catch(() => {});
  }, []);

  if (!notas.length && !fotos.length) return null;

  return (
    <div className="pagina destacados">
      {notas.length > 0 && (
        <section>
          <div className="seccion-cabeza">
            <h2>De la cooperativa</h2>
            <Link to="/noticias">Todas las noticias</Link>
          </div>
          <div className="rejilla-notas">
            {notas.map((nota) => (
              <article className="nota" key={nota.id}>
                {nota.imagen && <img src={nota.imagen} alt="" />}
                <p className="sobrelinea">{nota.categoria}</p>
                <h3><Link to={`/noticias/${nota.slug}`}>{nota.titulo}</Link></h3>
                <p>{nota.resumen}</p>
              </article>
            ))}
          </div>
        </section>
      )}
      {fotos.length > 0 && (
        <section>
          <div className="seccion-cabeza">
            <h2>La ruta en imágenes</h2>
            <Link to="/galeria">Abrir la galería</Link>
          </div>
          <div className="tira-fotos">
            {fotos.map((foto) => (
              <Link key={foto.id} to="/galeria" aria-label={foto.titulo}>
                <img src={foto.url} alt={foto.titulo} />
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
