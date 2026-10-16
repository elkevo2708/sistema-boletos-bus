import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { solicitar } from '../api';
import { useAuth } from '../contexto/AuthContext';
import { ahoraBogotaInput, fechaBogota, formatearFechaHora, formatearPesos } from '../formato';
import { PanelAnuncios, PanelBlog, PanelGaleria } from './AdminContenido';

export default function Admin() {
  const { usuario, token } = useAuth();
  const [rutas, setRutas] = useState([]);
  const [buses, setBuses] = useState([]);
  const [ventas, setVentas] = useState(null);
  const [fecha, setFecha] = useState(fechaBogota(0));
  const [mensaje, setMensaje] = useState('');
  const [error, setError] = useState('');
  const [ocupado, setOcupado] = useState(false);
  const [pestana, setPestana] = useState('operacion');

  const esAdmin = usuario?.rol === 'administrador';

  useEffect(() => {
    if (!esAdmin) return;
    Promise.all([
      solicitar('/admin/rutas', { token }),
      solicitar('/admin/buses', { token }),
      solicitar(`/admin/ventas?fecha=${fechaBogota(0)}`, { token }),
    ]).then(([listaRutas, listaBuses, reporte]) => {
      setRutas(listaRutas);
      setBuses(listaBuses);
      setVentas(reporte);
    }).catch((err) => setError(err.message));
  }, [esAdmin, token]);

  async function crearViaje(event) {
    event.preventDefault();
    const datos = new FormData(event.currentTarget);
    const precio = datos.get('precio');
    setOcupado(true);
    setError('');
    setMensaje('');
    try {
      const creado = await solicitar('/admin/viajes', {
        method: 'POST',
        token,
        body: {
          ruta_id: Number(datos.get('ruta_id')),
          bus_id: Number(datos.get('bus_id')),
          salida: datos.get('salida'),
          precio: precio ? precio : null,
        },
      });
      setMensaje(`Viaje ${creado.id} creado. Llega ${formatearFechaHora(creado.llegada_est)} a ${formatearPesos(creado.precio)}.`);
      event.currentTarget.reset();
    } catch (err) {
      setError(err.message);
    } finally {
      setOcupado(false);
    }
  }

  async function cambiarTarifa(event) {
    event.preventDefault();
    const datos = new FormData(event.currentTarget);
    setOcupado(true);
    setError('');
    setMensaje('');
    try {
      const rutaId = datos.get('ruta_id');
      const actualizada = await solicitar(`/admin/rutas/${rutaId}/tarifa`, {
        method: 'PATCH',
        token,
        body: { precio_base: datos.get('precio_base') },
      });
      setMensaje(`Tarifa actualizada a ${formatearPesos(actualizada.precio_base)}. Quedó registro en auditoría.`);
      setRutas((actual) => actual.map((ruta) => (
        String(ruta.id) === String(rutaId) ? { ...ruta, precio_base: actualizada.precio_base } : ruta
      )));
    } catch (err) {
      setError(err.message);
    } finally {
      setOcupado(false);
    }
  }

  async function consultarVentas(event) {
    event?.preventDefault();
    setOcupado(true);
    setError('');
    try {
      setVentas(await solicitar(`/admin/ventas?fecha=${fecha}`, { token }));
    } catch (err) {
      setError(err.message);
    } finally {
      setOcupado(false);
    }
  }

  if (!usuario) {
    return (
      <div className="pagina estrecha">
        <h1>Taquilla</h1>
        <p>Entra con la cuenta administradora para programar viajes y ver las ventas.</p>
        <Link className="btn btn-pino" to="/ingresar?siguiente=/admin" aria-label="Ingresar a taquilla">Ingresar</Link>
      </div>
    );
  }

  if (!esAdmin) {
    return (
      <div className="pagina estrecha">
        <h1>Taquilla</h1>
        <p className="aviso" role="alert">Esta cuenta no tiene rol administrador.</p>
      </div>
    );
  }

  return (
    <div className="pagina">
      <h1>Taquilla</h1>
      <p className="lead">Salidas, tarifas, noticias, promociones y la galería de la cooperativa.</p>
      <div className="filtros" role="tablist" aria-label="Secciones de taquilla">
        {[
          ['operacion', 'Operación'],
          ['blog', 'Noticias'],
          ['anuncios', 'Anuncios'],
          ['galeria', 'Galería'],
        ].map(([id, etiqueta]) => (
          <button key={id} type="button" role="tab" aria-selected={pestana === id} className={pestana === id ? 'activo' : ''} onClick={() => setPestana(id)} aria-label={`Abrir ${etiqueta}`}>
            {etiqueta}
          </button>
        ))}
      </div>
      {mensaje && <p className="aviso-ok" role="status">{mensaje}</p>}
      {error && <p className="aviso" role="alert">{error}</p>}

      {pestana === 'blog' && <PanelBlog token={token} />}
      {pestana === 'anuncios' && <PanelAnuncios token={token} />}
      {pestana === 'galeria' && <PanelGaleria token={token} />}

      {pestana === 'operacion' && (
      <>
      <div className="rejilla-admin">
        <form className="panel-form" onSubmit={crearViaje}>
          <h2>Crear viaje</h2>
          <label>
            Ruta
            <select name="ruta_id" required defaultValue="" aria-label="Ruta del viaje">
              <option value="" disabled>Selecciona</option>
              {rutas.map((ruta) => (
                <option key={ruta.id} value={ruta.id}>
                  {ruta.origen} → {ruta.destino} · {ruta.duracion_min} min · {formatearPesos(ruta.precio_base)}
                </option>
              ))}
            </select>
          </label>
          <label>
            Bus
            <select name="bus_id" required defaultValue="" aria-label="Bus del viaje">
              <option value="" disabled>Selecciona</option>
              {buses.map((bus) => (
                <option key={bus.id} value={bus.id} disabled={bus.estado !== 'operativo'}>
                  Disco {bus.numero_disco} · {bus.placa} · {bus.capacidad} puestos · {bus.estado}
                </option>
              ))}
            </select>
          </label>
          <label>
            Salida
            <input type="datetime-local" name="salida" required min={ahoraBogotaInput()} aria-label="Fecha y hora de salida" />
          </label>
          <label>
            Precio (opcional, usa la tarifa de la ruta)
            <input type="number" name="precio" min="1" step="0.01" aria-label="Precio del viaje" />
          </label>
          <button type="submit" className="btn btn-arcilla" disabled={ocupado} aria-label="Crear viaje">Crear viaje</button>
        </form>

        <form className="panel-form" onSubmit={cambiarTarifa}>
          <h2>Cambiar tarifa</h2>
          <label>
            Ruta
            <select name="ruta_id" required defaultValue="" aria-label="Ruta a retarifar">
              <option value="" disabled>Selecciona</option>
              {rutas.map((ruta) => (
                <option key={ruta.id} value={ruta.id}>
                  {ruta.origen} → {ruta.destino} · hoy {formatearPesos(ruta.precio_base)}
                </option>
              ))}
            </select>
          </label>
          <label>
            Nueva tarifa base
            <input type="number" name="precio_base" required min="1" step="0.01" aria-label="Nueva tarifa base" />
          </label>
          <button type="submit" className="btn btn-pino" disabled={ocupado} aria-label="Actualizar tarifa">Actualizar tarifa</button>
        </form>
      </div>

      <section className="panel-form ventas">
        <div className="ventas-cabeza">
          <h2>Ventas del día</h2>
          <form onSubmit={consultarVentas} className="fila-fecha">
            <label>
              Fecha
              <input type="date" value={fecha} onChange={(e) => setFecha(e.target.value)} aria-label="Fecha del reporte de ventas" />
            </label>
            <button type="submit" className="btn btn-pino" disabled={ocupado} aria-label="Consultar ventas del día">Consultar</button>
          </form>
        </div>
        <div className="tabla-wrap">
          <table>
            <caption>Pagos aprobados {ventas ? `del ${ventas.fecha}` : ''}</caption>
            <thead>
              <tr>
                <th>Ruta</th>
                <th>Boletos</th>
                <th>Total</th>
              </tr>
            </thead>
            <tbody>
              {ventas?.filas.length ? ventas.filas.map((fila) => (
                <tr key={fila.ruta_id}>
                  <td>{fila.origen} → {fila.destino}</td>
                  <td>{fila.boletos_pagados}</td>
                  <td>{formatearPesos(fila.total)}</td>
                </tr>
              )) : (
                <tr>
                  <td colSpan={3}>Aún no hay pagos aprobados en esta fecha.</td>
                </tr>
              )}
            </tbody>
            <tfoot>
              <tr>
                <th colSpan={2}>Total</th>
                <th>{formatearPesos(ventas?.total || 0)}</th>
              </tr>
            </tfoot>
          </table>
        </div>
      </section>
      </>
      )}
    </div>
  );
}
