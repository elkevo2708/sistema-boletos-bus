import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { solicitar } from '../api';
import TarjetaTurismo from '../componentes/TarjetaTurismo';
import { EncabezadoPagina, Esqueleto, EstadoVacio, Paginacion } from '../ui/ui';

const POR_PAGINA = 9;

export default function PortalLista({ tipo, titulo, bajada, imagen }) {
  const [params, setParams] = useSearchParams();
  const categoria = params.get('categoria') || '';
  const pagina = Math.max(1, Number(params.get('pagina') || 1));
  const [fichas, setFichas] = useState(null);
  const [categorias, setCategorias] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    const consulta = new URLSearchParams({ tipo });
    if (categoria) consulta.set('categoria', categoria);
    setFichas(null);
    solicitar(`/turismo/fichas?${consulta}`)
      .then(setFichas)
      .catch((err) => setError(err.message));
    solicitar(`/turismo/categorias?tipo=${tipo}`).then(setCategorias).catch(() => {});
  }, [tipo, categoria]);

  const total = fichas ? Math.max(1, Math.ceil(fichas.length / POR_PAGINA)) : 1;
  const visibles = (fichas || []).slice((pagina - 1) * POR_PAGINA, pagina * POR_PAGINA);

  function ir(siguiente) {
    const datos = {};
    if (categoria) datos.categoria = categoria;
    if (siguiente > 1) datos.pagina = String(siguiente);
    setParams(datos);
  }

  return (
    <>
      <EncabezadoPagina titulo={titulo} bajada={bajada} imagen={imagen} />
      <section className="portal-bloque">
        {categorias.length > 0 && (
          <div className="portal-chips" role="list">
            <Link to={window.location.pathname} className={!categoria ? 'activo' : ''}>Todo</Link>
            {categorias.map((item) => (
              <Link key={item.id} to={`?categoria=${item.slug}`} className={categoria === item.slug ? 'activo' : ''}>{item.nombre}</Link>
            ))}
          </div>
        )}
        {error && <p className="aviso" role="alert">{error}</p>}
        {!fichas && !error && <Esqueleto />}
        <div className="rejilla-turismo">
          {visibles.map((ficha) => <TarjetaTurismo key={ficha.id} ficha={ficha} />)}
        </div>
        {fichas && fichas.length === 0 && !error && (
          <EstadoVacio titulo="Todavía no hay fichas" texto="Cuando el panel publique una, aparece en esta sección." />
        )}
        <Paginacion pagina={Math.min(pagina, total)} total={fichas ? total : 1} onCambio={ir} />
      </section>
    </>
  );
}
