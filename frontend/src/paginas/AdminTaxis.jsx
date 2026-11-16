import { useEffect, useState } from 'react';
import { solicitar } from '../api';
import MapaFlota from './MapaFlota';

export default function AdminTaxis({ token }) {
  const [resumen, setResumen] = useState(null);
  const [companias, setCompanias] = useState([]);
  const [viajes, setViajes] = useState([]);
  const [sos, setSos] = useState([]);
  const [reporte, setReporte] = useState(null);
  const [aviso, setAviso] = useState('');
  const [error, setError] = useState('');

  async function cargar() {
    const [datos, lista, historial, alertas, cifras] = await Promise.all([
      solicitar('/admin/taxi/resumen', { token }),
      solicitar('/admin/taxi/companias', { token }),
      solicitar('/admin/taxi/viajes', { token }),
      solicitar('/admin/taxi/sos', { token }),
      solicitar('/admin/taxi/reportes', { token }),
    ]);
    setResumen(datos);
    setCompanias(lista);
    setViajes(historial);
    setSos(alertas);
    setReporte(cifras);
  }

  useEffect(() => {
    cargar().catch((err) => setError(err.message));
    const reloj = setInterval(() => cargar().catch(() => {}), 8000);
    return () => clearInterval(reloj);
  }, [token]);

  async function guardarTarifa(event, tarifaId) {
    event.preventDefault();
    const datos = new FormData(event.currentTarget);
    try {
      await solicitar(`/admin/taxi/tarifas/${tarifaId}`, {
        method: 'PATCH',
        token,
        body: {
          arranque: Number(datos.get('arranque')),
          costo_km: Number(datos.get('costo_km')),
          costo_minuto: Number(datos.get('costo_minuto')),
          tarifa_minima: Number(datos.get('tarifa_minima')),
          recargo_nocturno_pct: Number(datos.get('recargo_nocturno_pct')),
        },
      });
      setAviso('Tarifa de ejemplo actualizada.');
      setError('');
      await cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div>
      {aviso && <p className="aviso-ok" role="status">{aviso}</p>}
      {error && <p className="aviso" role="alert">{error}</p>}
      {resumen && (
        <div className="kpis">
          <article><strong>{resumen.disponibles}</strong><span>Disponibles</span></article>
          <article><strong>{resumen.viajes_hoy}</strong><span>Viajes de hoy</span></article>
          <article><strong>{resumen.finalizados_hoy}</strong><span>Finalizados hoy</span></article>
          <article><strong>{resumen.companias}</strong><span>Compañías</span></article>
        </div>
      )}
      <section className="panel-form">
        <h2>Mapa de unidades</h2>
        <p className="meta">Amarillo es libre, gris está ocupado. El icono apunta hacia donde se mueve.</p>
        <MapaFlota unidades={(resumen?.flota || []).filter((item) => item.lat != null)} />
        {sos.length > 0 && (
          <ul className="lista-admin">
            {sos.map((alerta) => (
              <li key={alerta.id}>SOS {alerta.nombre} · viaje {alerta.viaje_id ?? '—'} · {alerta.lat}, {alerta.lng}</li>
            ))}
          </ul>
        )}
        {reporte?.por_dia?.length > 0 && (
          <p className="meta">
            Últimos días: {reporte.por_dia.map((dia) => `${dia.dia} ${dia.viajes} viajes $${Number(dia.ingresos).toFixed(2)}`).join(' · ')}
          </p>
        )}
      </section>
      <div className="rejilla-admin">
        <section className="panel-form">
          <h2>Flota en vivo</h2>
          <ul className="lista-admin">
            {(resumen?.flota || []).map((item) => (
              <li key={item.id}>
                <strong>Unidad {item.unidad}</strong>
                <span className="meta">{item.nombre} · {item.placa} · {item.estado}{item.ejemplo ? ' · ejemplo' : ''}</span>
                <span className="meta">{item.lat}, {item.lng}</span>
              </li>
            ))}
          </ul>
        </section>
        <section>
          {companias.map((compania) => (
            <form key={compania.id} className="panel-form" onSubmit={(event) => guardarTarifa(event, compania.tarifa_id)}>
              <h2>{compania.nombre}</h2>
              <p className="meta">{compania.tarifa_ejemplo ? 'Valores de ejemplo, no son una tarifa oficial.' : 'Tarifa configurada en el panel.'}</p>
              <label>Arranque<input name="arranque" defaultValue={compania.arranque} aria-label="Arranque" /></label>
              <label>Por km<input name="costo_km" defaultValue={compania.costo_km} aria-label="Costo por kilómetro" /></label>
              <label>Por minuto<input name="costo_minuto" defaultValue={compania.costo_minuto} aria-label="Costo por minuto" /></label>
              <label>Mínima<input name="tarifa_minima" defaultValue={compania.tarifa_minima} aria-label="Tarifa mínima" /></label>
              <label>Recargo nocturno %<input name="recargo_nocturno_pct" defaultValue={compania.recargo_nocturno_pct} aria-label="Recargo nocturno" /></label>
              <button type="submit" className="btn btn-pino">Guardar tarifa</button>
            </form>
          ))}
        </section>
      </div>
      <section className="panel-form">
        <h2>Viajes recientes</h2>
        <ul className="lista-admin">
          {viajes.map((item) => (
            <li key={item.id}>
              <strong>{item.estado}</strong>
              <span className="meta">{item.pasajero} · unidad {item.numero_unidad || '—'} · {item.destino_texto}</span>
            </li>
          ))}
          {viajes.length === 0 && <li>Aún no hay viajes de taxi.</li>}
        </ul>
      </section>
    </div>
  );
}
