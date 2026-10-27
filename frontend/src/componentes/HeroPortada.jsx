import { useEffect, useState } from 'react';
import { solicitar } from '../api';

const RESPALDO_BUS = {
  id: 'respaldo',
  tipo: 'imagen',
  url: '/bus-lamana.jpg',
  incrustado: null,
  poster: '/bus-lamana.jpg',
  titulo: 'Viaja desde La Maná con el asiento ya elegido.',
  subtitulo: 'Salidas a Quevedo, Latacunga, Quito, Ambato y Guayaquil. Reserva en línea y aborda con tu código QR.',
  texto_boton: '',
  enlace_boton: '',
};

const RESPALDO_PORTAL = {
  id: 'respaldo-portal',
  tipo: 'imagen',
  url: '/turismo/panoramica.jpg',
  incrustado: null,
  poster: '/turismo/panoramica.jpg',
  titulo: 'La Maná abre el subtrópico de Cotopaxi.',
  subtitulo: 'Río, cascadas, cacao y banano. El bus de la cooperativa sigue en Transporte.',
  texto_boton: 'Ver atractivos',
  enlace_boton: '/atractivos',
};

export function incrustarVideo(enlace) {
  const texto = enlace || '';
  const youtube = texto.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/shorts\/)([\w-]{6,})/);
  if (youtube) {
    const video = youtube[1];
    return `https://www.youtube-nocookie.com/embed/${video}?autoplay=1&mute=1&loop=1&playlist=${video}&controls=0&playsinline=1&rel=0`;
  }
  const vimeo = texto.match(/vimeo\.com\/(?:video\/)?(\d+)/);
  if (vimeo) return `https://player.vimeo.com/video/${vimeo[1]}?autoplay=1&muted=1&loop=1&background=1`;
  return '';
}

export function MedioHero({ slide }) {
  if (!slide) return <img src="/bus-lamana.jpg" alt="" />;
  if (slide.tipo === 'video' && slide.incrustado) {
    return (
      <iframe
        src={slide.incrustado}
        title={slide.titulo || 'Video de la portada'}
        allow="autoplay; encrypted-media; picture-in-picture"
        tabIndex={-1}
      />
    );
  }
  if (slide.tipo === 'video' && slide.url) {
    return (
      <video
        key={slide.url}
        autoPlay
        muted
        loop
        playsInline
        poster={slide.poster || '/bus-lamana.jpg'}
      >
        <source src={slide.url} />
      </video>
    );
  }
  return <img src={slide.url || '/bus-lamana.jpg'} alt="" />;
}

export default function HeroPortada({ children, ambito = 'portal' }) {
  const respaldo = ambito === 'transporte' ? RESPALDO_BUS : RESPALDO_PORTAL;
  const [slides, setSlides] = useState([respaldo]);
  const [indice, setIndice] = useState(0);

  useEffect(() => {
    solicitar(`/portada?ambito=${ambito}`)
      .then((lista) => {
        if (Array.isArray(lista) && lista.length) setSlides(lista);
        else setSlides([respaldo]);
      })
      .catch(() => setSlides([respaldo]));
  }, [ambito]);

  useEffect(() => {
    if (slides.length < 2) return undefined;
    const reloj = setInterval(() => {
      setIndice((actual) => (actual + 1) % slides.length);
    }, 8000);
    return () => clearInterval(reloj);
  }, [slides.length]);

  const slide = slides[Math.min(indice, slides.length - 1)] || respaldo;

  function mover(delta) {
    setIndice((actual) => (actual + delta + slides.length) % slides.length);
  }

  return (
    <section className="hero">
      <div className="hero-medio" aria-hidden="true">
        <MedioHero slide={slide} />
      </div>
      <div className="hero-velo" />
      <div className="hero-contenido">
        <div className="hero-texto">
          <p className="sobrelinea">
            {ambito === 'transporte' ? 'Cotopaxi · Los Ríos · Sierra y costa' : 'Cantón La Maná · Cotopaxi'}
          </p>
          <h1>{slide.titulo}</h1>
          {slide.subtitulo && <p className="lead">{slide.subtitulo}</p>}
          {slide.texto_boton && slide.enlace_boton && (
            <a className={ambito === 'portal' ? 'btn btn-portal hero-cta' : 'btn btn-arcilla hero-cta'} href={slide.enlace_boton}>
              {slide.texto_boton}
            </a>
          )}
        </div>
        {children}
        {slides.length > 1 && (
          <div className="hero-controles" aria-label="Diapositivas de la portada">
            <button type="button" onClick={() => mover(-1)} aria-label="Diapositiva anterior">‹</button>
            {slides.map((item, posicion) => (
              <button
                key={item.id}
                type="button"
                className={posicion === indice ? 'punto activo' : 'punto'}
                aria-label={`Ver diapositiva ${posicion + 1}`}
                aria-current={posicion === indice}
                onClick={() => setIndice(posicion)}
              />
            ))}
            <button type="button" onClick={() => mover(1)} aria-label="Diapositiva siguiente">›</button>
          </div>
        )}
      </div>
    </section>
  );
}
