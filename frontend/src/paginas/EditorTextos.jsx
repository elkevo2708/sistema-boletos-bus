import { useEffect, useMemo, useState } from 'react';
import { solicitar } from '../api';
import { EstadoVacio } from '../ui/ui';

export default function EditorTextos({ token, espacio, prefijo = '' }) {
  const [lista, setLista] = useState([]);
  const [borrador, setBorrador] = useState({});
  const [busqueda, setBusqueda] = useState('');
  const [aviso, setAviso] = useState('');
  const [error, setError] = useState('');
  const [sucio, setSucio] = useState(false);

  useEffect(() => {
    solicitar(`/admin/textos?espacio=${espacio}`, { token })
      .then((datos) => {
        const propios = prefijo ? datos.filter((item) => item.clave.startsWith(prefijo)) : datos;
        setLista(propios);
        setBorrador(Object.fromEntries(propios.map((item) => [item.id, item.valor])));
      })
      .catch((err) => setError(err.message));
  }, [token, espacio, prefijo]);

  useEffect(() => {
    function salir(evento) {
      if (!sucio) return;
      evento.preventDefault();
      evento.returnValue = '';
    }
    window.addEventListener('beforeunload', salir);
    return () => window.removeEventListener('beforeunload', salir);
  }, [sucio]);

  const visibles = useMemo(() => {
    const q = busqueda.trim().toLowerCase();
    if (!q) return lista;
    return lista.filter((item) => `${item.etiqueta} ${item.aparece} ${item.valor}`.toLowerCase().includes(q));
  }, [lista, busqueda]);

  async function guardar(item) {
    setError('');
    try {
      const actualizado = await solicitar(`/admin/textos/${item.id}`, {
        method: 'PATCH',
        token,
        body: { valor: borrador[item.id] },
      });
      setLista((actual) => actual.map((fila) => (fila.id === item.id ? actualizado : fila)));
      setSucio(false);
      setAviso(`Guardado: ${item.etiqueta}. Ya se ve en la web.`);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="editor-textos">
      {aviso && <p className="toast" role="status">{aviso}</p>}
      {error && <p className="aviso" role="alert">{error}</p>}
      <label>
        Buscar un texto
        <input value={busqueda} onChange={(evento) => setBusqueda(evento.target.value)} placeholder="Por ejemplo: contacto" aria-label="Buscar un texto" />
      </label>
      {visibles.length === 0 && <EstadoVacio titulo="Nada con ese nombre" texto="Prueba con otra palabra del título o de la página." />}
      {visibles.map((item) => {
        const valor = borrador[item.id] ?? '';
        const cambio = valor !== item.valor;
        return (
          <form key={item.id} className="panel-form" onSubmit={(evento) => { evento.preventDefault(); guardar(item); }}>
            <h3>{item.etiqueta}</h3>
            <p className="meta">{item.aparece}</p>
            <label>
              Texto
              {item.maximo > 160 ? (
                <textarea
                  value={valor}
                  maxLength={item.maximo}
                  rows={4}
                  aria-label={item.etiqueta}
                  onChange={(evento) => { setBorrador({ ...borrador, [item.id]: evento.target.value }); setSucio(true); setAviso(''); }}
                />
              ) : (
                <input
                  value={valor}
                  maxLength={item.maximo}
                  aria-label={item.etiqueta}
                  onChange={(evento) => { setBorrador({ ...borrador, [item.id]: evento.target.value }); setSucio(true); setAviso(''); }}
                />
              )}
            </label>
            <p className="meta">{item.ayuda}</p>
            <p className="meta">{valor.length} / {item.maximo} caracteres</p>
            {item.clave.startsWith('portal.saber') && (
              <article className="vista-mini">
                <h4>{valor.slice(0, 80)}</h4>
                <p>Así se lee en el inicio, dentro de su tarjeta.</p>
              </article>
            )}
            <button type="submit" className="btn btn-pino" disabled={!cambio} aria-label={`Guardar ${item.etiqueta}`}>
              Guardar
            </button>
          </form>
        );
      })}
    </div>
  );
}
