import { Link } from 'react-router-dom';
import { RUTA_TIPO } from '../iconosTurismo';

export default function TarjetaTurismo({ ficha }) {
  const base = RUTA_TIPO[ficha.tipo] || '/atractivos';
  return (
    <article className="tarjeta-turismo">
      <Link to={`${base}/${ficha.slug}`}>
        {ficha.imagen ? (
          <img src={ficha.imagen} alt="" />
        ) : (
          <span className="tarjeta-vacia" aria-hidden="true">{ficha.zona || 'La Maná'}</span>
        )}
        <div>
          {ficha.categoria && <p className="sobrelinea">{ficha.categoria}</p>}
          <h3>{ficha.nombre}</h3>
          <p>{ficha.resumen}</p>
        </div>
      </Link>
    </article>
  );
}
