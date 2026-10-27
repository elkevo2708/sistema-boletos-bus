import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { solicitar, traerArchivo } from '../api';
import { useAuth } from '../contexto/AuthContext';
import { formatearFechaHora, formatearPesos } from '../formato';

export default function MisFacturas() {
  const { usuario, token } = useAuth();
  const [facturas, setFacturas] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!token) return;
    solicitar('/facturacion/mias', { token })
      .then(setFacturas)
      .catch((err) => setError(err.message));
  }, [token]);

  async function descargar(factura, tipo) {
    const blob = await traerArchivo(`/facturacion/${factura.id}/${tipo}`, token);
    const url = URL.createObjectURL(blob);
    const enlace = document.createElement('a');
    enlace.href = url;
    enlace.download = `${tipo === 'ride' ? 'RIDE' : 'Factura'}-${factura.numero}.${tipo === 'ride' ? 'pdf' : 'xml'}`;
    enlace.click();
    URL.revokeObjectURL(url);
  }

  if (!usuario) {
    return (
      <div className="pagina estrecha">
        <h1>Mis facturas</h1>
        <p>Ingresa para ver las facturas de tus pasajes.</p>
        <Link className="btn btn-pino" to="/ingresar?siguiente=/mis-facturas">Ingresar</Link>
      </div>
    );
  }

  return (
    <div className="pagina">
      <h1>Mis facturas</h1>
      <p className="lead">Comprobantes emitidos al pagar un pasaje en línea.</p>
      {error && <p className="aviso" role="alert">{error}</p>}
      <div className="tabla-wrap">
        <table>
          <caption>Facturas de {usuario.nombre}</caption>
          <thead>
            <tr>
              <th>Número</th>
              <th>Fecha</th>
              <th>Pasaje</th>
              <th>Total</th>
              <th>Estado</th>
              <th>Archivos</th>
            </tr>
          </thead>
          <tbody>
            {facturas.length ? facturas.map((factura) => (
              <tr key={factura.id}>
                <td data-label="Número">{factura.numero}</td>
                <td data-label="Fecha">{formatearFechaHora(factura.fecha_emision)}</td>
                <td data-label="Pasaje">
                  {factura.ruta}<br />
                  <span className="meta">{formatearFechaHora(factura.salida)} · asiento {factura.asiento} · {factura.pasajero}</span>
                </td>
                <td data-label="Total">{formatearPesos(factura.total)}</td>
                <td data-label="Estado"><span className={`estado estado-${factura.estado}`}>{factura.estado}</span></td>
                <td className="acciones-factura" data-label="Archivos">
                  <button type="button" onClick={() => descargar(factura, 'ride')} aria-label={`Descargar RIDE ${factura.numero}`}>RIDE</button>
                  <button type="button" onClick={() => descargar(factura, 'xml')} aria-label={`Descargar XML ${factura.numero}`}>XML</button>
                </td>
              </tr>
            )) : (
              <tr>
                <td colSpan={6}>Todavía no hay facturas en esta cuenta.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
