import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { solicitar } from '../api';
import { RUTA_TIPO } from '../iconosTurismo';

export default function PortalFicha({ tipo, volver }) {
  const { slug } = useParams();
  const [ficha, setFicha] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    setFicha(null);
    solicitar(`/turismo/fichas/${tipo}/${slug}`)
      .then(setFicha)
      .catch((err) => setError(err.message));
  }, [tipo, slug]);

  if (error) return <p className="portal-bloque aviso" role="alert">{error}</p>;
  if (!ficha) return <p className="portal-bloque">Cargando ficha…</p>;
  const base = RUTA_TIPO[tipo] || '/';

  return (
    <article className="portal-bloque ficha-turismo">
      <p className="miga"><Link to={base}>{volver}</Link> / {ficha.nombre}</p>
      {ficha.imagen && <img src={ficha.imagen} alt="" />}
      <p className="sobrelinea">{ficha.categoria || ficha.zona}</p>
      <h1>{ficha.nombre}</h1>
      <p className="lead">{ficha.resumen}</p>
      {ficha.cuerpo.split(/\n\n+/).map((parrafo) => <p key={parrafo.slice(0, 24)}>{parrafo}</p>)}
      {ficha.direccion && <p><strong>Referencia.</strong> {ficha.direccion}</p>}
      {ficha.credito && <p className="meta">Imagen: {ficha.credito}</p>}
      {tipo === 'ruta' && <p><Link className="btn btn-portal" to="/transporte">Ver salidas de Transporte</Link></p>}
    </article>
  );
}
