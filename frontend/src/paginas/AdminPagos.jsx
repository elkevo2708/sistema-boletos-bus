import { useEffect, useState } from 'react';
import { solicitar } from '../api';

export default function AdminPagos({ token }) {
  const [metodos, setMetodos] = useState([]);
  const [error, setError] = useState('');

  async function cargar() {
    setMetodos(await solicitar('/admin/pagos/metodos', { token }));
  }

  useEffect(() => {
    cargar().catch((err) => setError(err.message));
  }, [token]);

  async function alternar(item) {
    setError('');
    try {
      await solicitar(`/admin/pagos/metodos/${item.codigo}`, {
        method: 'PATCH',
        token,
        body: { activo: !item.activo },
      });
      await cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section className="panel-form">
      <h2>Formas de pago</h2>
      <p className="meta">DeUna!, tarjeta y PayPhone. Sin credenciales el cobro queda en modo de prueba.</p>
      {error && <p className="aviso" role="alert">{error}</p>}
      <ul className="lista-pagos">
        {metodos.map((item) => (
          <li key={item.codigo}>
            <div>
              <strong>{item.nombre}</strong>
              <span className="meta">
                {item.modo === 'live' ? 'En vivo' : 'Prueba'}
                {' · '}
                {item.credenciales_listas ? 'Credenciales listas' : `Falta ${item.faltan.join(', ') || 'configuración'}`}
              </span>
            </div>
            <button
              type="button"
              className="btn btn-pino"
              aria-pressed={item.activo}
              aria-label={`${item.activo ? 'Desactivar' : 'Activar'} ${item.nombre}`}
              onClick={() => alternar(item)}
            >
              {item.activo ? 'Activo' : 'Inactivo'}
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
