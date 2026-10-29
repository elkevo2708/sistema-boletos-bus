import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { solicitar } from '../api';
import { RUTA_TIPO } from '../iconosTurismo';
import { EncabezadoPagina, Esqueleto } from '../ui/ui';

export default function PortalFicha({ tipo, volver }) {
  const { slug } = useParams();
  const [ficha, setFicha] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    setFicha(null);
    setError('');
    solicitar(`/turismo/fichas/${tipo}/${slug}`)
      .then(setFicha)
      .catch((err) => setError(err.message));
  }, [tipo, slug]);

  if (error) return <p className="portal-bloque aviso" role="alert">{error}</p>;
  if (!ficha) return <div className="portal-bloque"><Esqueleto lineas={5} /></div>;
  const base = RUTA_TIPO[tipo] || '/';

  return (
    <>
      <EncabezadoPagina
        kicker={ficha.categoria || ficha.zona || 'La Maná'}
        titulo={ficha.nombre}
        bajada={ficha.resumen}
        imagen={ficha.imagen || '/turismo/panoramica.jpg'}
        miga={<><Link to={base}>{volver}</Link> / {ficha.nombre}</>}
      />
      <article className="ficha-cuerpo">
        {ficha.cuerpo.split(/\n\n+/).map((parrafo) => <p key={parrafo.slice(0, 24)}>{parrafo}</p>)}
        {ficha.direccion && <p><strong>Referencia.</strong> {ficha.direccion}</p>}
        {ficha.credito && <p className="meta">Imagen: {ficha.credito}</p>}
        {tipo === 'ruta' && <p><Link className="btn btn-portal" to="/transporte">Ver salidas de Transporte</Link></p>}
      </article>
    </>
  );
}
