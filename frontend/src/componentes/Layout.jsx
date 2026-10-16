import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { solicitar } from '../api';
import { useAuth } from '../contexto/AuthContext';
import Anuncios from './Anuncios';
import Marca from './Marca';

export default function Layout() {
  const { usuario, refreshToken, cerrar } = useAuth();
  const navegar = useNavigate();

  async function salir() {
    if (refreshToken) {
      try {
        await solicitar('/auth/logout', { method: 'POST', body: { refresh_token: refreshToken } });
      } catch {
        /* la sesión local se cierra igual */
      }
    }
    cerrar();
    navegar('/');
  }

  return (
    <>
      <a className="saltar" href="#contenido">Saltar al contenido</a>
      <header className="cabecera">
        <Marca />
        <nav className="nav" aria-label="Principal">
          <NavLink to="/" end>Salidas</NavLink>
          <NavLink to="/noticias">Noticias</NavLink>
          <NavLink to="/galeria">Galería</NavLink>
          <NavLink to="/admin">Taquilla</NavLink>
          {usuario ? (
            <>
              <span className="quien">{usuario.nombre}</span>
              <button type="button" className="btn btn-fantasma" onClick={salir} aria-label="Cerrar sesión">Salir</button>
            </>
          ) : (
            <NavLink to="/ingresar">Ingresar</NavLink>
          )}
        </nav>
      </header>
      <Anuncios />
      <main id="contenido">
        <Outlet />
      </main>
      <footer className="pie">
        <div>
          <strong>Cooperativa de Transporte La Maná</strong>
          <p>Terminal terrestre, avenida Amazonas y 19 de Mayo. La Maná, Cotopaxi, Ecuador.</p>
          <p>Taquilla de 05:00 a 21:00. Horarios en hora de Ecuador.</p>
        </div>
        <div>
          <p><a href="tel:+59332680142">+593 3 268 0142</a></p>
          <p><a href="mailto:reservas@lamana.ec">reservas@lamana.ec</a></p>
          <p><a href="https://wa.me/593984002210">WhatsApp de taquilla</a></p>
        </div>
        <div className="redes">
          <a href="https://www.facebook.com/" aria-label="Facebook de la cooperativa" target="_blank" rel="noreferrer">Facebook</a>
          <a href="https://www.instagram.com/" aria-label="Instagram de la cooperativa" target="_blank" rel="noreferrer">Instagram</a>
          <a href="https://www.tiktok.com/" aria-label="TikTok de la cooperativa" target="_blank" rel="noreferrer">TikTok</a>
        </div>
      </footer>
    </>
  );
}
