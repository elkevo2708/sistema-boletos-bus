import { Link } from 'react-router-dom';

export default function Marca() {
  return (
    <Link className="marca" to="/" aria-label="Trans La Maná, Cooperativa de Transporte, inicio">
      <img className="marca-logo" src="/logo-lamana.png" alt="Trans La Maná" />
    </Link>
  );
}
