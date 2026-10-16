import { Link } from 'react-router-dom';

export default function Marca() {
  return (
    <Link className="marca" to="/" aria-label="Cooperativa de Transporte La Maná, inicio">
      <svg className="marca-logo" viewBox="0 0 64 64" aria-hidden="true">
        <rect width="64" height="64" rx="6" fill="#7c2430" />
        <path d="M8 46 L22 26 L32 38 L42 18 L56 46 Z" fill="#e7d3a1" />
        <path d="M10 50 H54" stroke="#ffffff" strokeWidth="3" strokeLinecap="round" />
      </svg>
      <span>
        <strong>La Maná</strong>
        <small>Cooperativa de Transporte</small>
      </span>
    </Link>
  );
}
