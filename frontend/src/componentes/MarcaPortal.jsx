import { Link } from 'react-router-dom';

export default function MarcaPortal() {
  return (
    <Link className="marca-portal" to="/" aria-label="La Maná, portal de turismo, inicio">
      <svg viewBox="0 0 64 64" aria-hidden="true">
        <rect width="64" height="64" rx="14" fill="#0e6b32" />
        <path d="M32 10c8 8 14 14 14 24a14 14 0 0 1-28 0c0-10 6-16 14-24z" fill="#f4c400" />
        <path d="M32 22c3 4 6 7 6 12a6 6 0 0 1-12 0c0-5 3-8 6-12z" fill="#ffffff" />
        <rect x="14" y="48" width="36" height="4" rx="2" fill="#ffffff" />
      </svg>
      <span>
        <strong>La Maná</strong>
        <small>Cotopaxi · turismo</small>
      </span>
    </Link>
  );
}
