import { useEffect } from 'react';

export default function Lightbox({ imagenes, indice, onCerrar, onMover }) {
  const actual = imagenes[indice];

  useEffect(() => {
    function tecla(evento) {
      if (evento.key === 'Escape') onCerrar();
      if (evento.key === 'ArrowRight') onMover(1);
      if (evento.key === 'ArrowLeft') onMover(-1);
    }
    window.addEventListener('keydown', tecla);
    return () => window.removeEventListener('keydown', tecla);
  }, [onCerrar, onMover]);

  if (!actual) return null;

  return (
    <div className="velo" role="presentation" onClick={onCerrar}>
      <div
        className="lightbox"
        role="dialog"
        aria-modal="true"
        aria-label={actual.titulo}
        onClick={(evento) => evento.stopPropagation()}
      >
        <button type="button" className="cerrar" onClick={onCerrar} aria-label="Cerrar galería">Cerrar</button>
        <button type="button" onClick={() => onMover(-1)} aria-label="Imagen anterior">Anterior</button>
        <figure>
          <img src={actual.url} alt={actual.descripcion || actual.titulo} />
          <figcaption>
            <strong>{actual.titulo}</strong>
            {actual.descripcion && <span>{actual.descripcion}</span>}
          </figcaption>
        </figure>
        <button type="button" onClick={() => onMover(1)} aria-label="Imagen siguiente">Siguiente</button>
      </div>
    </div>
  );
}
