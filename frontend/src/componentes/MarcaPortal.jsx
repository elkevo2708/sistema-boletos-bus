import { Link } from 'react-router-dom';

export default function MarcaPortal({ compacta = false }) {
  return (
    <Link className={compacta ? 'marca-portal compacta' : 'marca-portal'} to="/" aria-label="La Maná Recorres, inicio">
      <img src="/marca-lamana-recorres.png" alt="La Maná Recorres" />
    </Link>
  );
}
