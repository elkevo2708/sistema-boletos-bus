import { Link } from 'react-router-dom';
import LogoRecorres from '../ui/LogoRecorres';

export default function MarcaPortal({ compacta = false, clara = false }) {
  return (
    <Link className={compacta ? 'marca-portal compacta' : 'marca-portal'} to="/" aria-label="La Maná Recorres, inicio">
      <LogoRecorres variante="isotipo" clara={clara} decorativo />
      <span className="marca-leyenda">
        <strong>La Maná</strong>
        <small>El cantón te espera</small>
      </span>
    </Link>
  );
}
