export default function CuerpoAnuncio({ anuncio, imagen }) {
  const foto = imagen || anuncio.imagen;
  const esImagen = anuncio.formato === 'imagen';
  return (
    <div className="modal vista-anuncio">
      <p className="sobrelinea">Promoción</p>
      <h2>{anuncio.titulo || 'Título'}</h2>
      {esImagen && foto && <img className="promo-imagen" src={foto} alt={anuncio.titulo || 'Promoción'} />}
      {esImagen && !foto && <p className="meta">La imagen se verá aquí.</p>}
      {!esImagen && <p>{anuncio.mensaje || 'Mensaje de la promoción'}</p>}
      {anuncio.enlace && <span className="btn btn-oro">{anuncio.texto_boton || 'Ver más'}</span>}
    </div>
  );
}