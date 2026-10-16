import { useEffect, useState } from 'react';
import { solicitar, traerArchivo } from '../api';
import { formatearFechaHora, formatearPesos } from '../formato';

const ESTADOS = ['', 'generada', 'firmada', 'autorizada', 'rechazada'];

export function PanelFacturas({ token }) {
  const [filtro, setFiltro] = useState({ estado: '', identificacion: '', desde: '', hasta: '' });
  const [facturas, setFacturas] = useState([]);
  const [error, setError] = useState('');
  const [aviso, setAviso] = useState('');

  async function cargar(event) {
    event?.preventDefault();
    const params = new URLSearchParams();
    Object.entries(filtro).forEach(([clave, valor]) => {
      if (valor) params.set(clave, valor);
    });
    const consulta = params.toString();
    try {
      setFacturas(await solicitar(`/admin/facturas${consulta ? `?${consulta}` : ''}`, { token }));
      setError('');
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    cargar();
  }, [token]);

  async function descargar(factura, tipo) {
    const blob = await traerArchivo(`/admin/facturas/${factura.id}/${tipo}`, token);
    const url = URL.createObjectURL(blob);
    const enlace = document.createElement('a');
    enlace.href = url;
    enlace.download = `${tipo === 'ride' ? 'RIDE' : 'Factura'}-${factura.numero}.${tipo === 'ride' ? 'pdf' : 'xml'}`;
    enlace.click();
    URL.revokeObjectURL(url);
  }

  async function reenviar(factura) {
    setAviso('');
    setError('');
    try {
      const actual = await solicitar(`/admin/facturas/${factura.id}/reenviar`, { method: 'POST', token });
      setAviso(`Factura ${actual.numero} en estado ${actual.estado}.`);
      await cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section className="panel-form">
      <h2>Facturas</h2>
      <form className="filtros-factura" onSubmit={cargar}>
        <label>
          Estado
          <select value={filtro.estado} onChange={(e) => setFiltro({ ...filtro, estado: e.target.value })} aria-label="Filtrar por estado">
            {ESTADOS.map((estado) => (
              <option key={estado || 'todas'} value={estado}>{estado || 'Todas'}</option>
            ))}
          </select>
        </label>
        <label>
          Identificación
          <input value={filtro.identificacion} onChange={(e) => setFiltro({ ...filtro, identificacion: e.target.value })} aria-label="Filtrar por identificación" />
        </label>
        <label>
          Desde
          <input type="date" value={filtro.desde} onChange={(e) => setFiltro({ ...filtro, desde: e.target.value })} aria-label="Fecha desde" />
        </label>
        <label>
          Hasta
          <input type="date" value={filtro.hasta} onChange={(e) => setFiltro({ ...filtro, hasta: e.target.value })} aria-label="Fecha hasta" />
        </label>
        <button type="submit" className="btn btn-pino" aria-label="Filtrar facturas">Filtrar</button>
      </form>
      {aviso && <p className="aviso-ok" role="status">{aviso}</p>}
      {error && <p className="aviso" role="alert">{error}</p>}
      <div className="tabla-wrap">
        <table>
          <caption>Comprobantes emitidos</caption>
          <thead>
            <tr>
              <th>Número</th>
              <th>Comprador</th>
              <th>Pasaje</th>
              <th>Total</th>
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {facturas.length ? facturas.map((factura) => (
              <tr key={factura.id}>
                <td>
                  {factura.numero}<br />
                  <span className="meta">{formatearFechaHora(factura.fecha_emision)}</span>
                </td>
                <td>
                  {factura.razon_social_comprador}<br />
                  <span className="meta">{factura.identificacion_comprador}</span>
                </td>
                <td>{factura.ruta} · asiento {factura.asiento}</td>
                <td>{formatearPesos(factura.total)}</td>
                <td><span className={`estado estado-${factura.estado}`}>{factura.estado}</span></td>
                <td className="acciones-factura">
                  <button type="button" onClick={() => reenviar(factura)} aria-label={`Reenviar factura ${factura.numero}`}>Reenviar</button>
                  <button type="button" onClick={() => descargar(factura, 'xml')} aria-label={`Descargar XML ${factura.numero}`}>XML</button>
                  <button type="button" onClick={() => descargar(factura, 'ride')} aria-label={`Descargar RIDE ${factura.numero}`}>RIDE</button>
                </td>
              </tr>
            )) : (
              <tr>
                <td colSpan={6}>No hay facturas con ese filtro.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export function PanelEmisor({ token }) {
  const [emisor, setEmisor] = useState(null);
  const [error, setError] = useState('');
  const [aviso, setAviso] = useState('');

  useEffect(() => {
    solicitar('/admin/emisor', { token }).then(setEmisor).catch((err) => setError(err.message));
  }, [token]);

  async function guardar(event) {
    event.preventDefault();
    const datos = new FormData(event.currentTarget);
    setError('');
    setAviso('');
    try {
      const guardado = await solicitar('/admin/emisor', {
        method: 'PUT',
        token,
        body: {
          ruc: datos.get('ruc'),
          razon_social: datos.get('razon_social'),
          nombre_comercial: datos.get('nombre_comercial'),
          establecimiento: datos.get('establecimiento'),
          punto_emision: datos.get('punto_emision'),
          direccion_matriz: datos.get('direccion_matriz'),
          obligado_contabilidad: datos.get('obligado_contabilidad') === 'on',
          ambiente: datos.get('ambiente'),
          tarifa_iva_pasaje: datos.get('tarifa_iva_pasaje'),
        },
      });
      setEmisor(guardado);
      setAviso('Datos del emisor actualizados. El secuencial no se reinicia.');
    } catch (err) {
      setError(err.message);
    }
  }

  if (!emisor) return error ? <p className="aviso" role="alert">{error}</p> : <p>Cargando emisor…</p>;

  return (
    <form className="panel-form panel-corto" onSubmit={guardar}>
      <h2>Emisor</h2>
      <p className="meta">Secuencial actual {emisor.secuencial}. El siguiente comprobante usa el número siguiente, con bloqueo de fila.</p>
      <label>
        RUC
        <input name="ruc" required defaultValue={emisor.ruc} minLength={13} maxLength={13} aria-label="RUC del emisor" />
      </label>
      <label>
        Razón social
        <input name="razon_social" required defaultValue={emisor.razon_social} aria-label="Razón social del emisor" />
      </label>
      <label>
        Nombre comercial
        <input name="nombre_comercial" required defaultValue={emisor.nombre_comercial} aria-label="Nombre comercial" />
      </label>
      <div className="dos">
        <label>
          Establecimiento
          <input name="establecimiento" required defaultValue={emisor.establecimiento} aria-label="Establecimiento" />
        </label>
        <label>
          Punto de emisión
          <input name="punto_emision" required defaultValue={emisor.punto_emision} aria-label="Punto de emisión" />
        </label>
      </div>
      <label>
        Dirección matriz
        <input name="direccion_matriz" required defaultValue={emisor.direccion_matriz} aria-label="Dirección matriz" />
      </label>
      <label>
        Ambiente
        <select name="ambiente" defaultValue={emisor.ambiente} aria-label="Ambiente SRI">
          <option value="pruebas">Pruebas</option>
          <option value="produccion">Producción</option>
        </select>
      </label>
      <label>
        IVA del pasaje (%)
        <input name="tarifa_iva_pasaje" type="number" min="0" max="100" step="0.01" required defaultValue={emisor.tarifa_iva_pasaje} aria-label="Tarifa de IVA del pasaje" />
      </label>
      <label className="check">
        <input type="checkbox" name="obligado_contabilidad" defaultChecked={Boolean(Number(emisor.obligado_contabilidad))} />
        Obligado a llevar contabilidad
      </label>
      {aviso && <p className="aviso-ok" role="status">{aviso}</p>}
      {error && <p className="aviso" role="alert">{error}</p>}
      <button type="submit" className="btn btn-arcilla" aria-label="Guardar emisor">Guardar emisor</button>
    </form>
  );
}
