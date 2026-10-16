import { Link } from 'react-router-dom';

export default function Marca() {
  return (
    <Link className="marca" to="/" aria-label="Cooperativa de Transporte La Maná, inicio">
      <svg className="marca-logo" viewBox="0 0 64 64" aria-hidden="true">
        <rect width="64" height="64" rx="16" fill="#0f3d32" />
        <path d="M8 44 L22 24 L32 36 L42 18 L56 44 Z" fill="#e4c98a" />
        <path d="M10 48 H54" stroke="#1f6f78" strokeWidth="3" strokeLinecap="round" />
      </svg>
      <span>
        <strong>La Maná</strong>
        <small>Cooperativa de Transporte</small>
      </span>
    </Link>
  );
}
