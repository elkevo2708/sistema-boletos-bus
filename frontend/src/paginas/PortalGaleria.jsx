import { useEffect, useState } from 'react';
import { solicitar } from '../api';

export default function PortalGaleria() {
  const [fotos, setFotos] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    solicitar('/turismo/galeria').then(setFotos).catch((err) => setError(err.message));
  }, []);

  return (
    <section className="portal-bloque">
      <div className="portal-encabezado">
        <p className="sobrelinea">La Maná</p>
        <h1>Galería</h1>
        <p className="lead">Fotografías libres del cantón y del cultivo. El crédito va debajo de cada una.</p>
      </div>
      {error && <p className="aviso" role="alert">{error}</p>}
      <div className="rejilla-galeria-portal">
        {fotos.map((foto) => (
          <figure key={foto.id}>
            <img src={foto.url} alt={foto.titulo} />
            <figcaption>
              <strong>{foto.titulo}</strong>
              {foto.descripcion && <span>{foto.descripcion}</span>}
              <small>{foto.credito}</small>
            </figcaption>
          </figure>
        ))}
      </div>
    </section>
  );
}
