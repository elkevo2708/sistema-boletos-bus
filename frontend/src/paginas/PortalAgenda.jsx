import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { solicitar } from '../api';

export function fechaLarga(iso) {
  if (!iso) return '';
  return new Intl.DateTimeFormat('es-EC', {
    day: 'numeric', month: 'long', year: 'numeric', timeZone: 'America/Guayaquil',
  }).format(new Date(`${iso}T12:00:00`));
}

export default function PortalAgenda() {
  const [eventos, setEventos] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    solicitar('/turismo/eventos').then(setEventos).catch((err) => setError(err.message));
  }, []);

  return (
    <section className="portal-bloque">
      <div className="portal-encabezado">
        <p className="sobrelinea">La Maná</p>
        <h1>Agenda</h1>
        <p className="lead">Fechas que taquilla publica. El programa fino de cada año se edita aquí, no se inventa.</p>
      </div>
      {error && <p className="aviso" role="alert">{error}</p>}
      <ul className="portal-agenda">
        {eventos.map((evento) => (
          <li key={evento.id}>
            <time dateTime={evento.inicio}>{fechaLarga(evento.inicio)}</time>
            <div>
              <h2><Link to={`/agenda/${evento.slug}`}>{evento.titulo}</Link></h2>
              <p>{evento.resumen}</p>
              {evento.lugar && <p className="meta">{evento.lugar}</p>}
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}

export function PortalEvento() {
  const { slug } = useParams();
  const [evento, setEvento] = useState(null);
  const [error, setError] = useState('');
  useEffect(() => {
    solicitar(`/turismo/eventos/${slug}`).then(setEvento).catch((err) => setError(err.message));
  }, [slug]);
  if (error) return <p className="portal-bloque aviso">{error}</p>;
  if (!evento) return <p className="portal-bloque">Cargando evento…</p>;
  return (
    <article className="portal-bloque ficha-turismo">
      <p className="miga"><Link to="/agenda">Agenda</Link> / {evento.titulo}</p>
      {evento.imagen && <img src={evento.imagen} alt="" />}
      <h1>{evento.titulo}</h1>
      <p className="lead">{fechaLarga(evento.inicio)}{evento.lugar ? ` · ${evento.lugar}` : ''}</p>
      {evento.cuerpo.split(/\n\n+/).map((parrafo) => <p key={parrafo.slice(0, 24)}>{parrafo}</p>)}
      {evento.credito && <p className="meta">Imagen: {evento.credito}</p>}
    </article>
  );
}
