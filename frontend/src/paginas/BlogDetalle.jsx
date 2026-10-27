import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { solicitar } from '../api';
import { formatearFechaHora } from '../formato';

export default function BlogDetalle() {
  const { slug } = useParams();
  const [nota, setNota] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    setNota(null);
    solicitar(`/blog/${slug}`).then(setNota).catch((err) => setError(err.message));
  }, [slug]);

  if (error) return <p className="pagina aviso" role="alert">{error}</p>;
  if (!nota) return <p className="pagina">Cargando la nota…</p>;

  return (
    <article className="pagina estrecha-larga">
      <p className="miga"><Link to="/transporte/noticias">Noticias</Link> / {nota.categoria}</p>
      <p className="sobrelinea">{formatearFechaHora(nota.publicado_en)}</p>
      <h1>{nota.titulo}</h1>
      <p className="lead">{nota.resumen}</p>
      {nota.imagen && <img className="portada" src={nota.imagen} alt="" />}
      {nota.cuerpo.split(/\n\n+/).map((parrafo) => <p key={parrafo.slice(0, 24)}>{parrafo}</p>)}
    </article>
  );
}
