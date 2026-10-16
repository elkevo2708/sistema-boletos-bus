import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { solicitar } from '../api';
import { fechaBogota, formatearFechaHora, formatearDinero } from '../formato';

const RUTAS = [
  ['La Maná', 'Quevedo', 'Unos 75 minutos por la vía plana hacia Los Ríos.'],
  ['La Maná', 'Latacunga', 'Subida a la sierra, con el valle de Cotopaxi al final.'],
  ['Quevedo', 'Guayaquil', 'Conexión desde la llanura hasta el puerto.'],
  ['Latacunga', 'Quito', 'Del valle interandino a la llegada en Quitumbe.'],
];

const DESTINOS = [
  ['Quevedo', 'destino-quevedo.jpg', '/noticias/quevedo-rio-y-mercado', 'Río, mercado y la salida más corta de la cooperativa.'],
  ['Latacunga', 'destino-latacunga.jpg', '/noticias/latacunga-y-la-sierra', 'Dos horas de subida y el frío claro de la sierra.'],
  ['Guayaquil', 'destino-guayaquil.jpg', '/galeria', 'Se llega desde Quevedo, el mismo día, en la unidad de la costa.'],
  ['Quito', 'terminal-quito.jpg', '/noticias/salida-extra-quito-en-feriado', 'Turno de madrugada hasta Quitumbe cuando el feriado lo pide.'],
];

const SERVICIOS = [
  ['Asiento numerado', 'Elige el puesto en el mapa antes de pagar. Nadie más puede tomarlo mientras la reserva esté vigente.'],
  ['Pasaje en línea', 'Origen, destino y fecha. La reserva dura diez minutos y el QR queda listo al confirmar.'],
  ['Cuatro formas de pago', 'Tarjeta, transferencia, PayPhone o efectivo en la ventanilla del terminal de La Maná.'],
  ['Equipaje de bodega', 'Etiquétalo con tu nombre y el número de asiento. En el bus de dos pisos el pasillo va despejado.'],
  ['Taquilla de madrugada', 'El andén abre a las 05:00. Llega veinte minutos antes: el abordaje cierra cuando el disco enciende luces.'],
  ['Horario de Ecuador', 'Todas las salidas se publican en hora local, sin conversión. La taquilla cierra a las 21:00.'],
];

export default function Buscar() {
  const [ciudades, setCiudades] = useState([]);
  const [origen, setOrigen] = useState('');
  const [destino, setDestino] = useState('');
  const [fecha, setFecha] = useState(fechaBogota(1));
  const [viajes, setViajes] = useState(null);
  const [error, setError] = useState('');
  const [cargando, setCargando] = useState(false);
  const [auto, setAuto] = useState(true);
  const [anuncios, setAnuncios] = useState([]);
  const [faq, setFaq] = useState(0);

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
    solicitar('/anuncios').then(setAnuncios).catch(() => {});
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

  function intercambiar() {
    setOrigen(destino);
    setDestino(origen);
  }

  function elegirRuta(origenNombre, destinoNombre) {
    const o = ciudades.find((ciudad) => ciudad.nombre === origenNombre);
    const d = ciudades.find((ciudad) => ciudad.nombre === destinoNombre);
    if (!o || !d) return;
    setOrigen(String(o.id));
    setDestino(String(d.id));
    buscar(null, { origen: String(o.id), destino: String(d.id), fecha });
    document.getElementById('rutas')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  const nombre = (id) => ciudades.find((ciudad) => String(ciudad.id) === String(id));

  return (
    <div>
      <section className="hero">
        <div className="hero-texto">
          <p className="sobrelinea">Cotopaxi · Los Ríos · Sierra y costa</p>
          <h1>Viaja desde La Maná con el asiento ya elegido.</h1>
          <p className="lead">Salidas a Quevedo, Latacunga, Quito, Ambato y Guayaquil. Reserva en línea y aborda con tu código QR.</p>
        </div>
        <form id="buscar" className="panel-busqueda" onSubmit={buscar}>
          <label>
            Origen
            <select value={origen} onChange={(e) => setOrigen(e.target.value)} required aria-label="Ciudad de origen">
              <option value="">Selecciona</option>
              {ciudades.map((ciudad) => (
                <option key={ciudad.id} value={ciudad.id}>{ciudad.nombre} · {ciudad.departamento}</option>
              ))}
            </select>
          </label>
          <button type="button" className="intercambio" onClick={intercambiar} aria-label="Intercambiar origen y destino">⇄</button>
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
            <input type="date" value={fecha} min={fechaBogota(0)} onChange={(e) => setFecha(e.target.value)} required aria-label="Fecha de salida" />
          </label>
          <button type="submit" className="btn btn-arcilla" aria-label="Buscar viajes" disabled={cargando}>
            {cargando ? 'Buscando…' : 'Buscar pasajes'}
          </button>
        </form>
        {error && <p className="aviso aviso-hero" role="alert">{error}</p>}
      </section>

      <section className="cifras" aria-label="La cooperativa en cifras">
        <article><strong>7</strong><span>Ciudades en la red</span></article>
        <article><strong>2</strong><span>Discos en servicio</span></article>
        <article><strong>40</strong><span>Puestos por unidad</span></article>
        <article><strong>10</strong><span>Minutos de reserva</span></article>
      </section>

      <section className="franja-clara">
        <div className="pagina empresa">
          <div>
            <p className="sobrelinea">La cooperativa</p>
            <h2>Del subtrópico de Cotopaxi a la costa y a la sierra.</h2>
            <p>
              Salimos de la matriz en La Maná. Un disco baja a Quevedo y sigue a Guayaquil.
              El otro sube a Latacunga, Santo Domingo, Ambato y Quito. El pasaje se cobra por asiento y el QR es el boleto.
            </p>
            <Link className="btn btn-arcilla" to="/galeria">Ver la flota</Link>
          </div>
          <img src="/bus-lamana.jpg" alt="Unidad naranja y negra de Trans La Maná" />
        </div>
      </section>

      <section className="pagina" id="encomiendas">
        <div className="encomiendas">
          <img src="/encomiendas-lamana.png" alt="Afiche de encomiendas de Trans La Maná" />
          <div>
            <p className="sobrelinea">Encomiendas</p>
            <h2>Paquetes entre la costa y la sierra.</h2>
            <p>
              La cobertura del afiche llega a La Maná, Quevedo, Quinsaloma, Moraspungo,
              Latacunga, Ambato, Quito, Guayaquil, Durán y Empalme.
            </p>
            <Link className="btn btn-pino" to="/encomiendas">Ver cobertura y teléfonos</Link>
          </div>
        </div>
      </section>

      <section className="pagina" id="servicios">
        <div className="seccion-cabeza">
          <div>
            <p className="sobrelinea">Servicios</p>
            <h2>Lo que incluye el pasaje.</h2>
          </div>
        </div>
        <div className="rejilla-servicios">
          {SERVICIOS.map(([titulo, texto]) => (
            <article className="servicio" key={titulo}>
              <h3>{titulo}</h3>
              <p>{texto}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="franja-clara" id="destinos">
        <div className="pagina">
          <div className="seccion-cabeza">
            <div>
              <p className="sobrelinea">Destinos</p>
              <h2>A dónde sale el disco.</h2>
            </div>
            <Link to="/noticias">Leer las crónicas</Link>
          </div>
          <div className="rejilla-destinos">
            {DESTINOS.map(([ciudad, foto, enlace, texto]) => (
              <article className="destino" key={ciudad}>
                <img src={`/medios/${foto}`} alt="" />
                <div>
                  <h3>{ciudad}</h3>
                  <p>{texto}</p>
                  <Link to={enlace}>Conocer {ciudad}</Link>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      {anuncios.length > 0 && (
        <section className="pagina" id="promos">
          <div className="seccion-cabeza">
            <div>
              <p className="sobrelinea">Promociones</p>
              <h2>Vigentes esta temporada.</h2>
            </div>
          </div>
          <div className="rejilla-promos">
            {anuncios.map((anuncio) => (
              <article className="promo" key={anuncio.id}>
                <p className="sobrelinea">{anuncio.tipo === 'modal' ? 'Aviso' : 'Tarifa'}</p>
                <h3>{anuncio.titulo}</h3>
                <p>{anuncio.mensaje}</p>
                {anuncio.enlace?.startsWith('/') && <Link to={anuncio.enlace}>Ver detalle</Link>}
              </article>
            ))}
          </div>
        </section>
      )}

      <section className="pagina resultados" id="rutas" aria-live="polite">
        <div className="seccion-cabeza">
          <div>
            <p className="sobrelinea">Horarios</p>
            <h2>
              {viajes?.length
                ? `${viajes.length} salida${viajes.length === 1 ? '' : 's'} · ${nombre(origen)?.nombre ?? ''} → ${nombre(destino)?.nombre ?? ''}`
                : 'Salidas del día'}
            </h2>
          </div>
        </div>
        <div className="atajos-ruta">
          {RUTAS.map(([desde, hasta, texto]) => (
            <button type="button" key={`${desde}-${hasta}`} onClick={() => elegirRuta(desde, hasta)} aria-label={`Buscar ${desde} a ${hasta}`}>
              <strong>{desde} → {hasta}</strong>
              <span>{texto}</span>
            </button>
          ))}
        </div>
        {viajes && viajes.length === 0 && <p>No hay salidas para esa ruta y fecha. Prueba otro día o una de las rutas de arriba.</p>}
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
                  className="btn btn-arcilla"
                  to={`/viajes/${viaje.id}`}
                  aria-label={`Elegir asientos del viaje de ${viaje.origen} a ${viaje.destino} a las ${formatearFechaHora(viaje.salida)}`}
                >
                  Elegir asiento
                </Link>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="pasos">
        <div className="pagina">
          <p className="sobrelinea">Boleto en línea</p>
          <h2>Cómo comprar el pasaje.</h2>
          <ol>
            <li><strong>1</strong><span>Elige origen, destino y fecha.</span></li>
            <li><strong>2</strong><span>Marca el asiento en el mapa del bus.</span></li>
            <li><strong>3</strong><span>Paga con tarjeta, transferencia, PayPhone o en ventanilla.</span></li>
            <li><strong>4</strong><span>Descarga el QR y preséntalo al abordar.</span></li>
          </ol>
        </div>
      </section>

      <section className="pagina">
        <div className="seccion-cabeza">
          <div>
            <p className="sobrelinea">Flota</p>
            <h2>Unidades de la cooperativa.</h2>
          </div>
          <Link to="/galeria">Abrir la galería</Link>
        </div>
        <div className="rejilla-flota">
          <figure>
            <img src="/bus-lamana.jpg" alt="Unidad naranja y negra de Trans La Maná" />
            <figcaption>Librea de la cooperativa</figcaption>
          </figure>
          <figure>
            <img src="/medios/bus-interior.jpg" alt="Butacas y pasillo central de la unidad" />
            <figcaption>Butacas con pasillo central</figcaption>
          </figure>
          <figure>
            <img src="/medios/bus-dos-pisos.jpg" alt="Unidad de dos pisos hacia la sierra" />
            <figcaption>Dos pisos · sierra y Guayaquil</figcaption>
          </figure>
        </div>
      </section>

      <section className="franja-clara">
        <div className="pagina faq">
          <div>
            <p className="sobrelinea">Preguntas</p>
            <h2>Antes de viajar.</h2>
          </div>
          {[
            ['¿Cómo puedo pagar?', 'En línea aceptamos tarjeta de crédito o débito, transferencia al Banco del Pacífico y PayPhone. También puedes dejar el pago en efectivo en la ventanilla del terminal de La Maná, con el QR de la reserva.'],
            ['¿Cómo recibo el boleto?', 'Al confirmar el pago aparece el código QR en pantalla. Ese código es el boleto: muéstralo en el andén. La reserva sin pago dura diez minutos y después el asiento vuelve a quedar libre.'],
            ['¿Puedo cancelar o cambiar la fecha?', 'Puedes cancelar mientras el boleto siga reservado y no se haya pagado. Un pasaje ya pagado no se cambia de fecha en esta boletería: hay que comprar la nueva salida.'],
          ].map(([pregunta, respuesta], indice) => (
            <div className={faq === indice ? 'pregunta abierta' : 'pregunta'} key={pregunta}>
              <button type="button" aria-expanded={faq === indice} onClick={() => setFaq(faq === indice ? -1 : indice)}>
                {pregunta}
              </button>
              {faq === indice && <p>{respuesta}</p>}
            </div>
          ))}
        </div>
      </section>

      <section className="pagina">
        <div className="seccion-cabeza">
          <div>
            <p className="sobrelinea">Oficinas</p>
            <h2>Dónde comprar y dónde llegar.</h2>
          </div>
        </div>
        <div className="rejilla-oficinas">
          <article>
            <h3>Matriz La Maná</h3>
            <p>Taquilla de 05:00 a 21:00. También hay punto en Quevedo, Guayaquil y Durán.</p>
            <p><a href="tel:+593994127992">099 412 7992</a></p>
          </article>
          <article>
            <h3>Quevedo</h3>
            <p>Llegada al terminal de la ciudad. La bajada al centro se anuncia a bordo, cerca del mercado.</p>
          </article>
          <article>
            <h3>Quito</h3>
            <p>El turno de madrugada termina en Quitumbe. El de la sierra hace escala en Latacunga.</p>
          </article>
        </div>
      </section>

      <Destacados />
    </div>
  );
}

function Destacados() {
  const [notas, setNotas] = useState([]);

  useEffect(() => {
    solicitar('/blog').then((data) => setNotas(data.slice(0, 3))).catch(() => {});
  }, []);

  if (!notas.length) return null;

  return (
    <div className="franja-clara">
      <div className="pagina destacados">
        <section>
          <div className="seccion-cabeza">
            <div>
              <p className="sobrelinea">Noticias</p>
              <h2>De la ruta.</h2>
            </div>
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
      </div>
    </div>
  );
}
