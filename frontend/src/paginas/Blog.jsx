import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { solicitar } from '../api';
import { formatearFechaHora } from '../formato';
import { EncabezadoPagina, EstadoVacio } from '../ui/ui';

export default function Blog() {
  const [categoria, setCategoria] = useState('');
  const [notas, setNotas] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    const ruta = categoria ? `/blog?categoria=${categoria}` : '/blog';
    solicitar(ruta).then(setNotas).catch((err) => setError(err.message));
  }, [categoria]);

  return (
    <>
      <EncabezadoPagina kicker="Transporte" titulo="Lo que se mueve en la ruta." bajada="Noticias y destinos de la cooperativa." imagen="/bus-lamana.jpg" miga={<><Link to="/">Inicio</Link> / Noticias</>} />
    <div className="pagina">
      <div className="filtros" role="tablist" aria-label="Filtrar publicaciones">
        {[
          ['', 'Todo'],
          ['noticia', 'Noticias'],
          ['destino', 'Destinos'],
        ].map(([valor, etiqueta]) => (
          <button
            key={etiqueta}
            type="button"
            role="tab"
            aria-selected={categoria === valor}
            className={categoria === valor ? 'activo' : ''}
            onClick={() => setCategoria(valor)}
            aria-label={`Ver ${etiqueta.toLowerCase()}`}
          >
            {etiqueta}
          </button>
        ))}
      </div>
      {error && <p className="aviso" role="alert">{error}</p>}
      <div className="rejilla-notas">
        {notas.map((nota) => (
          <article className="nota" key={nota.id}>
            {nota.imagen && <img src={nota.imagen} alt="" loading="lazy" decoding="async" />}
            <p className="sobrelinea">{nota.categoria} · {formatearFechaHora(nota.publicado_en)}</p>
            <h2><Link to={`/transporte/noticias/${nota.slug}`}>{nota.titulo}</Link></h2>
            <p>{nota.resumen}</p>
          </article>
        ))}
      </div>
      {!error && notas.length === 0 && <EstadoVacio titulo="Sin publicaciones" texto="No hay notas en esta categoría." />}
    </div>
    </>
  );
}
