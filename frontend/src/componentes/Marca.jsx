import { Link } from 'react-router-dom';

export default function Marca() {
  return (
    <Link className="marca" to="/" aria-label="Ir al inicio de La Maná Recorres">
      <img className="marca-logo" src="/logo-lamana.png" alt="" />
      <span className="marca-leyenda">
        <strong>La Maná</strong>
        <small>Tu asiento, en el bus</small>
      </span>
    </Link>
  );
}
