import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { solicitar } from '../api';
import { EncabezadoPagina, Esqueleto, Insignia } from '../ui/ui';

export default function AprendeArticulo() {
  const { slug } = useParams();
  const [nota, setNota] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    solicitar(`/aprende/articulos/${slug}`).then(setNota).catch((err) => setError(err.message));
  }, [slug]);

  if (error) return <p className="pagina aviso" role="alert">{error}</p>;
  if (!nota) return <div className="pagina"><Esqueleto lineas={3} /></div>;

  return (
    <>
      <EncabezadoPagina
        kicker="Conoce La Maná"
        titulo={nota.titulo}
        bajada={nota.resumen}
        miga={<><Link to="/aprende">Aprende</Link> / {nota.titulo}</>}
      />
      <article className="portal-bloque ficha-cuerpo">
        {nota.ejemplo ? <Insignia>Ejemplo</Insignia> : null}
        {String(nota.cuerpo || '').split(/\n\n+/).map((parrafo) => <p key={parrafo.slice(0, 24)}>{parrafo}</p>)}
      </article>
    </>
  );
}
