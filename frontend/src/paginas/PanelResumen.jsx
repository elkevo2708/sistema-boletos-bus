import { useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { CalendarPlus, MapPinned, Plus, Route, TrendingDown, TrendingUp } from 'lucide-react';
import { fechaBogota, formatearDia, formatearFechaHora, formatearPesos } from '../formato';
import { GraficoBarras, GraficoHoras, GraficoLinea } from '../ui/Graficos';
import { Esqueleto, EstadoVacio, Insignia, Tabla } from '../ui/ui';

function Variacion({ valor, nota }) {
  if (valor == null) return null;
  const sube = valor >= 0;
  const Icono = sube ? TrendingUp : TrendingDown;
  return (
    <small className={sube ? 'kpi-var sube' : 'kpi-var baja'}>
      <Icono size={16} aria-hidden="true" />
      {sube ? '+' : ''}{valor} % {nota}
    </small>
  );
}

function entero(dato) {
  return dato ? String(Math.round(dato.valor)) : '—';
}

function tonoEstado(estado) {
  if (['aprobado', 'finalizado', 'pagado'].includes(estado)) return 'verde';
  if (['cancelado', 'rechazado'].includes(estado)) return 'peligro';
  return 'amarillo';
}

function MapaTaxis({ unidades }) {
  const caja = useRef(null);
  const mapa = useRef(null);
  const clave = unidades.map((unidad) => unidad.id).join(',');

  useEffect(() => {
    let cancelado = false;
    (async () => {
      const leaflet = await import('leaflet');
      await import('leaflet/dist/leaflet.css');
      if (cancelado || !caja.current) return;
      const L = leaflet.default ?? leaflet;
      const lienzo = L.map(caja.current, { zoomControl: false }).setView([-0.9406, -79.2344], 14);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap',
        maxZoom: 19,
      }).addTo(lienzo);
      unidades.forEach((unidad) => {
        const marca = L.marker([unidad.lat, unidad.lng], {
          icon: L.divIcon({
            className: 'pin-taxi',
            html: `<span style="background:${unidad.ejemplo ? '#1497b8' : '#f2c200'}"></span>`,
            iconSize: [18, 18],
            iconAnchor: [9, 9],
          }),
        }).addTo(lienzo);
        marca.bindTooltip(`Unidad ${unidad.unidad}${unidad.ejemplo ? ' · ejemplo' : ''}`);
      });
      if (unidades.length) {
        lienzo.fitBounds(L.latLngBounds(unidades.map((unidad) => [unidad.lat, unidad.lng])).pad(0.35));
      }
      mapa.current = lienzo;
      setTimeout(() => lienzo.invalidateSize(), 180);
    })();
    return () => {
      cancelado = true;
      mapa.current?.remove();
      mapa.current = null;
    };
  }, [clave]);

  return <div ref={caja} className="saas-mapa" role="img" aria-label="Mapa de taxis en línea" />;
}

export default function PanelResumen({ tablero, cargando, error, rango, onRango, onConsultar, onIr, puede }) {
  if (cargando && !tablero) {
    return (
      <div className="kpis" aria-label="Cargando indicadores">
        {Array.from({ length: 8 }, (_, indice) => <Esqueleto key={indice} lineas={2} />)}
      </div>
    );
  }
  if (error && !tablero) return <p className="aviso" role="alert">{error}</p>;
  if (!tablero) return null;

  const transporte = tablero.transporte;
  const turismo = tablero.turismo;
  const taxi = tablero.taxi;
  const tarjetas = [];
  if (transporte) {
    const k = transporte.kpis;
    tarjetas.push(
      ['Ventas de hoy', formatearPesos(k.ventas_hoy.valor), k.ventas_hoy.variacion, 'frente a ayer'],
      ['Ventas del mes', formatearPesos(k.ventas_mes.valor), k.ventas_mes.variacion, 'frente al mes anterior'],
      ['Boletos vendidos', entero(k.boletos), k.boletos.variacion, 'en el rango, frente al anterior'],
      ['Viajes activos', entero(k.viajes_activos), k.viajes_activos.variacion, 'salidas de hoy frente a ayer'],
      ['Ocupación', `${k.ocupacion.valor} %`, k.ocupacion.variacion, 'de hoy frente a ayer'],
    );
  }
  if (taxi) {
    tarjetas.push(
      ['Taxis en línea', entero(taxi.kpis.en_linea), null, ''],
      ['Viajes de taxi hoy', entero(taxi.kpis.viajes_hoy), taxi.kpis.viajes_hoy.variacion, 'frente a ayer'],
    );
  }
  if (turismo) {
    tarjetas.push(
      ['Fichas publicadas', String(turismo.fichas), null, ''],
      ['Atractivos', String(turismo.atractivos), null, ''],
      ['Eventos publicados', String(turismo.eventos_publicados), null, ''],
    );
  }

  return (
    <div className="saas-resumen">
      {tablero.demo && (
        <p className="aviso-ok" role="status">Parte de estas cifras son de demostración y están marcadas como ejemplo. No son operación real ni tarifas oficiales.</p>
      )}
      <form className="saas-rango" onSubmit={(evento) => { evento.preventDefault(); onConsultar(); }}>
        <label>
          Desde
          <input type="date" value={rango.desde} max={rango.hasta} onChange={(evento) => onRango({ ...rango, desde: evento.target.value })} aria-label="Fecha inicial del resumen" />
        </label>
        <label>
          Hasta
          <input type="date" value={rango.hasta} min={rango.desde} onChange={(evento) => onRango({ ...rango, hasta: evento.target.value })} aria-label="Fecha final del resumen" />
        </label>
        <button type="submit" className="btn btn-pino" aria-label="Aplicar rango de fechas">Aplicar</button>
        <button type="button" className="btn btn-fantasma" onClick={() => onConsultar(fechaBogota(-29), fechaBogota(0))} aria-label="Ver los últimos 30 días">
          30 días
        </button>
      </form>

      <div className="kpis">
        {tarjetas.map(([etiqueta, valor, variacion, nota]) => (
          <article key={etiqueta}>
            <span>{etiqueta}</span>
            <strong>{valor}</strong>
            <Variacion valor={variacion} nota={nota} />
          </article>
        ))}
      </div>

      <div className="saas-accesos">
        {puede.transporte && <button type="button" className="btn btn-pino" onClick={() => onIr('transporte', 'operacion')} aria-label="Crear viaje"><Plus size={18} aria-hidden="true" /> Crear viaje</button>}
        {puede.turismo && <button type="button" className="btn btn-fantasma" onClick={() => onIr('turismo', 'turismo')} aria-label="Publicar atractivo"><Route size={18} aria-hidden="true" /> Publicar atractivo</button>}
        {puede.turismo && <button type="button" className="btn btn-fantasma" onClick={() => onIr('turismo', 'turismo')} aria-label="Nuevo evento"><CalendarPlus size={18} aria-hidden="true" /> Nuevo evento</button>}
        {puede.taxi && <Link className="btn btn-fantasma" to="/taxi"><MapPinned size={18} aria-hidden="true" /> Ver mapa de taxis</Link>}
      </div>

      <div className="saas-graficos">
        {transporte && (
          <section className="panel-form">
            <h2>Ventas por día</h2>
            <GraficoLinea puntos={transporte.ventas_por_dia} titulo="Ventas de boletos por día" />
            {transporte.ventas_por_dia.every((punto) => !punto.total) && <EstadoVacio titulo="Sin ventas" texto="No hay pagos aprobados en este rango." />}
          </section>
        )}
        {transporte && (
          <section className="panel-form">
            <h2>Ocupación por ruta</h2>
            {transporte.ocupacion_por_ruta.length ? (
              <GraficoBarras
                titulo="Ocupación por ruta"
                puntos={transporte.ocupacion_por_ruta.map((fila) => ({
                  nombre: fila.ruta,
                  valor: fila.ocupados,
                  detalle: `${fila.ocupacion} %`,
                }))}
              />
            ) : <EstadoVacio titulo="Sin salidas" texto="No hay viajes en este rango." />}
          </section>
        )}
        {taxi && (
          <section className="panel-form">
            <h2>Viajes de taxi por hora</h2>
            <GraficoHoras puntos={taxi.por_hora} titulo="Viajes de taxi agrupados por hora" />
            {taxi.por_hora.every((punto) => !punto.total) && <EstadoVacio titulo="Sin viajes de taxi" texto="No hay solicitudes en este rango." />}
          </section>
        )}
        {turismo && (
          <section className="panel-form">
            <h2>Atractivos publicados</h2>
            <p className="meta">Orden editorial. El portal no cuenta visitas, así que esta lista no es un ranking de audiencia.</p>
            {turismo.top_atractivos.length ? (
              <ul className="saas-top-lista">
                {turismo.top_atractivos.map((ficha) => (
                  <li key={ficha.slug}>
                    <Link to={`/atractivos/${ficha.slug}`}>{ficha.nombre}</Link>
                    <span>{ficha.zona}</span>
                    {ficha.destacado && <Insignia tono="amarillo">Destacado</Insignia>}
                  </li>
                ))}
              </ul>
            ) : <EstadoVacio titulo="Sin atractivos" texto="Publica la primera ficha desde Portal turismo." />}
          </section>
        )}
      </div>

      <div className="saas-dos">
        {transporte && (
          <section className="panel-form">
            <h2>Últimas ventas</h2>
            <Tabla
              titulo="Pagos más recientes"
              columnas={['Ruta', 'Estado', 'Total', 'Fecha']}
              vacio="Aún no hay pagos."
              filas={transporte.ventas_recientes.map((fila) => ({
                key: fila.id,
                celdas: [
                  fila.ruta,
                  <span key="e">{fila.demo && <Insignia>Ejemplo</Insignia>} <Insignia tono={tonoEstado(fila.estado)}>{fila.estado}</Insignia></span>,
                  formatearPesos(fila.monto),
                  formatearFechaHora(fila.fecha),
                ],
              }))}
            />
          </section>
        )}
        {taxi && (
          <section className="panel-form">
            <h2>Últimos viajes de taxi</h2>
            <Tabla
              titulo="Solicitudes recientes de taxi"
              columnas={['Destino', 'Estado', 'Tarifa', 'Fecha']}
              vacio="Aún no hay viajes de taxi."
              filas={taxi.recientes.map((fila) => ({
                key: fila.id,
                celdas: [
                  fila.destino || 'Sin destino',
                  <span key="e">{fila.demo && <Insignia>Ejemplo</Insignia>} <Insignia tono={tonoEstado(fila.estado)}>{fila.estado}</Insignia></span>,
                  formatearPesos(fila.tarifa),
                  formatearFechaHora(fila.fecha),
                ],
              }))}
            />
          </section>
        )}
        {turismo && (
          <section className="panel-form">
            <h2>Próximos eventos</h2>
            {turismo.eventos_proximos.length ? (
              <ul className="saas-top-lista">
                {turismo.eventos_proximos.map((evento) => (
                  <li key={evento.slug}>
                    <Link to={`/agenda/${evento.slug}`}>{evento.titulo}</Link>
                    <span>{formatearDia(evento.inicio)} · {evento.lugar}</span>
                    {evento.demo && <Insignia>Ejemplo</Insignia>}
                  </li>
                ))}
              </ul>
            ) : <EstadoVacio titulo="Sin eventos próximos" texto="La agenda publicada no tiene fechas por venir." />}
          </section>
        )}
        {taxi && (
          <section className="panel-form">
            <h2>Taxis en línea</h2>
            {taxi.unidades.length ? <MapaTaxis unidades={taxi.unidades} /> : <EstadoVacio titulo="Nadie en línea" texto="Cuando un conductor se conecte, aparece en este mapa." />}
          </section>
        )}
      </div>
      {error && <p className="aviso" role="alert">{error}</p>}
    </div>
  );
}
