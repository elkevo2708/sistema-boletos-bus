import { useEffect, useState } from 'react';
import { solicitar } from '../api';
import { ahoraBogotaInput, fechaBogota } from '../formato';

export function PanelBlog({ token }) {
  const [posts, setPosts] = useState([]);
  const [fotos, setFotos] = useState([]);
  const [error, setError] = useState('');
  const [editando, setEditando] = useState(null);

  async function cargar() {
    const [lista, galeria] = await Promise.all([
      solicitar('/admin/blog', { token }),
      solicitar('/admin/galeria', { token }),
    ]);
    setPosts(lista);
    setFotos(galeria);
  }

  useEffect(() => { cargar().catch((err) => setError(err.message)); }, [token]);

  async function guardar(event) {
    event.preventDefault();
    const datos = new FormData(event.currentTarget);
    const cuerpo = {
      titulo: datos.get('titulo'),
      resumen: datos.get('resumen'),
      cuerpo: datos.get('cuerpo'),
      categoria: datos.get('categoria'),
      imagen: datos.get('imagen') || null,
      publicado: datos.get('publicado') === 'on',
      publicado_en: `${datos.get('publicado_en')}:00`,
    };
    setError('');
    try {
      if (editando) {
        await solicitar(`/admin/blog/${editando}`, { method: 'PATCH', token, body: cuerpo });
      } else {
        await solicitar('/admin/blog', { method: 'POST', token, body: cuerpo });
      }
      setEditando(null);
      event.currentTarget.reset();
      await cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  async function borrar(id, titulo) {
    if (!window.confirm(`¿Eliminar «${titulo}»?`)) return;
    await solicitar(`/admin/blog/${id}`, { method: 'DELETE', token });
    await cargar();
  }

  const actual = posts.find((post) => post.id === editando) || null;

  return (
    <div className="rejilla-admin">
      <form className="panel-form" onSubmit={guardar} key={actual?.id ?? 'nueva'}>
        <h2>{actual ? 'Editar publicación' : 'Nueva publicación'}</h2>
        <label>Título<input name="titulo" required minLength={4} defaultValue={actual?.titulo ?? ''} aria-label="Título de la publicación" /></label>
        <label>Resumen<textarea name="resumen" required minLength={10} rows={3} defaultValue={actual?.resumen ?? ''} aria-label="Resumen" /></label>
        <label>Cuerpo<textarea name="cuerpo" required minLength={20} rows={8} defaultValue={actual?.cuerpo ?? ''} aria-label="Cuerpo de la publicación" /></label>
        <label>
          Categoría
          <select name="categoria" defaultValue={actual?.categoria ?? 'noticia'} aria-label="Categoría de la publicación">
            <option value="noticia">Noticia</option>
            <option value="destino">Destino</option>
          </select>
        </label>
        <label>
          Imagen
          <select name="imagen" defaultValue={String(actual?.imagen || '').replace(/^\/medios\//, '')} aria-label="Imagen de la publicación">
            <option value="">Sin imagen</option>
            {fotos.map((foto) => <option key={foto.id} value={foto.archivo}>{foto.titulo}</option>)}
          </select>
        </label>
        <label>Fecha<input type="datetime-local" name="publicado_en" required defaultValue={actual ? String(actual.publicado_en).replace(' ', 'T').slice(0, 16) : ahoraBogotaInput()} aria-label="Fecha de publicación" /></label>
        <label className="check"><input type="checkbox" name="publicado" defaultChecked={actual ? Boolean(actual.publicado) : true} /> Publicada</label>
        {error && <p className="aviso" role="alert">{error}</p>}
        <div className="acciones">
          <button type="submit" className="btn btn-arcilla" aria-label="Guardar publicación">Guardar publicación</button>
          {actual && (
            <button type="button" className="btn btn-fantasma" onClick={() => setEditando(null)} aria-label="Cancelar edición">Cancelar</button>
          )}
        </div>
      </form>
      <ul className="lista-admin">
        {posts.map((post) => (
          <li key={post.id}>
            <strong>{post.titulo}</strong>
            <span>{post.categoria} · {post.publicado ? 'publicada' : 'borrador'}</span>
            <div>
              <button type="button" onClick={() => setEditando(post.id)} aria-label={`Editar ${post.titulo}`}>Editar</button>
              <button type="button" onClick={() => borrar(post.id, post.titulo)} aria-label={`Eliminar ${post.titulo}`}>Eliminar</button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function PanelAnuncios({ token }) {
  const [lista, setLista] = useState([]);
  const [error, setError] = useState('');

  async function cargar() {
    setLista(await solicitar('/admin/anuncios', { token }));
  }
  useEffect(() => { cargar().catch((err) => setError(err.message)); }, [token]);

  async function crear(event) {
    event.preventDefault();
    const datos = new FormData(event.currentTarget);
    setError('');
    try {
      await solicitar('/admin/anuncios', {
        method: 'POST',
        token,
        body: {
          titulo: datos.get('titulo'),
          mensaje: datos.get('mensaje'),
          enlace: datos.get('enlace') || null,
          tipo: datos.get('tipo'),
          activo: true,
          inicio: datos.get('inicio'),
          fin: datos.get('fin'),
        },
      });
      event.currentTarget.reset();
      await cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  async function alternar(anuncio) {
    await solicitar(`/admin/anuncios/${anuncio.id}`, {
      method: 'PATCH',
      token,
      body: { ...anuncio, activo: !anuncio.activo, enlace: anuncio.enlace || null },
    });
    await cargar();
  }

  async function borrar(id, titulo) {
    if (!window.confirm(`¿Eliminar el anuncio «${titulo}»?`)) return;
    await solicitar(`/admin/anuncios/${id}`, { method: 'DELETE', token });
    await cargar();
  }

  return (
    <div className="rejilla-admin">
      <form className="panel-form" onSubmit={crear}>
        <h2>Nuevo anuncio</h2>
        <label>Título<input name="titulo" required minLength={3} aria-label="Título del anuncio" /></label>
        <label>Mensaje<textarea name="mensaje" required minLength={8} rows={4} aria-label="Mensaje del anuncio" /></label>
        <label>Enlace<input name="enlace" placeholder="/noticias/..." aria-label="Enlace del anuncio" /></label>
        <label>
          Dónde se muestra
          <select name="tipo" defaultValue="banner" aria-label="Tipo de anuncio">
            <option value="banner">Franja en el inicio</option>
            <option value="modal">Ventana emergente</option>
          </select>
        </label>
        <div className="dos">
          <label>Desde<input type="date" name="inicio" required defaultValue={fechaBogota(0)} aria-label="Inicio de la promoción" /></label>
          <label>Hasta<input type="date" name="fin" required defaultValue={fechaBogota(30)} aria-label="Fin de la promoción" /></label>
        </div>
        {error && <p className="aviso" role="alert">{error}</p>}
        <button type="submit" className="btn btn-arcilla" aria-label="Publicar anuncio">Publicar anuncio</button>
      </form>
      <ul className="lista-admin">
        {lista.map((anuncio) => (
          <li key={anuncio.id}>
            <strong>{anuncio.titulo}</strong>
            <span>{anuncio.tipo} · {anuncio.inicio} a {anuncio.fin} · {anuncio.activo ? 'activo' : 'pausado'}</span>
            <div>
              <button type="button" onClick={() => alternar(anuncio)} aria-label={`${anuncio.activo ? 'Pausar' : 'Activar'} ${anuncio.titulo}`}>
                {anuncio.activo ? 'Pausar' : 'Activar'}
              </button>
              <button type="button" onClick={() => borrar(anuncio.id, anuncio.titulo)} aria-label={`Eliminar anuncio ${anuncio.titulo}`}>Eliminar</button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function PanelGaleria({ token }) {
  const [fotos, setFotos] = useState([]);
  const [error, setError] = useState('');

  async function cargar() {
    setFotos(await solicitar('/admin/galeria', { token }));
  }
  useEffect(() => { cargar().catch((err) => setError(err.message)); }, [token]);

  async function subir(event) {
    event.preventDefault();
    const datos = new FormData(event.currentTarget);
    setError('');
    try {
      const respuesta = await fetch('/api/admin/galeria', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: datos,
      });
      if (!respuesta.ok) {
        const data = await respuesta.json().catch(() => ({}));
        throw new Error(typeof data.detail === 'string' ? data.detail : 'No se pudo subir la imagen');
      }
      event.currentTarget.reset();
      await cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  async function borrar(id, titulo) {
    if (!window.confirm(`¿Quitar «${titulo}» de la galería?`)) return;
    await solicitar(`/admin/galeria/${id}`, { method: 'DELETE', token });
    await cargar();
  }

  return (
    <div>
      <form className="panel-form panel-corto" onSubmit={subir}>
        <h2>Subir imagen</h2>
        <label>Título<input name="titulo" required minLength={2} aria-label="Título de la imagen" /></label>
        <label>Descripción<input name="descripcion" aria-label="Descripción de la imagen" /></label>
        <label>
          Categoría
          <select name="categoria" required defaultValue="buses" aria-label="Categoría de la imagen">
            <option value="buses">Buses</option>
            <option value="destinos">Destinos</option>
            <option value="terminales">Terminales</option>
          </select>
        </label>
        <label>Archivo<input name="archivo" type="file" accept="image/jpeg,image/png,image/webp" required aria-label="Archivo de imagen" /></label>
        {error && <p className="aviso" role="alert">{error}</p>}
        <button type="submit" className="btn btn-arcilla" aria-label="Subir imagen a la galería">Subir imagen</button>
      </form>
      <div className="mosaico admin-mosaico">
        {fotos.map((foto) => (
          <figure key={foto.id}>
            <img src={foto.url} alt={foto.titulo} />
            <figcaption>
              {foto.titulo}
              <button type="button" onClick={() => borrar(foto.id, foto.titulo)} aria-label={`Eliminar ${foto.titulo}`}>Eliminar</button>
            </figcaption>
          </figure>
        ))}
      </div>
    </div>
  );
}
