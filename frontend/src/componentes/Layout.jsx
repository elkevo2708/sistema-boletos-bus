import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom';
import { solicitar } from '../api';
import { useAuth } from '../contexto/AuthContext';

export default function Layout() {
  const { usuario, refreshToken, cerrar } = useAuth();
  const navegar = useNavigate();

  async function salir() {
    if (refreshToken) {
      try {
        await solicitar('/auth/logout', { method: 'POST', body: { refresh_token: refreshToken } });
      } catch {
        /* la sesión local se cierra aunque el token ya no exista */
      }
    }
    cerrar();
    navegar('/');
  }

  return (
    <>
      <a className="saltar" href="#contenido">Saltar al contenido</a>
      <header className="cabecera">
        <Link className="marca" to="/" aria-label="VíaAndina, inicio">
          <span className="marca-sello" aria-hidden="true">VA</span>
          <span>
            <strong>VíaAndina</strong>
            <small>Boletos intermunicipales</small>
          </span>
        </Link>
        <nav className="nav" aria-label="Principal">
          <NavLink to="/" end>Buscar</NavLink>
          <NavLink to="/admin">Taquilla</NavLink>
          {usuario ? (
            <>
              <span className="quien">{usuario.nombre}</span>
              <button type="button" className="btn btn-fantasma" onClick={salir} aria-label="Cerrar sesión">
                Salir
              </button>
            </>
          ) : (
            <NavLink to="/ingresar">Ingresar</NavLink>
          )}
        </nav>
      </header>
      <main id="contenido">
        <Outlet />
      </main>
      <footer className="pie">
        Horarios en hora de Colombia. La reserva de un asiento dura 10 minutos.
      </footer>
    </>
  );
}
