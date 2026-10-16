import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { solicitar } from '../api';

function destino(enlace) {
  if (!enlace) return null;
  if (enlace.startsWith('/')) return enlace;
  return enlace;
}

export default function Anuncios() {
  const [lista, setLista] = useState([]);
  const [modalId, setModalId] = useState(null);

  useEffect(() => {
    solicitar('/anuncios')
      .then((data) => {
        setLista(data);
        const modal = data.find((item) => item.tipo === 'modal' && !sessionStorage.getItem(`lamana_anuncio_${item.id}`));
        if (modal) setModalId(modal.id);
      })
      .catch(() => setLista([]));
  }, []);

  function cerrar(id) {
    sessionStorage.setItem(`lamana_anuncio_${id}`, '1');
    if (modalId === id) setModalId(null);
    setLista((actual) => actual.map((item) => (item.id === id ? { ...item, oculto: true } : item)));
  }

  const banners = lista.filter((item) => item.tipo === 'banner' && !item.oculto && !sessionStorage.getItem(`lamana_anuncio_${item.id}`));
  const modal = lista.find((item) => item.id === modalId);

  return (
    <>
      {banners.map((anuncio) => (
        <div className="banda" key={anuncio.id} role="region" aria-label={anuncio.titulo}>
          <p>
            <strong>{anuncio.titulo}.</strong> {anuncio.mensaje}{' '}
            {anuncio.enlace && (
              anuncio.enlace.startsWith('/')
                ? <Link to={destino(anuncio.enlace)}>Ver detalle</Link>
                : <a href={anuncio.enlace}>Ver detalle</a>
            )}
          </p>
          <button type="button" onClick={() => cerrar(anuncio.id)} aria-label={`Cerrar anuncio ${anuncio.titulo}`}>
            Cerrar
          </button>
        </div>
      ))}
      {modal && (
        <div className="velo" role="presentation">
          <div className="modal" role="dialog" aria-modal="true" aria-labelledby={`anuncio-${modal.id}`}>
            <p className="sobrelinea">Promoción</p>
            <h2 id={`anuncio-${modal.id}`}>{modal.titulo}</h2>
            <p>{modal.mensaje}</p>
            <div className="acciones">
              {modal.enlace?.startsWith('/') && <Link className="btn btn-oro" to={modal.enlace} onClick={() => cerrar(modal.id)}>Ver más</Link>}
              <button type="button" className="btn btn-fantasma" onClick={() => cerrar(modal.id)} aria-label="Cerrar promoción">
                Ahora no
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
