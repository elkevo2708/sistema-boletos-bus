import { useEffect, useState } from 'react';
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom';
import { solicitar } from '../api';
import { useAuth } from '../contexto/AuthContext';
import { IDIOMAS, MENU_EXTRA, MENU_PORTAL, Search, UserRound } from '../iconosTurismo';
import MarcaPortal from './MarcaPortal';

export default function PortalLayout() {
  const [menu, setMenu] = useState(false);
  const [conteos, setConteos] = useState({});
  const [consulta, setConsulta] = useState('');
  const [idioma, setIdioma] = useState(() => localStorage.getItem('lamana_idioma') || 'es');
  const { usuario } = useAuth();
  const navegar = useNavigate();
  const textos = IDIOMAS[idioma] || IDIOMAS.es;

  useEffect(() => {
    solicitar('/turismo/resumen')
      .then((data) => setConteos(data.conteos || {}))
      .catch(() => {});
  }, []);

  useEffect(() => {
    document.documentElement.lang = idioma === 'en' ? 'en' : 'es';
    localStorage.setItem('lamana_idioma', idioma);
  }, [idioma]);

  function cerrar() {
    setMenu(false);
  }

  function buscar(event) {
    event.preventDefault();
    const q = consulta.trim();
    navegar(q ? `/explorar?q=${encodeURIComponent(q)}` : '/explorar');
    cerrar();
  }

  const totalFichas = Object.entries(conteos)
    .filter(([clave]) => !['transporte', 'taxi', 'evento'].includes(clave))
    .reduce((suma, [, valor]) => suma + Number(valor || 0), 0);

  function badge(item) {
    if (item.conteo === 'lamana') return totalFichas;
    return conteos[item.tipo] || 0;
  }

  const destinoLogin = usuario?.rol === 'conductor'
    ? '/conductor'
    : usuario?.rol === 'cliente'
      ? '/mis-facturas'
      : usuario
        ? '/admin'
        : '/ingresar';

  function enlaces(clase) {
    return MENU_PORTAL.map((item) => (
      <NavLink key={item.to} className={clase} to={item.to} end={item.fin} onClick={cerrar}>
        <item.Icono size={22} strokeWidth={1.75} aria-hidden="true" />
        <span>{textos[item.clave]}</span>
        <small>{badge(item)}</small>
      </NavLink>
    ));
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
              placeholder={textos.buscar}
              aria-label={textos.buscar}
            />
          </form>
          <label className="portal-idioma">
            <span aria-hidden="true">ES</span>
            <select value={idioma} onChange={(e) => setIdioma(e.target.value)} aria-label="Idioma">
              <option value="es">ES</option>
              <option value="en">EN</option>
            </select>
          </label>
          <nav className="portal-nav" aria-label="Secciones del portal">
            {enlaces()}
            <Link className="portal-login" to={destinoLogin} onClick={cerrar}>
              <UserRound size={22} strokeWidth={1.75} aria-hidden="true" />
              <span>{usuario ? usuario.nombre : textos.login}</span>
            </Link>
          </nav>
        </div>
        {menu && (
          <>
            <button type="button" className="drawer-fondo" aria-label="Cerrar menú" onClick={cerrar} />
            <div className="portal-desplegable abierto">
              <form className="portal-buscar" onSubmit={buscar} role="search">
                <Search size={18} aria-hidden="true" />
                <input
                  value={consulta}
                  onChange={(e) => setConsulta(e.target.value)}
                  placeholder={textos.buscar}
                  aria-label={textos.buscar}
                />
              </form>
              <div className="portal-movil-items">{enlaces('portal-item-movil')}</div>
              {MENU_EXTRA.map((item) => (
                <Link key={item.to} to={item.to} onClick={cerrar}>
                  <item.Icono size={18} strokeWidth={1.75} aria-hidden="true" /> {item.label}
                </Link>
              ))}
              <Link className="portal-item-movil" to={destinoLogin} onClick={cerrar}>
                <UserRound size={18} strokeWidth={1.75} aria-hidden="true" />
                <span>{usuario ? usuario.nombre : textos.login}</span>
              </Link>
            </div>
          </>
        )}
      </header>
      <main id="contenido">
        <Outlet />
      </main>
      <footer className="portal-pie">
        <div className="contenedor portal-pie-grid">
          <div>
            <MarcaPortal />
            <p>Guía del cantón La Maná, en el subtrópico de Cotopaxi. Los textos se editan en el panel.</p>
          </div>
          <div>
            <p className="pie-titulo">Recorrer</p>
            {MENU_EXTRA.map((item) => (
              <p key={item.to}><Link to={item.to}>{item.label}</Link></p>
            ))}
          </div>
          <div>
            <p className="pie-titulo">Servicios</p>
            <p><Link to="/transporte">Transporte</Link></p>
            <p><Link to="/taxi">Taxi</Link></p>
            <p><Link to="/admin">Panel</Link></p>
          </div>
          <div>
            <p className="pie-titulo">Contacto</p>
            <p><Link to="/contacto">Escribir al portal</Link></p>
            <p><a href="mailto:turismo@lamana.ec">turismo@lamana.ec</a></p>
          </div>
        </div>
      </footer>
      <p className="portal-base">© 2026 La Maná Recorres. El transporte conserva su propia marca.</p>
    </div>
  );
}
