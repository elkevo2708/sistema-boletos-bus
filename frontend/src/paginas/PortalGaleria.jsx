import { useEffect, useState } from 'react';
import { solicitar } from '../api';
import { EncabezadoPagina, Esqueleto, EstadoVacio } from '../ui/ui';

export default function PortalGaleria() {
  const [fotos, setFotos] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    solicitar('/turismo/galeria').then(setFotos).catch((err) => setError(err.message));
  }, []);

  return (
    <>
      <EncabezadoPagina titulo="Galería" bajada="Fotografías libres del cantón y del cultivo. El crédito va debajo de cada una." imagen="/turismo/banano.jpg" />
    <section className="portal-bloque">
      {error && <p className="aviso" role="alert">{error}</p>}
      {!fotos && !error && <Esqueleto />}
      {fotos && fotos.length === 0 && !error && <EstadoVacio titulo="Sin fotos" texto="La galería se llena desde el panel." />}
      <div className="rejilla-galeria-portal">
        {(fotos || []).map((foto) => (
          <figure key={foto.id}>
            <img src={foto.url} alt={foto.titulo} loading="lazy" decoding="async" />
            <figcaption>
              <strong>{foto.titulo}</strong>
              {foto.descripcion && <span>{foto.descripcion}</span>}
              <small>{foto.credito}</small>
            </figcaption>
          </figure>
        ))}
      </div>
    </section>
    </>
  );
}
