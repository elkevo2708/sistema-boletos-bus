import { useEffect } from 'react';

export function Boton({
  variante = 'primario',
  tamano = 'md',
  className = '',
  children,
  ...props
}) {
  const mapa = {
    primario: 'btn btn-pino',
    secundario: 'btn btn-fantasma',
    ghost: 'btn btn-fantasma',
    peligro: 'btn btn-peligro',
    acento: 'btn btn-oro',
    arcilla: 'btn btn-arcilla',
  };
  const clases = `${mapa[variante] || mapa.primario} ${tamano === 'lg' ? 'btn-grande' : ''} ${className}`.trim();
  return (
    <button type="button" className={clases} {...props}>
      {children}
    </button>
  );
}

export function Tarjeta({ className = '', children, ...props }) {
  return <article className={`tarjeta ${className}`.trim()} {...props}>{children}</article>;
}

export function EncabezadoPagina({ kicker = 'La Maná', titulo, bajada, imagen = '/turismo/panoramica.jpg', miga }) {
  return (
    <header className="page-hero">
      <img src={imagen} alt="" />
      <div className="page-hero-velo" />
      <div className="page-hero-texto">
        {miga && <nav className="miga" aria-label="Miga de pan">{miga}</nav>}
        {kicker && <p className="sobrelinea">{kicker}</p>}
        <h1>{titulo}</h1>
        {bajada && <p className="lead">{bajada}</p>}
      </div>
    </header>
  );
}

export function Seccion({ titulo, kicker, accion, clara = false, children, className = '' }) {
  return (
    <section className={`portal-bloque ${clara ? 'portal-claro' : ''} ${className}`.trim()}>
      {(titulo || accion) && (
        <div className="portal-encabezado">
          <div>
            {kicker && <p className="sobrelinea">{kicker}</p>}
            {titulo && <h2>{titulo}</h2>}
          </div>
          {accion}
        </div>
      )}
      {children}
    </section>
  );
}

export function Insignia({ children, tono = 'amarillo' }) {
  return <span className={`insignia insignia-${tono}`}>{children}</span>;
}

export function Pastilla({ activo = false, children, ...props }) {
  const etiqueta = props.href ? 'a' : 'button';
  const Clase = etiqueta;
  return <Clase className={activo ? 'pastilla activo' : 'pastilla'} {...props}>{children}</Clase>;
}

export function Pestanias({ etiqueta, children }) {
  return <div className="pestanas" role="tablist" aria-label={etiqueta}>{children}</div>;
}

export function Modal({ titulo, onCerrar, children, etiquetaCerrar = 'Cerrar' }) {
  useEffect(() => {
    function tecla(evento) {
      if (evento.key === 'Escape') onCerrar?.();
    }
    document.addEventListener('keydown', tecla);
    return () => document.removeEventListener('keydown', tecla);
  }, [onCerrar]);

  return (
    <div className="velo" role="presentation" onClick={onCerrar}>
      <div className="modal" role="dialog" aria-modal="true" aria-label={titulo} onClick={(evento) => evento.stopPropagation()}>
        {titulo && <h2>{titulo}</h2>}
        {children}
        {onCerrar && (
          <button type="button" className="btn btn-fantasma" onClick={onCerrar} aria-label={etiquetaCerrar}>
            {etiquetaCerrar}
          </button>
        )}
      </div>
    </div>
  );
}

export function Aviso({ tono = 'error', children }) {
  return <p className={tono === 'ok' ? 'aviso-ok' : 'aviso'} role={tono === 'ok' ? 'status' : 'alert'}>{children}</p>;
}

export function EstadoVacio({ titulo, texto, accion }) {
  return (
    <div className="vacio" role="status">
      <strong>{titulo}</strong>
      {texto && <p>{texto}</p>}
      {accion}
    </div>
  );
}

export function Esqueleto({ lineas = 3 }) {
  return (
    <div className="esqueleto-bloque" role="status" aria-label="Cargando">
      {Array.from({ length: lineas }, (_, i) => <span key={i} className="esqueleto" />)}
    </div>
  );
}

export function Tabla({ columnas, filas, titulo, vacio = 'No hay registros.' }) {
  return (
    <div className="tabla-wrap">
      <table>
        {titulo && <caption>{titulo}</caption>}
        <thead>
          <tr>{columnas.map((col) => <th key={col}>{col}</th>)}</tr>
        </thead>
        <tbody>
          {filas.length ? filas.map((fila) => (
            <tr key={fila.key}>
              {fila.celdas.map((celda, indice) => (
                <td key={columnas[indice]} data-label={columnas[indice]}>{celda}</td>
              ))}
            </tr>
          )) : (
            <tr><td colSpan={columnas.length}>{vacio}</td></tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

export function Paginacion({ pagina, total, onCambio }) {
  if (total <= 1) return null;
  return (
    <nav className="paginacion" aria-label="Paginación">
      <button type="button" className="btn btn-fantasma" disabled={pagina <= 1} onClick={() => onCambio(pagina - 1)} aria-label="Página anterior">
        Anterior
      </button>
      <span>Página {pagina} de {total}</span>
      <button type="button" className="btn btn-fantasma" disabled={pagina >= total} onClick={() => onCambio(pagina + 1)} aria-label="Página siguiente">
        Siguiente
      </button>
    </nav>
  );
}

export function Campo({ etiqueta, children }) {
  return (
    <label>
      {etiqueta}
      {children}
    </label>
  );
}
