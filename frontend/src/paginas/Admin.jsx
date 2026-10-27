import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { solicitar } from '../api';
import { useAuth } from '../contexto/AuthContext';
import { ahoraBogotaInput, fechaBogota, formatearFechaHora, formatearPesos } from '../formato';
import { PanelAnuncios, PanelBlog, PanelGaleria } from './AdminContenido';
import { PanelEmisor, PanelFacturas } from './AdminFacturas';
import PanelFlota from './AdminFlota';
import AdminPagos from './AdminPagos';
import AdminPortada from './AdminPortada';
import AdminTaxis from './AdminTaxis';
import AdminTurismo from './AdminTurismo';

export default function Admin() {
  const { usuario, token } = useAuth();
  const [rutas, setRutas] = useState([]);
  const [buses, setBuses] = useState([]);
  const [viajes, setViajes] = useState([]);
  const [ventas, setVentas] = useState(null);
  const [fecha, setFecha] = useState(fechaBogota(0));
  const [mensaje, setMensaje] = useState('');
  const [error, setError] = useState('');
  const [ocupado, setOcupado] = useState(false);
  const [modulo, setModulo] = useState('resumen');
  const [menu, setMenu] = useState(false);
  const [pestana, setPestana] = useState('operacion');
  const [kpis, setKpis] = useState(null);

  const modulos = {
    administrador: ['resumen', 'turismo', 'transporte', 'taxi'],
    operador_turismo: ['turismo'],
    operador_transporte: ['transporte'],
    operador_taxi: ['taxi'],
  }[usuario?.rol] || [];
  const puedeTransporte = modulos.includes('transporte');
  const carga = useRef(0);

  function recargarCatalogo() {
    const id = carga.current + 1;
    carga.current = id;
    return Promise.all([
      solicitar('/admin/rutas', { token }),
      solicitar('/admin/buses', { token }),
      solicitar('/admin/viajes', { token }),
    ]).then(([listaRutas, listaBuses, listaViajes]) => {
      if (carga.current !== id) return;
      setRutas(listaRutas);
      setBuses(listaBuses);
      setViajes(listaViajes);
    });
  }

  useEffect(() => {
    if (!usuario || !modulos.length) return;
    if (!modulos.includes(modulo)) setModulo(modulos[0]);
    if (modulos.includes('resumen')) {
      solicitar('/admin/resumen', { token }).then(setKpis).catch(() => {});
    }
  }, [usuario, token]);

  useEffect(() => {
    if (!puedeTransporte) return;
    const id = carga.current + 1;
    carga.current = id;
    Promise.all([
      solicitar('/admin/rutas', { token }),
      solicitar('/admin/buses', { token }),
      solicitar('/admin/viajes', { token }),
      solicitar(`/admin/ventas?fecha=${fechaBogota(0)}`, { token }),
    ]).then(([listaRutas, listaBuses, listaViajes, reporte]) => {
      if (carga.current !== id) return;
      setRutas(listaRutas);
      setBuses(listaBuses);
      setViajes(listaViajes);
      setVentas(reporte);
    }).catch((err) => setError(err.message));
  }, [puedeTransporte, token]);

  async function crearViaje(event) {
    event.preventDefault();
    const datos = new FormData(event.currentTarget);
    const rutaId = datos.get('ruta_id');
    const busId = datos.get('bus_id');
    const salida = String(datos.get('salida') || '');
    const precio = String(datos.get('precio') || '').trim();
    setError('');
    setMensaje('');
    if (!rutaId) {
      setError('Selecciona la ruta del viaje.');
      return;
    }
    if (!busId) {
      setError('Selecciona el bus del viaje.');
      return;
    }
    if (!salida) {
      setError('Indica la fecha y hora de salida.');
      return;
    }
    if (salida <= ahoraBogotaInput()) {
      setError('La salida debe ser futura.');
      return;
    }
    if (precio && Number(precio) <= 0) {
      setError('El precio debe ser mayor que cero.');
      return;
    }
    const formulario = event.currentTarget;
    setOcupado(true);
    try {
      const creado = await solicitar('/admin/viajes', {
        method: 'POST',
        token,
        body: {
          ruta_id: Number(rutaId),
          bus_id: Number(busId),
          salida,
          precio: precio || null,
        },
      });
      setMensaje(`Viaje ${creado.id} creado. Llega ${formatearFechaHora(creado.llegada_est)} a ${formatearPesos(creado.precio)}.`);
      formulario.reset();
      await recargarCatalogo();
    } catch (err) {
      setError(err.message);
    } finally {
      setOcupado(false);
    }
  }

  async function cambiarTarifa(event) {
    event.preventDefault();
    const datos = new FormData(event.currentTarget);
    const rutaId = datos.get('ruta_id');
    const precio = String(datos.get('precio_base') || '').trim();
    setError('');
    setMensaje('');
    if (!rutaId) {
      setError('Selecciona la ruta a retarifar.');
      return;
    }
    if (!precio || Number(precio) <= 0) {
      setError('La tarifa debe ser mayor que cero.');
      return;
    }
    setOcupado(true);
    try {
      const actualizada = await solicitar(`/admin/rutas/${rutaId}/tarifa`, {
        method: 'PATCH',
        token,
        body: { precio_base: precio },
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

  async function cancelarViaje(viaje) {
    if (!window.confirm(`¿Cancelar el viaje ${viaje.origen} → ${viaje.destino}?`)) return;
    setError('');
    setMensaje('');
    setOcupado(true);
    try {
      await solicitar(`/admin/viajes/${viaje.id}`, { method: 'DELETE', token });
      setMensaje(`Viaje ${viaje.id} cancelado.`);
      await recargarCatalogo();
    } catch (err) {
      setError(err.message);
    } finally {
      setOcupado(false);
    }
  }

  async function generarHorario() {
    setError('');
    setMensaje('');
    setOcupado(true);
    try {
      const resultado = await solicitar('/admin/horarios/generar', { method: 'POST', token });
      setMensaje(resultado.creados
        ? `Se programaron ${resultado.creados} salidas nuevas para los próximos 30 días.`
        : 'El horario de los próximos 30 días ya estaba completo.');
      await recargarCatalogo();
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
        <h1>Panel</h1>
        <p>Un solo ingreso para turismo, transporte y taxis.</p>
        <Link className="btn btn-pino" to="/ingresar?siguiente=/admin" aria-label="Ingresar al panel">Ingresar</Link>
      </div>
    );
  }

  if (!modulos.length) {
    return (
      <div className="pagina estrecha">
        <h1>Panel</h1>
        <p className="aviso" role="alert">Esta cuenta no administra un módulo.</p>
      </div>
    );
  }

  const etiquetas = { resumen: 'Resumen', turismo: 'Portal turismo', transporte: 'Transporte', taxi: 'Taxis' };
  const subtransporte = [
    ['operacion', 'Viajes'],
    ['pagos', 'Pagos'],
    ['flota', 'Flota'],
    ['facturas', 'Facturas'],
    ['emisor', 'Emisor SRI'],
    ['blog', 'Noticias'],
    ['anuncios', 'Promos'],
    ['galeria', 'Galería'],
  ];

  return (
    <div className="dashboard">
      {menu && <button type="button" className="drawer-fondo" aria-label="Cerrar módulos" onClick={() => setMenu(false)} />}
      <aside className={menu ? 'dash-lado abierto' : 'dash-lado'} aria-label="Módulos del panel">
        <p className="sobrelinea">Panel</p>
        {modulos.map((id) => (
          <button key={id} type="button" className={modulo === id ? 'activo' : ''} onClick={() => { setModulo(id); setMenu(false); }} aria-label={`Abrir ${etiquetas[id]}`}>
            {etiquetas[id]}
          </button>
        ))}
      </aside>
      <div className="dash-cuerpo">
      <button type="button" className="btn btn-fantasma dash-abrir" onClick={() => setMenu(true)} aria-label="Abrir módulos del panel">Módulos</button>
      <h1>{etiquetas[modulo]}</h1>
      {modulo === 'resumen' && (
        <div className="kpis" aria-label="Indicadores">
          <article><strong>{formatearPesos(kpis?.transporte?.ventas_hoy || 0)}</strong><span>Ventas de boletos hoy</span></article>
          <article><strong>{kpis?.transporte?.viajes_hoy ?? '—'}</strong><span>Viajes del día</span></article>
          <article><strong>{kpis?.transporte ? `${Math.round(kpis.transporte.ocupacion * 100)} %` : '—'}</strong><span>Ocupación</span></article>
          <article><strong>{kpis?.turismo?.mensajes ?? '—'}</strong><span>Mensajes</span></article>
          <article><strong>{kpis?.turismo?.fichas ?? '—'}</strong><span>Fichas turísticas</span></article>
          <article><strong>{kpis?.turismo?.eventos_proximos ?? '—'}</strong><span>Eventos próximos</span></article>
          <article><strong>{kpis?.taxi?.viajes_hoy ?? '—'}</strong><span>Viajes de taxi hoy</span></article>
        </div>
      )}
      {modulo === 'turismo' && (
        <div className="filtros" role="tablist" aria-label="Portal turismo">
          <button type="button" className={pestana === 'turismo' ? 'activo' : ''} onClick={() => setPestana('turismo')} aria-label="Abrir fichas">Fichas y agenda</button>
          <button type="button" className={pestana === 'portada' ? 'activo' : ''} onClick={() => setPestana('portada')} aria-label="Abrir portada">Portada</button>
        </div>
      )}
      {modulo === 'transporte' && (
        <div className="filtros" role="tablist" aria-label="Transporte">
          {subtransporte.map(([id, etiqueta]) => (
            <button key={id} type="button" className={pestana === id ? 'activo' : ''} onClick={() => setPestana(id)} aria-label={`Abrir ${etiqueta}`}>{etiqueta}</button>
          ))}
        </div>
      )}
      {mensaje && <p className="aviso-ok" role="status">{mensaje}</p>}
      {error && <p className="aviso" role="alert">{error}</p>}

      {modulo === 'turismo' && pestana === 'portada' && <AdminPortada token={token} />}
      {modulo === 'turismo' && pestana !== 'portada' && <AdminTurismo token={token} />}
      {modulo === 'taxi' && <AdminTaxis token={token} />}
      {modulo === 'transporte' && pestana === 'pagos' && <AdminPagos token={token} />}
      {modulo === 'transporte' && pestana === 'flota' && <PanelFlota token={token} onCambio={recargarCatalogo} />}
      {modulo === 'transporte' && pestana === 'facturas' && <PanelFacturas token={token} />}
      {modulo === 'transporte' && pestana === 'emisor' && <PanelEmisor token={token} />}
      {modulo === 'transporte' && pestana === 'blog' && <PanelBlog token={token} />}
      {modulo === 'transporte' && pestana === 'anuncios' && <PanelAnuncios token={token} />}
      {modulo === 'transporte' && pestana === 'galeria' && <PanelGaleria token={token} />}

      {modulo === 'transporte' && (pestana === 'operacion' || pestana === 'turismo' || pestana === 'portada') && (
      <>
      <div className="rejilla-admin">
        <form className="panel-form" noValidate onSubmit={crearViaje}>
          <h2>Crear viaje</h2>
          <label>
            Ruta
            <select name="ruta_id" defaultValue="" aria-label="Ruta del viaje">
              <option value="">Selecciona</option>
              {rutas.map((ruta) => (
                <option key={ruta.id} value={ruta.id}>
                  {ruta.origen} → {ruta.destino} · {ruta.duracion_min} min · {formatearPesos(ruta.precio_base)}
                </option>
              ))}
            </select>
          </label>
          <label>
            Bus
            <select name="bus_id" defaultValue="" aria-label="Bus del viaje">
              <option value="">Selecciona</option>
              {buses.map((bus) => (
                <option key={bus.id} value={bus.id} disabled={bus.estado !== 'operativo'}>
                  Disco {bus.numero_disco} · {bus.placa} · {bus.capacidad} puestos · {bus.estado}
                </option>
              ))}
            </select>
          </label>
          <label>
            Salida
            <input type="datetime-local" name="salida" aria-label="Fecha y hora de salida" />
          </label>
          <label>
            Precio (opcional, usa la tarifa de la ruta)
            <input type="number" name="precio" min="1" step="0.01" aria-label="Precio del viaje" />
          </label>
          <button type="submit" className="btn btn-arcilla" disabled={ocupado} aria-label="Crear viaje">Crear viaje</button>
        </form>

        <form className="panel-form" noValidate onSubmit={cambiarTarifa}>
          <h2>Cambiar tarifa</h2>
          <label>
            Ruta
            <select name="ruta_id" defaultValue="" aria-label="Ruta a retarifar">
              <option value="">Selecciona</option>
              {rutas.map((ruta) => (
                <option key={ruta.id} value={ruta.id}>
                  {ruta.origen} → {ruta.destino} · hoy {formatearPesos(ruta.precio_base)}
                </option>
              ))}
            </select>
          </label>
          <label>
            Nueva tarifa base
            <input type="number" name="precio_base" min="0.01" step="0.01" aria-label="Nueva tarifa base" />
          </label>
          <button type="submit" className="btn btn-pino" disabled={ocupado} aria-label="Actualizar tarifa">Actualizar tarifa</button>
        </form>
      </div>

      <section className="panel-form">
        <h2>Horario recurrente</h2>
        <p className="meta">Cada par de ciudades tiene dos salidas al día. Generar completa los próximos 30 días y no duplica las que ya existen.</p>
        <button type="button" className="btn btn-pino" onClick={generarHorario} disabled={ocupado} aria-label="Generar salidas de los próximos 30 días">
          Generar salidas
        </button>
      </section>

      <section className="panel-form">
        <h2>Viajes próximos</h2>
        <ul className="lista-admin">
          {viajes.length ? viajes.map((viaje) => (
            <li key={viaje.id}>
              <strong>{viaje.origen} → {viaje.destino}</strong>
              <span>
                {formatearFechaHora(viaje.salida)} · disco {viaje.numero_disco} · {formatearPesos(viaje.precio)} · {viaje.estado}
              </span>
              {viaje.estado === 'programado' && (
                <div>
                  <button type="button" onClick={() => cancelarViaje(viaje)} disabled={ocupado} aria-label={`Cancelar viaje ${viaje.id}`}>
                    Cancelar
                  </button>
                </div>
              )}
            </li>
          )) : <li>No hay viajes en la ventana reciente.</li>}
        </ul>
      </section>

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
                  <td data-label="Ruta">{fila.origen} → {fila.destino}</td>
                  <td data-label="Boletos">{fila.boletos_pagados}</td>
                  <td data-label="Total">{formatearPesos(fila.total)}</td>
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
    </div>
  );
}
