import { useEffect, useState } from 'react';
import { enviarFormulario, solicitar } from '../api';
import CuerpoAnuncio from '../componentes/CuerpoAnuncio';
import { ahoraBogotaInput, fechaBogota } from '../formato';

function anuncioVacio() {
  return {
    titulo: '',
    mensaje: '',
    enlace: '',
    texto_boton: '',
    tipo: 'modal',
    formato: 'texto',
    activo: true,
    inicio: fechaBogota(0),
    fin: fechaBogota(30),
  };
}

function validarAnuncio(campos, archivo, tieneImagen) {
  if (campos.titulo.trim().length < 3) return 'El título debe tener al menos 3 caracteres.';
  if (!campos.inicio || !campos.fin) return 'Indica el inicio y el fin de la promoción.';
  if (campos.fin < campos.inicio) return 'La fecha final no puede ser anterior al inicio.';
  if (campos.formato === 'texto' && campos.mensaje.trim().length < 8) {
    return 'El mensaje debe tener al menos 8 caracteres.';
  }
  if (campos.formato === 'imagen' && !archivo && !tieneImagen) {
    return 'La promoción con imagen necesita un archivo.';
  }
  return '';
}

function formularioAnuncio(campos, archivo) {
  const datos = new FormData();
  datos.set('titulo', campos.titulo.trim());
  datos.set('mensaje', campos.mensaje.trim());
  datos.set('enlace', campos.enlace.trim());
  datos.set('texto_boton', campos.texto_boton.trim());
  datos.set('tipo', campos.tipo);
  datos.set('formato', campos.formato);
  datos.set('activo', campos.activo ? 'true' : 'false');
  datos.set('inicio', campos.inicio);
  datos.set('fin', campos.fin);
  if (archivo) datos.set('imagen', archivo);
  return datos;
}

export function PanelBlog({ token }) {
  const [posts, setPosts] = useState([]);
  const [fotos, setFotos] = useState([]);
  const [error, setError] = useState('');
  const [aviso, setAviso] = useState('');
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
    const titulo = String(datos.get('titulo') || '').trim();
    const resumen = String(datos.get('resumen') || '').trim();
    const cuerpo = String(datos.get('cuerpo') || '').trim();
    const publicadoEn = String(datos.get('publicado_en') || '');
    setError('');
    setAviso('');
    if (titulo.length < 4) {
      setError('El título debe tener al menos 4 caracteres.');
      return;
    }
    if (resumen.length < 10) {
      setError('El resumen debe tener al menos 10 caracteres.');
      return;
    }
    if (cuerpo.length < 20) {
      setError('El cuerpo debe tener al menos 20 caracteres.');
      return;
    }
    if (!publicadoEn) {
      setError('Indica la fecha de publicación.');
      return;
    }
    const payload = {
      titulo,
      resumen,
      cuerpo,
      categoria: datos.get('categoria'),
      imagen: datos.get('imagen') || null,
      publicado: datos.get('publicado') === 'on',
      publicado_en: `${publicadoEn}:00`,
    };
    try {
      if (editando) {
        await solicitar(`/admin/blog/${editando}`, { method: 'PATCH', token, body: payload });
        setAviso('Publicación actualizada.');
      } else {
        await solicitar('/admin/blog', { method: 'POST', token, body: payload });
        setAviso('Publicación creada.');
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
    setError('');
    setAviso('');
    try {
      await solicitar(`/admin/blog/${id}`, { method: 'DELETE', token });
      if (editando === id) setEditando(null);
      setAviso('Publicación eliminada.');
      await cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  const actual = posts.find((post) => post.id === editando) || null;

  return (
    <div className="rejilla-admin">
      <form className="panel-form" noValidate onSubmit={guardar} key={actual?.id ?? 'nueva'}>
        <h2>{actual ? 'Editar publicación' : 'Nueva publicación'}</h2>
        <label>Título<input name="titulo" defaultValue={actual?.titulo ?? ''} aria-label="Título de la publicación" /></label>
        <label>Resumen<textarea name="resumen" rows={3} defaultValue={actual?.resumen ?? ''} aria-label="Resumen" /></label>
        <label>Cuerpo<textarea name="cuerpo" rows={8} defaultValue={actual?.cuerpo ?? ''} aria-label="Cuerpo de la publicación" /></label>
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
        <label>Fecha<input type="datetime-local" name="publicado_en" defaultValue={actual ? String(actual.publicado_en).replace(' ', 'T').slice(0, 16) : ahoraBogotaInput()} aria-label="Fecha de publicación" /></label>
        <label className="check"><input type="checkbox" name="publicado" defaultChecked={actual ? Boolean(actual.publicado) : true} /> Publicada</label>
        {aviso && <p className="aviso-ok" role="status">{aviso}</p>}
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
  const [campos, setCampos] = useState(anuncioVacio);
  const [editando, setEditando] = useState(null);
  const [archivo, setArchivo] = useState(null);
  const [fotoLocal, setFotoLocal] = useState('');
  const [imagenGuardada, setImagenGuardada] = useState('');
  const [error, setError] = useState('');
  const [aviso, setAviso] = useState('');

  async function cargar() {
    setLista(await solicitar('/admin/anuncios', { token }));
  }
  useEffect(() => { cargar().catch((err) => setError(err.message)); }, [token]);

  function asignar(nombre, valor) {
    setCampos((actual) => ({ ...actual, [nombre]: valor }));
  }

  function limpiarFormulario() {
    if (fotoLocal) URL.revokeObjectURL(fotoLocal);
    setCampos(anuncioVacio());
    setEditando(null);
    setArchivo(null);
    setFotoLocal('');
    setImagenGuardada('');
  }

  function elegirArchivo(event) {
    const file = event.target.files?.[0] || null;
    if (fotoLocal) URL.revokeObjectURL(fotoLocal);
    setArchivo(file);
    setFotoLocal(file ? URL.createObjectURL(file) : '');
  }

  async function guardar(event) {
    event.preventDefault();
    const fallo = validarAnuncio(campos, archivo, Boolean(imagenGuardada));
    setError(fallo);
    setAviso('');
    if (fallo) return;
    try {
      const datos = formularioAnuncio(campos, archivo);
      if (editando) {
        await enviarFormulario(`/admin/anuncios/${editando}`, { method: 'PATCH', token, datos });
        setAviso('Anuncio actualizado.');
      } else {
        await enviarFormulario('/admin/anuncios', { method: 'POST', token, datos });
        setAviso('Anuncio publicado.');
      }
      limpiarFormulario();
      await cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  function editar(anuncio) {
    if (fotoLocal) URL.revokeObjectURL(fotoLocal);
    setEditando(anuncio.id);
    setArchivo(null);
    setFotoLocal('');
    setImagenGuardada(anuncio.formato === 'imagen' ? (anuncio.imagen || '') : '');
    setCampos({
      titulo: anuncio.titulo || '',
      mensaje: anuncio.mensaje || '',
      enlace: anuncio.enlace || '',
      texto_boton: anuncio.texto_boton || '',
      tipo: anuncio.tipo || 'modal',
      formato: anuncio.formato || 'texto',
      activo: Boolean(Number(anuncio.activo)),
      inicio: String(anuncio.inicio).slice(0, 10),
      fin: String(anuncio.fin).slice(0, 10),
    });
    setError('');
    setAviso('');
  }

  async function alternar(anuncio) {
    setError('');
    setAviso('');
    try {
      const datos = formularioAnuncio({
        titulo: anuncio.titulo || '',
        mensaje: anuncio.mensaje || '',
        enlace: anuncio.enlace || '',
        texto_boton: anuncio.texto_boton || '',
        tipo: anuncio.tipo,
        formato: anuncio.formato || 'texto',
        activo: !Boolean(Number(anuncio.activo)),
        inicio: String(anuncio.inicio).slice(0, 10),
        fin: String(anuncio.fin).slice(0, 10),
      }, null);
      await enviarFormulario(`/admin/anuncios/${anuncio.id}`, { method: 'PATCH', token, datos });
      setAviso(anuncio.activo ? 'Anuncio pausado.' : 'Anuncio activado.');
      await cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  async function borrar(id, titulo) {
    if (!window.confirm(`¿Eliminar el anuncio «${titulo}»?`)) return;
    setError('');
    setAviso('');
    try {
      await solicitar(`/admin/anuncios/${id}`, { method: 'DELETE', token });
      if (editando === id) limpiarFormulario();
      setAviso('Anuncio eliminado.');
      await cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  const foto = fotoLocal || (campos.formato === 'imagen' ? imagenGuardada : '');

  return (
    <div className="rejilla-admin">
      <form className="panel-form" noValidate onSubmit={guardar}>
        <h2>{editando ? 'Editar anuncio' : 'Nuevo anuncio'}</h2>
        <label>Título<input value={campos.titulo} onChange={(e) => asignar('titulo', e.target.value)} aria-label="Título del anuncio" /></label>
        <fieldset className="opciones">
          <legend>Formato</legend>
          <label>
            <input type="radio" name="formato" value="texto" checked={campos.formato === 'texto'} onChange={() => asignar('formato', 'texto')} />
            Solo texto
          </label>
          <label>
            <input type="radio" name="formato" value="imagen" checked={campos.formato === 'imagen'} onChange={() => asignar('formato', 'imagen')} />
            Imagen
          </label>
        </fieldset>
        {campos.formato === 'texto' ? (
          <label>Mensaje<textarea value={campos.mensaje} onChange={(e) => asignar('mensaje', e.target.value)} rows={4} aria-label="Mensaje del anuncio" /></label>
        ) : (
          <label>
            Imagen
            <input type="file" accept="image/jpeg,image/png,image/webp" onChange={elegirArchivo} aria-label="Imagen de la promoción" />
          </label>
        )}
        <label>Texto del botón<input value={campos.texto_boton} onChange={(e) => asignar('texto_boton', e.target.value)} aria-label="Texto del botón" placeholder="Ver más" /></label>
        <label>Enlace<input value={campos.enlace} onChange={(e) => asignar('enlace', e.target.value)} placeholder="/noticias/..." aria-label="Enlace del anuncio" /></label>
        <label>
          Dónde se muestra
          <select value={campos.tipo} onChange={(e) => asignar('tipo', e.target.value)} aria-label="Tipo de anuncio">
            <option value="banner">Franja en el inicio</option>
            <option value="modal">Ventana emergente</option>
          </select>
        </label>
        <div className="dos">
          <label>Desde<input type="date" value={campos.inicio} onChange={(e) => asignar('inicio', e.target.value)} aria-label="Inicio de la promoción" /></label>
          <label>Hasta<input type="date" value={campos.fin} onChange={(e) => asignar('fin', e.target.value)} aria-label="Fin de la promoción" /></label>
        </div>
        <label className="check">
          <input type="checkbox" checked={campos.activo} onChange={(e) => asignar('activo', e.target.checked)} />
          Activo
        </label>
        {aviso && <p className="aviso-ok" role="status">{aviso}</p>}
        {error && <p className="aviso" role="alert">{error}</p>}
        <div className="acciones">
          <button type="submit" className="btn btn-arcilla" aria-label="Publicar anuncio">{editando ? 'Guardar cambios' : 'Publicar anuncio'}</button>
          {editando && (
            <button type="button" className="btn btn-fantasma" onClick={limpiarFormulario} aria-label="Cancelar edición del anuncio">Cancelar</button>
          )}
        </div>
      </form>
      <div>
        <h2>Vista previa</h2>
        <CuerpoAnuncio anuncio={campos} imagen={foto} />
        {aviso && <p className="aviso-ok" role="status">{aviso}</p>}
        {error && <p className="aviso" role="alert">{error}</p>}
        <ul className="lista-admin">
          {lista.map((anuncio) => (
            <li key={anuncio.id}>
              <strong>{anuncio.titulo}</strong>
              <span>
                {anuncio.formato || 'texto'} · {anuncio.tipo} · {anuncio.inicio} a {anuncio.fin} · {Number(anuncio.activo) ? 'activo' : 'pausado'}
              </span>
              <div>
                <button type="button" onClick={() => editar(anuncio)} aria-label={`Editar anuncio ${anuncio.titulo}`}>Editar</button>
                <button type="button" onClick={() => alternar(anuncio)} aria-label={`${Number(anuncio.activo) ? 'Pausar' : 'Activar'} ${anuncio.titulo}`}>
                  {Number(anuncio.activo) ? 'Pausar' : 'Activar'}
                </button>
                <button type="button" onClick={() => borrar(anuncio.id, anuncio.titulo)} aria-label={`Eliminar anuncio ${anuncio.titulo}`}>Eliminar</button>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export function PanelGaleria({ token }) {
  const [fotos, setFotos] = useState([]);
  const [error, setError] = useState('');
  const [aviso, setAviso] = useState('');

  async function cargar() {
    setFotos(await solicitar('/admin/galeria', { token }));
  }
  useEffect(() => { cargar().catch((err) => setError(err.message)); }, [token]);

  async function subir(event) {
    event.preventDefault();
    const datos = new FormData(event.currentTarget);
    const titulo = String(datos.get('titulo') || '').trim();
    const archivo = datos.get('archivo');
    setError('');
    setAviso('');
    if (titulo.length < 2) {
      setError('El título debe tener al menos 2 caracteres.');
      return;
    }
    if (!archivo || !archivo.name) {
      setError('Elige una imagen JPG, PNG o WebP.');
      return;
    }
    datos.set('titulo', titulo);
    try {
      await enviarFormulario('/admin/galeria', { method: 'POST', token, datos });
      setAviso('Imagen publicada en la galería.');
      event.currentTarget.reset();
      await cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  async function borrar(id, titulo) {
    if (!window.confirm(`¿Quitar «${titulo}» de la galería?`)) return;
    setError('');
    setAviso('');
    try {
      await solicitar(`/admin/galeria/${id}`, { method: 'DELETE', token });
      setAviso('Imagen eliminada.');
      await cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div>
      <form className="panel-form panel-corto" noValidate onSubmit={subir}>
        <h2>Subir imagen</h2>
        <label>Título<input name="titulo" aria-label="Título de la imagen" /></label>
        <label>Descripción<input name="descripcion" aria-label="Descripción de la imagen" /></label>
        <label>
          Categoría
          <select name="categoria" defaultValue="buses" aria-label="Categoría de la imagen">
            <option value="buses">Buses</option>
            <option value="destinos">Destinos</option>
            <option value="terminales">Terminales</option>
          </select>
        </label>
        <label>Archivo<input name="archivo" type="file" accept="image/jpeg,image/png,image/webp" aria-label="Archivo de imagen" /></label>
        {aviso && <p className="aviso-ok" role="status">{aviso}</p>}
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
