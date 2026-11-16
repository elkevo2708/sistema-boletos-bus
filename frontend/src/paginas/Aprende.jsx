import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { solicitar } from '../api';
import { EncabezadoPagina, Esqueleto, EstadoVacio, Insignia } from '../ui/ui';

function precio(curso) {
  if (curso.gratis) return 'Gratis';
  return curso.costo != null ? `USD ${Number(curso.costo).toFixed(2)}` : 'Con costo';
}

export function TarjetaCurso({ curso }) {
  return (
    <article className="tarjeta-curso">
      <img src={curso.imagen || '/turismo/panoramica.jpg'} alt="" loading="lazy" decoding="async" />
      <div>
        <p className="meta">{curso.categoria || 'Formación'} · {curso.nivel} · {curso.duracion_horas} h</p>
        <h3><Link to={`/aprende/cursos/${curso.slug}`}>{curso.titulo}</Link></h3>
        <p>{curso.resumen}</p>
        <p className="curso-meta">
          <Insignia tono="turquesa">{curso.modalidad}</Insignia>
          <Insignia tono={curso.gratis ? 'verde' : 'amarillo'}>{precio(curso)}</Insignia>
          {curso.ejemplo && <Insignia>Ejemplo</Insignia>}
        </p>
      </div>
    </article>
  );
}

export default function Aprende() {
  const [resumen, setResumen] = useState(null);
  const [cursos, setCursos] = useState([]);
  const [categoria, setCategoria] = useState('');
  const [q, setQ] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    solicitar('/aprende/resumen').then(setResumen).catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    const params = new URLSearchParams();
    if (categoria) params.set('categoria', categoria);
    if (q.trim()) params.set('q', q.trim());
    const reloj = setTimeout(() => {
      solicitar(`/aprende/cursos?${params}`).then(setCursos).catch((err) => setError(err.message));
    }, 250);
    return () => clearTimeout(reloj);
  }, [categoria, q]);

  const proximos = useMemo(() => resumen?.proximos || [], [resumen]);

  return (
    <>
      <EncabezadoPagina
        kicker="Formación ciudadana"
        titulo="Aprende en La Maná"
        bajada="Cursos y artículos para la ciudadanía. Los marcados como ejemplo no son una oferta oficial."
        imagen="/turismo/parque.jpg"
        miga={<Link to="/">Inicio</Link>}
      />
      <section className="portal-bloque">
        {error && <p className="aviso" role="alert">{error}</p>}
        {!resumen && <Esqueleto lineas={3} />}
        <div className="curso-categorias" role="list">
          <button type="button" className={!categoria ? 'activo' : ''} onClick={() => setCategoria('')}>Todas</button>
          {(resumen?.categorias || []).map((item) => (
            <button key={item.slug} type="button" className={categoria === item.slug ? 'activo' : ''} onClick={() => setCategoria(item.slug)}>
              {item.nombre}
            </button>
          ))}
        </div>
        <form className="portal-buscar portal-buscar-pagina" role="search" onSubmit={(evento) => evento.preventDefault()}>
          <input value={q} onChange={(evento) => setQ(evento.target.value)} placeholder="Buscar un curso" aria-label="Buscar un curso" />
        </form>
        <h2>Cursos</h2>
        {cursos.length === 0 && resumen && <EstadoVacio titulo="No hay cursos con ese filtro" texto="Prueba otra categoría o borra la búsqueda." />}
        <div className="rejilla-cursos">
          {cursos.map((curso) => <TarjetaCurso key={curso.id} curso={curso} />)}
        </div>
        <h2>Próximos inicios</h2>
        <ul className="portal-agenda">
          {proximos.map((curso) => (
            <li key={curso.id}>
              <time dateTime={curso.inicio || ''}>{curso.inicio || 'Fecha por confirmar'}</time>
              <div>
                <h3><Link to={`/aprende/cursos/${curso.slug}`}>{curso.titulo}</Link></h3>
                <p>{curso.modalidad} · {precio(curso)} · {curso.cupos} cupos</p>
              </div>
            </li>
          ))}
        </ul>
        <h2>Conoce La Maná</h2>
        <p className="meta">Artículos de divulgación. No reemplazan un trámite ni un programa municipal.</p>
        <div className="rejilla-cursos">
          {(resumen?.articulos || []).map((nota) => (
            <article key={nota.id} className="tarjeta-curso">
              <div>
                <p className="meta">{nota.categoria}{nota.ejemplo ? ' · ejemplo' : ''}</p>
                <h3><Link to={`/aprende/articulos/${nota.slug}`}>{nota.titulo}</Link></h3>
                <p>{nota.resumen}</p>
              </div>
            </article>
          ))}
        </div>
        <p><Link className="btn btn-portal" to="/aprende/guias">Guías prácticas</Link></p>
      </section>
    </>
  );
}
