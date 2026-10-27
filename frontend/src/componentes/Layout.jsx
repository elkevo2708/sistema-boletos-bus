import { useState } from 'react';
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom';
import { solicitar } from '../api';
import { useAuth } from '../contexto/AuthContext';
import Anuncios from './Anuncios';
import Marca from './Marca';

export default function Layout() {
  const { usuario, refreshToken, cerrar } = useAuth();
  const navegar = useNavigate();
  const [menu, setMenu] = useState(false);

  async function salir() {
    if (refreshToken) {
      try {
        await solicitar('/auth/logout', { method: 'POST', body: { refresh_token: refreshToken } });
      } catch {
        /* la sesión local se cierra igual */
      }
    }
    cerrar();
    navegar('/transporte');
  }

  function cerrarMenu() {
    setMenu(false);
  }

  return (
    <>
      <a className="saltar" href="#contenido">Saltar al contenido</a>
      <div className="cabecera-fija">
        <div className="barra-util">
          <p>
            <a href="tel:+593994127992">Matriz 099 412 7992</a>
            <span aria-hidden="true"> · </span>
            <a href="tel:+593980405468">Quevedo 098 040 5468</a>
            <span aria-hidden="true"> · </span>
            <a href="tel:+593991175522">Guayaquil 099 117 5522</a>
            <span aria-hidden="true"> · </span>
            <a href="tel:+593991172085">Durán 099 117 2085</a>
          </p>
          <p>Taquilla 05:00–21:00 · <a href="mailto:reservas@lamana.ec">reservas@lamana.ec</a></p>
        </div>
        <header className="cabecera">
          <Marca />
          <button
            type="button"
            className="menu-btn"
            aria-expanded={menu}
            aria-label={menu ? 'Cerrar menú' : 'Abrir menú'}
            onClick={() => setMenu((abierto) => !abierto)}
          >
            <span />
            <span />
            <span />
          </button>
          <nav className={menu ? 'nav abierto' : 'nav'} aria-label="Principal">
            <NavLink to="/transporte" end onClick={cerrarMenu}>Inicio</NavLink>
            <Link to={{ pathname: '/transporte', hash: 'rutas' }} onClick={cerrarMenu}>Rutas</Link>
            <Link to={{ pathname: '/transporte', hash: 'destinos' }} onClick={cerrarMenu}>Destinos</Link>
            <NavLink to="/transporte/encomiendas" onClick={cerrarMenu}>Encomiendas</NavLink>
            <NavLink to="/transporte/noticias" onClick={cerrarMenu}>Noticias</NavLink>
            <NavLink to="/transporte/galeria" onClick={cerrarMenu}>Galería</NavLink>
            <NavLink to="/" end onClick={cerrarMenu}>Portal</NavLink>
            <NavLink to="/admin" onClick={cerrarMenu}>Taquilla</NavLink>
            {usuario ? (
              <>
                <NavLink to="/mis-facturas" onClick={cerrarMenu}>Mis facturas</NavLink>
                <span className="quien">{usuario.nombre}</span>
                <button type="button" className="enlace-salir" onClick={() => { cerrarMenu(); salir(); }} aria-label="Cerrar sesión">Salir</button>
              </>
            ) : (
              <NavLink to="/ingresar" onClick={cerrarMenu}>Ingresar</NavLink>
            )}
            <Link className="btn btn-arcilla btn-pasaje" to={{ pathname: '/transporte', hash: 'buscar' }} onClick={cerrarMenu}>
              Pasaje en línea
            </Link>
          </nav>
        </header>
      </div>
      <Anuncios />
      <main id="contenido">
        <Outlet />
      </main>
      <footer className="pie">
        <div>
          <img className="logo-pie" src="/logo-lamana.png" alt="Trans La Maná" />
          <p>Salidas diarias desde La Maná hacia la costa y la sierra. El asiento se elige antes de pagar.</p>
        </div>
        <div>
          <p className="pie-titulo">Enlaces</p>
          <p><Link to="/transporte">Inicio</Link></p>
          <p><Link to="/">Portal de turismo</Link></p>
          <p><Link to="/transporte/encomiendas">Encomiendas</Link></p>
          <p><Link to="/transporte/noticias">Noticias</Link></p>
          <p><Link to="/transporte/galeria">Galería</Link></p>
          <p><Link to="/admin">Taquilla</Link></p>
          <p><Link to="/mis-facturas">Mis facturas</Link></p>
        </div>
        <div>
          <p className="pie-titulo">Rutas</p>
          <p><Link to={{ pathname: '/transporte', hash: 'rutas' }}>La Maná – Quevedo</Link></p>
          <p><Link to={{ pathname: '/transporte', hash: 'rutas' }}>La Maná – Latacunga</Link></p>
          <p><Link to={{ pathname: '/transporte', hash: 'rutas' }}>Quevedo – Guayaquil</Link></p>
          <p><Link to={{ pathname: '/transporte', hash: 'rutas' }}>Latacunga – Quito</Link></p>
        </div>
        <div>
          <p className="pie-titulo">Teléfonos</p>
          <p>Matriz La Maná<br /><a href="tel:+593994127992">099 412 7992</a></p>
          <p>Quevedo · <a href="tel:+593980405468">098 040 5468</a></p>
          <p>Guayaquil · <a href="tel:+593991175522">099 117 5522</a></p>
          <p>Durán · <a href="tel:+593991172085">099 117 2085</a></p>
          <p><a href="mailto:reservas@lamana.ec">reservas@lamana.ec</a></p>
          <div className="redes">
            <a href="https://www.facebook.com/" aria-label="Facebook de la cooperativa" target="_blank" rel="noreferrer">Facebook</a>
            <a href="https://www.instagram.com/" aria-label="Instagram de la cooperativa" target="_blank" rel="noreferrer">Instagram</a>
            <a href="https://www.tiktok.com/" aria-label="TikTok de la cooperativa" target="_blank" rel="noreferrer">TikTok</a>
          </div>
        </div>
      </footer>
      <p className="pie-base">© 2026 Cooperativa de Transporte La Maná. Horarios en hora de Ecuador.</p>
      <a className="whatsapp" href="https://wa.me/593994127992" aria-label="Escribir por WhatsApp a la matriz de La Maná" target="_blank" rel="noreferrer">
        <svg viewBox="0 0 24 24" width="28" height="28" aria-hidden="true">
          <path fill="#fff" d="M12 3a8.7 8.7 0 0 0-7.5 13.1L3.5 20.5l4.5-1.2A8.7 8.7 0 1 0 12 3zm4.8 12.3c-.2.6-1.2 1.1-1.6 1.1-.4.1-.9.2-2.9-.6-2.4-1-4-3.5-4.1-3.7-.1-.2-1-1.3-1-2.5s.6-1.8.9-2c.2-.2.5-.3.7-.3h.5c.2 0 .4 0 .6.5.2.6.7 2 .8 2.1.1.2.1.3 0 .5-.1.2-.2.3-.3.5l-.4.5c-.1.1-.3.3-.1.6.2.3.8 1.3 1.7 2.1 1.2 1 2.1 1.3 2.4 1.4.3.1.5.1.6-.1.2-.2.7-.8.9-1.1.2-.3.4-.2.6-.1.2.1 1.6.8 1.9.9.3.2.4.2.5.3.1.2 0 .8-.2 1.4z" />
        </svg>
      </a>
    </>
  );
}
