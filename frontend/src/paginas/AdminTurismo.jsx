import { useEffect, useState } from 'react';
import { enviarFormulario, solicitar } from '../api';

const TIPOS = ['atractivo', 'gastronomia', 'hospedaje', 'actividad', 'ruta', 'parroquia', 'guia', 'evento'];

const FICHA_VACIA = {
  tipo: 'atractivo',
  categoria_id: '',
  nombre: '',
  resumen: '',
  cuerpo: '',
  zona: '',
  direccion: '',
  imagen: '',
  credito: '',
  destacado: false,
  orden: 0,
  activo: true,
};

export default function AdminTurismo({ token }) {
  const [seccion, setSeccion] = useState('fichas');
  const [categorias, setCategorias] = useState([]);
  const [fichas, setFichas] = useState([]);
  const [eventos, setEventos] = useState([]);
  const [galeria, setGaleria] = useState([]);
  const [mensajes, setMensajes] = useState([]);
  const [ficha, setFicha] = useState(FICHA_VACIA);
  const [categoria, setCategoria] = useState({ tipo: 'atractivo', nombre: '', resumen: '', orden: 0, activo: true });
  const [evento, setEvento] = useState({
    titulo: '', resumen: '', cuerpo: '', inicio: '', fin: '', lugar: '', imagen: '', credito: '', categoria_id: '', activo: true,
  });
  const [mensaje, setMensaje] = useState('');
  const [error, setError] = useState('');

  async function cargar() {
    const [cats, lista, fechas, fotos, buzon] = await Promise.all([
      solicitar('/admin/turismo/categorias', { token }),
      solicitar('/admin/turismo/fichas', { token }),
      solicitar('/admin/turismo/eventos', { token }),
      solicitar('/admin/turismo/galeria', { token }),
      solicitar('/admin/turismo/mensajes', { token }),
    ]);
    setCategorias(cats);
    setFichas(lista);
    setEventos(fechas);
    setGaleria(fotos);
    setMensajes(buzon);
  }

  useEffect(() => {
    cargar().catch((err) => setError(err.message));
  }, [token]);

  function aviso(texto) {
    setError('');
    setMensaje(texto);
  }

  async function guardarCategoria(event) {
    event.preventDefault();
    try {
      await solicitar('/admin/turismo/categorias', {
        method: 'POST', token, body: { ...categoria, orden: Number(categoria.orden) || 0 },
      });
      aviso('Categoría guardada.');
      setCategoria({ tipo: 'atractivo', nombre: '', resumen: '', orden: 0, activo: true });
      await cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  async function guardarFicha(event) {
    event.preventDefault();
    const cuerpo = {
      ...ficha,
      categoria_id: ficha.categoria_id ? Number(ficha.categoria_id) : null,
      orden: Number(ficha.orden) || 0,
      imagen: ficha.imagen || null,
      lat: ficha.lat ?? null,
      lng: ficha.lng ?? null,
    };
    try {
      await solicitar(ficha.id ? `/admin/turismo/fichas/${ficha.id}` : '/admin/turismo/fichas', {
        method: ficha.id ? 'PATCH' : 'POST',
        token,
        body: cuerpo,
      });
      aviso(ficha.id ? 'Ficha actualizada.' : 'Ficha creada.');
      setFicha(FICHA_VACIA);
      await cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  async function subir(event, asignar) {
    const archivo = event.target.files?.[0];
    if (!archivo) return;
    const datos = new FormData();
    datos.set('archivo', archivo);
    try {
      const respuesta = await enviarFormulario('/admin/turismo/medios', { token, datos });
      asignar(respuesta.url);
      aviso('Imagen subida. Guarde la ficha para usarla.');
    } catch (err) {
      setError(err.message);
    }
  }

  async function guardarEvento(event) {
    event.preventDefault();
    try {
      await solicitar('/admin/turismo/eventos', {
        method: 'POST',
        token,
        body: {
          ...evento,
          categoria_id: evento.categoria_id ? Number(evento.categoria_id) : null,
          fin: evento.fin || null,
          imagen: evento.imagen || null,
        },
      });
      aviso('Evento publicado.');
      setEvento({ titulo: '', resumen: '', cuerpo: '', inicio: '', fin: '', lugar: '', imagen: '', credito: '', categoria_id: '', activo: true });
      await cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  async function quitar(ruta, etiqueta) {
    if (!window.confirm(`¿Quitar ${etiqueta}?`)) return;
    try {
      await solicitar(ruta, { method: 'DELETE', token });
      aviso('Eliminado.');
      await cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  async function subirGaleria(event) {
    event.preventDefault();
    const formulario = event.currentTarget;
    const datos = new FormData(formulario);
    try {
      await enviarFormulario('/admin/turismo/galeria', { token, datos });
      formulario.reset();
      aviso('Foto agregada a la galería del portal.');
      await cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  const categoriasDelTipo = categorias.filter((item) => item.tipo === ficha.tipo);

  return (
    <div>
      <div className="filtros" role="tablist" aria-label="Turismo">
        {[
          ['fichas', 'Fichas'],
          ['categorias', 'Categorías'],
          ['eventos', 'Agenda'],
          ['galeria', 'Galería'],
          ['mensajes', 'Mensajes'],
        ].map(([id, etiqueta]) => (
          <button key={id} type="button" className={seccion === id ? 'activo' : ''} onClick={() => setSeccion(id)} aria-label={`Abrir ${etiqueta}`}>{etiqueta}</button>
        ))}
      </div>
      {mensaje && <p className="aviso-ok" role="status">{mensaje}</p>}
      {error && <p className="aviso" role="alert">{error}</p>}

      {seccion === 'categorias' && (
        <div className="rejilla-admin">
          <form className="panel-form" noValidate onSubmit={guardarCategoria}>
            <h2>Nueva categoría</h2>
            <label>Tipo
              <select value={categoria.tipo} onChange={(e) => setCategoria({ ...categoria, tipo: e.target.value })} aria-label="Tipo de categoría">
                {TIPOS.map((tipo) => <option key={tipo}>{tipo}</option>)}
              </select>
            </label>
            <label>Nombre<input value={categoria.nombre} onChange={(e) => setCategoria({ ...categoria, nombre: e.target.value })} aria-label="Nombre de la categoría" /></label>
            <label>Resumen<input value={categoria.resumen} onChange={(e) => setCategoria({ ...categoria, resumen: e.target.value })} aria-label="Resumen de la categoría" /></label>
            <button type="submit" className="btn btn-pino" aria-label="Guardar categoría">Guardar categoría</button>
          </form>
          <ul className="lista-admin">
            {categorias.map((item) => (
              <li key={item.id}>
                <strong>{item.nombre}</strong>
                <span className="meta">{item.tipo} · {item.slug}</span>
                <button type="button" onClick={() => quitar(`/admin/turismo/categorias/${item.id}`, item.nombre)} aria-label={`Quitar ${item.nombre}`}>Quitar</button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {seccion === 'fichas' && (
        <div className="rejilla-admin">
          <form className="panel-form" noValidate onSubmit={guardarFicha}>
            <h2>{ficha.id ? 'Editar ficha' : 'Nueva ficha'}</h2>
            <label>Tipo
              <select value={ficha.tipo} onChange={(e) => setFicha({ ...ficha, tipo: e.target.value, categoria_id: '' })} aria-label="Tipo de ficha">
                {TIPOS.filter((tipo) => tipo !== 'evento').map((tipo) => <option key={tipo}>{tipo}</option>)}
              </select>
            </label>
            <label>Categoría
              <select value={ficha.categoria_id} onChange={(e) => setFicha({ ...ficha, categoria_id: e.target.value })} aria-label="Categoría de la ficha">
                <option value="">Sin categoría</option>
                {categoriasDelTipo.map((item) => <option key={item.id} value={item.id}>{item.nombre}</option>)}
              </select>
            </label>
            <label>Nombre<input value={ficha.nombre} onChange={(e) => setFicha({ ...ficha, nombre: e.target.value })} aria-label="Nombre de la ficha" /></label>
            <label>Resumen<input value={ficha.resumen} onChange={(e) => setFicha({ ...ficha, resumen: e.target.value })} aria-label="Resumen de la ficha" /></label>
            <label>Texto<textarea value={ficha.cuerpo} onChange={(e) => setFicha({ ...ficha, cuerpo: e.target.value })} aria-label="Texto de la ficha" rows={5} /></label>
            <label>Zona<input value={ficha.zona} onChange={(e) => setFicha({ ...ficha, zona: e.target.value })} aria-label="Zona" /></label>
            <label>Imagen actual<input value={ficha.imagen || ''} onChange={(e) => setFicha({ ...ficha, imagen: e.target.value })} aria-label="Ruta de la imagen" /></label>
            <label>Subir imagen
              <input type="file" accept="image/jpeg,image/png,image/webp" aria-label="Archivo de la ficha" onChange={(e) => subir(e, (url) => setFicha((actual) => ({ ...actual, imagen: url })))} />
            </label>
            <label>Crédito<input value={ficha.credito} onChange={(e) => setFicha({ ...ficha, credito: e.target.value })} aria-label="Crédito de la imagen" /></label>
            <label className="check">
              <input type="checkbox" checked={ficha.destacado} onChange={(e) => setFicha({ ...ficha, destacado: e.target.checked })} aria-label="Ficha destacada" />
              Destacada en el inicio
            </label>
            <button type="submit" className="btn btn-pino" aria-label="Guardar ficha">Guardar ficha</button>
          </form>
          <ul className="lista-admin">
            {fichas.map((item) => (
              <li key={item.id}>
                <strong>{item.nombre}</strong>
                <span className="meta">{item.tipo} · {item.activo ? 'activa' : 'oculta'}</span>
                <button type="button" onClick={() => setFicha({ ...item, categoria_id: item.categoria_id || '', imagen: item.imagen || '' })} aria-label={`Editar ${item.nombre}`}>Editar</button>
                <button type="button" onClick={() => quitar(`/admin/turismo/fichas/${item.id}`, item.nombre)} aria-label={`Quitar ${item.nombre}`}>Quitar</button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {seccion === 'eventos' && (
        <div className="rejilla-admin">
          <form className="panel-form" noValidate onSubmit={guardarEvento}>
            <h2>Nuevo evento</h2>
            <label>Título<input value={evento.titulo} onChange={(e) => setEvento({ ...evento, titulo: e.target.value })} aria-label="Título del evento" /></label>
            <label>Resumen<input value={evento.resumen} onChange={(e) => setEvento({ ...evento, resumen: e.target.value })} aria-label="Resumen del evento" /></label>
            <label>Texto<textarea value={evento.cuerpo} onChange={(e) => setEvento({ ...evento, cuerpo: e.target.value })} aria-label="Texto del evento" rows={4} /></label>
            <div className="dos">
              <label>Inicio<input type="date" value={evento.inicio} onChange={(e) => setEvento({ ...evento, inicio: e.target.value })} aria-label="Inicio del evento" /></label>
              <label>Fin<input type="date" value={evento.fin} onChange={(e) => setEvento({ ...evento, fin: e.target.value })} aria-label="Fin del evento" /></label>
            </div>
            <label>Lugar<input value={evento.lugar} onChange={(e) => setEvento({ ...evento, lugar: e.target.value })} aria-label="Lugar del evento" /></label>
            <button type="submit" className="btn btn-pino" aria-label="Guardar evento">Guardar evento</button>
          </form>
          <ul className="lista-admin">
            {eventos.map((item) => (
              <li key={item.id}>
                <strong>{item.titulo}</strong>
                <span className="meta">{item.inicio}</span>
                <button type="button" onClick={() => quitar(`/admin/turismo/eventos/${item.id}`, item.titulo)} aria-label={`Quitar ${item.titulo}`}>Quitar</button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {seccion === 'galeria' && (
        <div className="rejilla-admin">
          <form className="panel-form" noValidate onSubmit={subirGaleria}>
            <h2>Foto de la galería</h2>
            <label>Título<input name="titulo" aria-label="Título de la foto" /></label>
            <label>Descripción<input name="descripcion" aria-label="Descripción de la foto" /></label>
            <label>Crédito<input name="credito" aria-label="Crédito de la foto" /></label>
            <label>Archivo<input name="archivo" type="file" accept="image/jpeg,image/png,image/webp" aria-label="Archivo de la galería" /></label>
            <button type="submit" className="btn btn-pino" aria-label="Subir foto">Subir foto</button>
          </form>
          <ul className="lista-admin">
            {galeria.map((item) => (
              <li key={item.id}>
                <strong>{item.titulo}</strong>
                <button type="button" onClick={() => quitar(`/admin/turismo/galeria/${item.id}`, item.titulo)} aria-label={`Quitar ${item.titulo}`}>Quitar</button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {seccion === 'mensajes' && (
        <ul className="lista-admin">
          {mensajes.map((item) => (
            <li key={item.id}>
              <strong>{item.nombre}</strong>
              <span className="meta">{item.email} · {item.creado_en}</span>
              <p>{item.mensaje}</p>
            </li>
          ))}
          {mensajes.length === 0 && <li>No hay mensajes.</li>}
        </ul>
      )}
    </div>
  );
}
