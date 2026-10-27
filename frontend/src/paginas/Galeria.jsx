import { useEffect, useMemo, useState } from 'react';
import { solicitar } from '../api';
import Lightbox from '../componentes/Lightbox';
import { EncabezadoPagina, EstadoVacio } from '../ui/ui';

const FILTROS = [
  ['', 'Todas'],
  ['buses', 'Buses'],
  ['destinos', 'Destinos'],
  ['terminales', 'Terminales'],
];

export default function Galeria() {
  const [categoria, setCategoria] = useState('');
  const [fotos, setFotos] = useState([]);
  const [abierta, setAbierta] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const ruta = categoria ? `/galeria?categoria=${categoria}` : '/galeria';
    solicitar(ruta).then(setFotos).catch((err) => setError(err.message));
  }, [categoria]);

  const indice = useMemo(
    () => fotos.findIndex((foto) => foto.id === abierta),
    [fotos, abierta],
  );

  function mover(delta) {
    if (!fotos.length) return;
    const siguiente = (indice + delta + fotos.length) % fotos.length;
    setAbierta(fotos[siguiente].id);
  }

  return (
    <>
      <EncabezadoPagina kicker="Transporte" titulo="La cooperativa en el camino." bajada="Buses, destinos y terminales." imagen="/bus-lamana.jpg" />
    <div className="pagina">
      <div className="filtros" role="tablist" aria-label="Filtrar galería">
        {FILTROS.map(([valor, etiqueta]) => (
          <button
            key={etiqueta}
            type="button"
            role="tab"
            aria-selected={categoria === valor}
            className={categoria === valor ? 'activo' : ''}
            onClick={() => setCategoria(valor)}
            aria-label={`Ver ${etiqueta.toLowerCase()}`}
          >
            {etiqueta}
          </button>
        ))}
      </div>
      {error && <p className="aviso" role="alert">{error}</p>}
      <div className="mosaico">
        {fotos.map((foto) => (
          <button
            key={foto.id}
            type="button"
            className="foto"
            onClick={() => setAbierta(foto.id)}
            aria-label={`Ampliar ${foto.titulo}`}
          >
            <img src={foto.url} alt={foto.titulo} loading="lazy" decoding="async" />
            <span>{foto.titulo}</span>
          </button>
        ))}
      </div>
      {indice >= 0 && (
        <Lightbox
          imagenes={fotos}
          indice={indice}
          onCerrar={() => setAbierta(null)}
          onMover={mover}
        />
      )}
      {!error && fotos.length === 0 && <EstadoVacio titulo="Sin fotos" texto="No hay imágenes en esta categoría." />}
    </div>
    </>
  );
}
