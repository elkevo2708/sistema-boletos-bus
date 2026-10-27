import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { solicitar } from '../api';
import TarjetaTurismo from '../componentes/TarjetaTurismo';
import { MENU_PORTAL } from '../iconosTurismo';

export default function PortalExplorar() {
  const [params, setParams] = useSearchParams();
  const q = params.get('q') || '';
  const [texto, setTexto] = useState(q);
  const [fichas, setFichas] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    setTexto(q);
    const consulta = q ? `?q=${encodeURIComponent(q)}` : '';
    solicitar(`/turismo/fichas${consulta}`)
      .then(setFichas)
      .catch((err) => setError(err.message));
  }, [q]);

  function enviar(event) {
    event.preventDefault();
    const siguiente = texto.trim();
    setParams(siguiente ? { q: siguiente } : {});
  }

  return (
    <section className="portal-bloque">
      <div className="portal-encabezado">
        <h1>Buscar</h1>
      </div>
      <form className="portal-buscar portal-buscar-pagina" onSubmit={enviar}>
        <input value={texto} onChange={(e) => setTexto(e.target.value)} aria-label="Texto de búsqueda" placeholder="Río, cacao, parroquia…" />
        <button type="submit" className="btn btn-portal">Buscar</button>
      </form>
      <div className="portal-chips">
        {MENU_PORTAL.filter((item) => item.tipo).map((item) => (
          <a key={item.to} href={item.to}>{item.label}</a>
        ))}
      </div>
      {error && <p className="aviso" role="alert">{error}</p>}
      <div className="rejilla-turismo">
        {fichas.map((ficha) => <TarjetaTurismo key={`${ficha.tipo}-${ficha.id}`} ficha={ficha} />)}
      </div>
      {!error && fichas.length === 0 && <p>No hay fichas con ese texto.</p>}
    </section>
  );
}
