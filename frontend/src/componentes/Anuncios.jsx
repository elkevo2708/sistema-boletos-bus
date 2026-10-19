import { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { solicitar } from '../api';

function Boton({ anuncio, onClick }) {
  if (!anuncio.enlace) return null;
  const texto = anuncio.texto_boton || 'Ver más';
  if (anuncio.enlace.startsWith('/')) {
    return <Link className="btn btn-oro" to={anuncio.enlace} onClick={onClick}>{texto}</Link>;
  }
  return (
    <a className="btn btn-oro" href={anuncio.enlace} target="_blank" rel="noreferrer" onClick={onClick}>
      {texto}
    </a>
  );
}

export default function Anuncios() {
  const { pathname } = useLocation();
  const [lista, setLista] = useState([]);
  const [modalId, setModalId] = useState(null);
  const enTaquilla = pathname.startsWith('/admin');

  useEffect(() => {
    solicitar('/anuncios')
      .then((data) => {
        setLista(data);
        const modal = data.find((item) => item.tipo === 'modal' && !sessionStorage.getItem(`lamana_anuncio_${item.id}`));
        if (modal && !window.location.pathname.startsWith('/admin')) setModalId(modal.id);
      })
      .catch(() => setLista([]));
  }, []);

  function cerrar(id) {
    sessionStorage.setItem(`lamana_anuncio_${id}`, '1');
    const siguiente = lista.find(
      (item) => item.tipo === 'modal' && item.id !== id && !sessionStorage.getItem(`lamana_anuncio_${item.id}`),
    );
    setModalId(siguiente && !enTaquilla ? siguiente.id : null);
    setLista((actual) => actual.map((item) => (item.id === id ? { ...item, oculto: true } : item)));
  }

  if (enTaquilla) return null;

  const banners = lista.filter((item) => item.tipo === 'banner' && !item.oculto && !sessionStorage.getItem(`lamana_anuncio_${item.id}`));
  const modal = lista.find((item) => item.id === modalId);
  const esImagen = modal?.formato === 'imagen';

  return (
    <>
      {banners.map((anuncio) => (
        <div className="banda" key={anuncio.id} role="region" aria-label={anuncio.titulo}>
          {anuncio.formato === 'imagen' && anuncio.imagen && (
            <img src={anuncio.imagen} alt="" />
          )}
          <p>
            <strong>{anuncio.titulo}.</strong> {anuncio.formato === 'imagen' ? '' : anuncio.mensaje}{' '}
            <Boton anuncio={anuncio} onClick={() => cerrar(anuncio.id)} />
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
            {esImagen && modal.imagen && <img className="promo-imagen" src={modal.imagen} alt={modal.titulo} />}
            {!esImagen && <p>{modal.mensaje}</p>}
            <div className="acciones">
              <Boton anuncio={modal} onClick={() => cerrar(modal.id)} />
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