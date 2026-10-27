import { useEffect, useState } from 'react';
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom';
import { solicitar } from '../api';
import { Bus, MENU_EXTRA, MENU_PORTAL, Search } from '../iconosTurismo';
import MarcaPortal from './MarcaPortal';

export default function PortalLayout() {
  const [menu, setMenu] = useState(false);
  const [conteos, setConteos] = useState({});
  const [consulta, setConsulta] = useState('');
  const navegar = useNavigate();

  useEffect(() => {
    solicitar('/turismo/resumen')
      .then((data) => setConteos(data.conteos || {}))
      .catch(() => {});
  }, []);

  function cerrar() {
    setMenu(false);
  }

  function buscar(event) {
    event.preventDefault();
    const q = consulta.trim();
    navegar(q ? `/explorar?q=${encodeURIComponent(q)}` : '/explorar');
  }

  return (
    <div className="portal">
      <a className="saltar" href="#contenido">Saltar al contenido</a>
      <header className="portal-cabecera">
        <div className="portal-barra">
          <button
            type="button"
            className="menu-btn portal-menu"
            aria-expanded={menu}
            aria-label={menu ? 'Cerrar menú' : 'Abrir menú'}
            onClick={() => setMenu((abierto) => !abierto)}
          >
            <span /><span /><span />
          </button>
          <MarcaPortal />
          <form className="portal-buscar" onSubmit={buscar} role="search">
            <Search size={18} aria-hidden="true" />
            <input
              value={consulta}
              onChange={(e) => setConsulta(e.target.value)}
              placeholder="Buscar en La Maná"
              aria-label="Buscar en el portal"
            />
          </form>
          <Link className="portal-ingreso" to="/ingresar">Ingresar</Link>
        </div>
        <nav className={menu ? 'portal-nav abierto' : 'portal-nav'} aria-label="Secciones del portal">
          {MENU_PORTAL.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.fin} onClick={cerrar}>
              <item.Icono size={22} aria-hidden="true" />
              <span>{item.label}</span>
              {item.tipo && <small>{conteos[item.tipo] || 0}</small>}
            </NavLink>
          ))}
          <Link className="portal-bus" to="/transporte" onClick={cerrar}>
            <Bus size={22} aria-hidden="true" />
            <span>Transporte</span>
          </Link>
        </nav>
      </header>
      <main id="contenido">
        <Outlet />
      </main>
      <footer className="portal-pie">
        <div>
          <MarcaPortal />
          <p>Guía del cantón La Maná, en el subtrópico de Cotopaxi. Los textos se editan en taquilla.</p>
        </div>
        <div>
          <p className="pie-titulo">Recorrer</p>
          {MENU_EXTRA.map((item) => (
            <p key={item.to}><Link to={item.to}>{item.label}</Link></p>
          ))}
          <p><Link to="/explorar">Buscador</Link></p>
        </div>
        <div>
          <p className="pie-titulo">Transporte</p>
          <p><Link to="/transporte">Pasajes de la cooperativa</Link></p>
          <p><Link to="/transporte/encomiendas">Encomiendas</Link></p>
          <p><Link to="/admin">Taquilla</Link></p>
        </div>
        <div>
          <p className="pie-titulo">Contacto</p>
          <p><Link to="/contacto">Escribir al portal</Link></p>
          <p><a href="mailto:turismo@lamana.ec">turismo@lamana.ec</a></p>
          <p className="meta">Las fotos libres llevan crédito en cada ficha. El logo es propio del portal.</p>
        </div>
      </footer>
      <p className="portal-base">© 2026 Portal de turismo de La Maná. El transporte conserva su propia marca.</p>
    </div>
  );
}
