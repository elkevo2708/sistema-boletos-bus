import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { solicitar } from '../api';
import { EncabezadoPagina, Esqueleto, EstadoVacio } from '../ui/ui';

export function fechaLarga(iso) {
  if (!iso) return '';
  return new Intl.DateTimeFormat('es-EC', {
    day: 'numeric', month: 'long', year: 'numeric', timeZone: 'America/Guayaquil',
  }).format(new Date(`${iso}T12:00:00`));
}

export default function PortalAgenda() {
  const [eventos, setEventos] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    solicitar('/turismo/eventos').then(setEventos).catch((err) => setError(err.message));
  }, []);

  return (
    <>
      <EncabezadoPagina titulo="Agenda" bajada="Fechas que taquilla publica. El programa fino de cada año se edita aquí, no se inventa." />
    <section className="portal-bloque">
      {error && <p className="aviso" role="alert">{error}</p>}
      {!eventos && !error && <Esqueleto />}
      {!error && eventos && eventos.length === 0 && <EstadoVacio titulo="Sin fechas publicadas" texto="Cuando haya un evento, aparece en esta lista." />}
      <ul className="portal-agenda">
        {(eventos || []).map((evento) => (
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
    </>
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
  if (!evento) return <div className="portal-bloque"><Esqueleto /></div>;
  return (
    <>
      <EncabezadoPagina
        titulo={evento.titulo}
        bajada={`${fechaLarga(evento.inicio)}${evento.lugar ? ` · ${evento.lugar}` : ''}`}
        imagen={evento.imagen || '/turismo/parque.jpg'}
        miga={<><Link to="/agenda">Agenda</Link> / {evento.titulo}</>}
      />
    <article className="ficha-cuerpo">
      {evento.cuerpo.split(/\n\n+/).map((parrafo) => <p key={parrafo.slice(0, 24)}>{parrafo}</p>)}
      {evento.credito && <p className="meta">Imagen: {evento.credito}</p>}
    </article>
    </>
  );
}
