export function MarcoEdicion({ miga, titulo, frase, aparece, ver, children }) {
  return (
    <section className="marco-edicion">
      <nav className="miga" aria-label="Miga de pan">{miga}</nav>
      <header className="marco-cabeza">
        <div>
          <h2>{titulo}</h2>
          <p>{frase}</p>
          {aparece && <p className="meta">Aparece en la web: {aparece}</p>}
        </div>
        {ver && (
          <a className="btn btn-fantasma" href={ver} target="_blank" rel="noreferrer">
            Ver en la web
          </a>
        )}
      </header>
      {children}
    </section>
  );
}
