import { NavLink } from 'react-router-dom';

export default function BarraInferior({ items, etiqueta = 'Navegación principal' }) {
  return (
    <nav className="barra-inferior" aria-label={etiqueta}>
      {items.map((item) => (
        <NavLink key={item.to} to={item.to} end={item.end}>
          <item.Icono size={22} strokeWidth={2.1} aria-hidden="true" />
          <span>{item.label}</span>
        </NavLink>
      ))}
    </nav>
  );
}
