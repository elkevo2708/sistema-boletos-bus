import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { solicitar } from '../api';
import { fechaBogota, formatearFechaHora, formatearPesos } from '../formato';

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
        const bogota = lista.find((ciudad) => ciudad.nombre === 'Bogotá');
        const medellin = lista.find((ciudad) => ciudad.nombre === 'Medellín');
        if (bogota && medellin) {
          setOrigen(String(bogota.id));
          setDestino(String(medellin.id));
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
    <div className="pagina">
      <section className="hero">
        <p className="sobrelinea">Cordillera, valle y costa</p>
        <h1>Cruza el país con el asiento ya elegido.</h1>
        <p className="lead">
          Consulta la salida, mira el mapa del bus y reserva durante diez minutos
          mientras confirmas el pago.
        </p>
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
                <p className="precio">{formatearPesos(viaje.precio)}</p>
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
    </div>
  );
}
