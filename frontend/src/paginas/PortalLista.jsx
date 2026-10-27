import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { solicitar } from '../api';
import TarjetaTurismo from '../componentes/TarjetaTurismo';

export default function PortalLista({ tipo, titulo, bajada }) {
  const [params] = useSearchParams();
  const categoria = params.get('categoria') || '';
  const [fichas, setFichas] = useState([]);
  const [categorias, setCategorias] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    const consulta = new URLSearchParams({ tipo });
    if (categoria) consulta.set('categoria', categoria);
    solicitar(`/turismo/fichas?${consulta}`)
      .then(setFichas)
      .catch((err) => setError(err.message));
    solicitar(`/turismo/categorias?tipo=${tipo}`).then(setCategorias).catch(() => {});
  }, [tipo, categoria]);

  return (
    <section className="portal-bloque">
      <div className="portal-encabezado">
        <p className="sobrelinea">La Maná</p>
        <h1>{titulo}</h1>
        {bajada && <p className="lead">{bajada}</p>}
      </div>
      {categorias.length > 0 && (
        <div className="portal-chips" role="list">
          <a href={window.location.pathname} className={!categoria ? 'activo' : ''}>Todo</a>
          {categorias.map((item) => (
            <a key={item.id} href={`?categoria=${item.slug}`} className={categoria === item.slug ? 'activo' : ''}>{item.nombre}</a>
          ))}
        </div>
      )}
      {error && <p className="aviso" role="alert">{error}</p>}
      <div className="rejilla-turismo">
        {fichas.map((ficha) => <TarjetaTurismo key={ficha.id} ficha={ficha} />)}
      </div>
      {!error && fichas.length === 0 && <p>No hay fichas publicadas en esta sección.</p>}
    </section>
  );
}
