import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { solicitar } from '../api';
import HeroPortada from '../componentes/HeroPortada';
import { fechaBogota, formatearDia, formatearFechaHora, formatearDinero } from '../formato';

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
  ['Tres formas de pago', 'DeUna!, tarjeta de crédito o débito, y PayPhone.'],
  ['Equipaje de bodega', 'Etiquétalo con tu nombre y el número de asiento. En el bus de dos pisos el pasillo va despejado.'],
  ['Taquilla de madrugada', 'El andén abre a las 05:00. Llega veinte minutos antes: el abordaje cierra cuando el disco enciende luces.'],
  ['Horario de Ecuador', 'Todas las salidas se publican en hora local, sin conversión. La taquilla cierra a las 21:00.'],
];

export default function Buscar() {
  const [ciudades, setCiudades] = useState([]);
  const [origen, setOrigen] = useState('');
  const [destino, setDestino] = useState('');
  const [fecha, setFecha] = useState(fechaBogota(0));
  const [viajes, setViajes] = useState(null);
  const [proximas, setProximas] = useState([]);
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

  function irAResultados() {
    document.getElementById('rutas')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  async function buscar(event, valores, desplazar = Boolean(event)) {
    event?.preventDefault();
    const o = valores?.origen ?? origen;
    const d = valores?.destino ?? destino;
    const f = valores?.fecha ?? fecha;
    if (desplazar) irAResultados();
    if (!o || !d || !f) {
      setViajes(null);
      setProximas([]);
      setError('Elige origen, destino y fecha.');
      return;
    }
    if (o === d) {
      setViajes(null);
      setProximas([]);
      setError('Elige un destino distinto al origen.');
      return;
    }
    setCargando(true);
    setError('');
    setViajes(null);
    setProximas([]);
    try {
      const [data, fechas] = await Promise.all([
        solicitar(`/viajes?origen=${o}&destino=${d}&fecha=${f}`),
        solicitar(`/viajes/proximas?origen=${o}&destino=${d}&desde=${f}`).catch(() => []),
      ]);
      setViajes(data);
      setProximas(Array.isArray(fechas) ? fechas : []);
    } catch (err) {
      setViajes(null);
      setProximas([]);
      const red = err?.message === 'Failed to fetch' || err?.message === 'NetworkError when attempting to fetch resource.';
      setError(red ? 'No se pudo consultar las salidas. Inténtalo de nuevo.' : err.message);
    } finally {
      setCargando(false);
      if (desplazar) irAResultados();
    }
  }

  useEffect(() => {
    if (!auto || !origen || !destino) return;
    setAuto(false);
    buscar(null, { origen, destino, fecha }, false);
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
    buscar(null, { origen: String(o.id), destino: String(d.id), fecha }, true);
  }

  function irAFecha(dia) {
    setFecha(dia);
    buscar(null, { origen, destino, fecha: dia }, true);
  }

  function buscarRegreso() {
    const salida = destino;
    const llegada = origen;
    setOrigen(salida);
    setDestino(llegada);
    buscar(null, { origen: salida, destino: llegada, fecha }, true);
  }

  const nombre = (id) => ciudades.find((ciudad) => String(ciudad.id) === String(id));

  return (
    <div>
      <HeroPortada>
        <form id="buscar" className="panel-busqueda" noValidate onSubmit={buscar}>
          <label>
            Origen
            <select value={origen} onChange={(e) => setOrigen(e.target.value)} aria-label="Ciudad de origen">
              <option value="">Selecciona</option>
              {ciudades.map((ciudad) => (
                <option key={ciudad.id} value={ciudad.id}>{ciudad.nombre} · {ciudad.departamento}</option>
              ))}
            </select>
          </label>
          <button type="button" className="intercambio" onClick={intercambiar} aria-label="Intercambiar origen y destino">⇄</button>
          <label>
            Destino
            <select value={destino} onChange={(e) => setDestino(e.target.value)} aria-label="Ciudad de destino">
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
            <input type="date" value={fecha} min={fechaBogota(0)} onChange={(e) => setFecha(e.target.value)} aria-label="Fecha de salida" />
          </label>
          <button type="submit" className="btn btn-arcilla btn-buscar" aria-label="Buscar pasajes" disabled={cargando}>
            {cargando ? 'Buscando…' : 'Buscar pasajes'}
          </button>
        </form>
        {error && <p className="aviso aviso-hero" role="alert">{error}</p>}
      </HeroPortada>

      <section className="cifras" aria-label="La cooperativa en cifras">
        <article><strong>7</strong><span>Ciudades en la red</span></article>
        <article><strong>23</strong><span>Discos en servicio</span></article>
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

      <section className="pagina resultados" id="rutas" aria-live="polite" aria-busy={cargando}>
        <div className="seccion-cabeza">
          <div>
            <p className="sobrelinea">Horarios</p>
            <h2>
              {cargando && 'Buscando salidas…'}
              {!cargando && viajes?.length
                ? `${viajes.length} salida${viajes.length === 1 ? '' : 's'} · ${nombre(origen)?.nombre ?? ''} → ${nombre(destino)?.nombre ?? ''}`
                : null}
              {!cargando && viajes && viajes.length === 0 && 'No hay salidas para esa fecha'}
              {!cargando && !viajes && !error && 'Salidas del día'}
              {!cargando && error && !viajes && 'No se pudo buscar'}
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
        {error && <p className="aviso" role="alert">{error}</p>}
        {cargando && <p className="buscando" role="status">Buscando salidas para esa ruta.</p>}
        {!cargando && viajes && viajes.length === 0 && (
          <div className="vacio" role="status">
            <p>No hay salidas para esa fecha.</p>
            {proximas.length > 0 && (
              <>
                <p>Estas fechas sí tienen cupo en {nombre(origen)?.nombre} → {nombre(destino)?.nombre}.</p>
                <div className="fechas-siguientes">
                  {proximas.map((item) => (
                    <button
                      type="button"
                      key={item.fecha}
                      onClick={() => irAFecha(String(item.fecha).slice(0, 10))}
                      aria-label={`Buscar el ${formatearDia(item.fecha)}`}
                    >
                      {formatearDia(item.fecha)} · {item.salidas} salida{Number(item.salidas) === 1 ? '' : 's'}
                    </button>
                  ))}
                </div>
              </>
            )}
            <button
              type="button"
              className="btn btn-pino"
              onClick={buscarRegreso}
              aria-label={`Buscar el regreso de ${nombre(destino)?.nombre ?? 'destino'} a ${nombre(origen)?.nombre ?? 'origen'}`}
            >
              Buscar el regreso: {nombre(destino)?.nombre} → {nombre(origen)?.nombre}
            </button>
          </div>
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
            <li><strong>3</strong><span>Paga con DeUna!, tarjeta o PayPhone.</span></li>
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
            ['¿Cómo puedo pagar?', 'En línea aceptamos DeUna! (la billetera de Banco Pichincha), tarjeta de crédito o débito y PayPhone. El número de tarjeta no sale de su navegador.'],
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
