import { useEffect, useMemo, useState } from 'react';
import { enviarFormulario, solicitar } from '../api';
import CampoImagen from '../componentes/CampoImagen';
import { MedioHero, incrustarVideo } from '../componentes/HeroPortada';

const VACIO = {
  tipo: 'imagen',
  origen: 'enlace',
  titulo: 'Viaja desde La Maná con el asiento ya elegido.',
  subtitulo: 'Salidas a Quevedo, Latacunga, Quito, Ambato y Guayaquil.',
  texto_boton: '',
  enlace_boton: '',
  enlace: '/bus-lamana.jpg',
  orden: 1,
  activo: true,
  ambito: 'portal',
};

export default function AdminPortada({ token }) {
  const [lista, setLista] = useState([]);
  const [form, setForm] = useState(VACIO);
  const [archivo, setArchivo] = useState(null);
  const [posterUrl, setPosterUrl] = useState('');
  const [vistaArchivo, setVistaArchivo] = useState('');
  const [subidas, setSubidas] = useState(0);
  const [mensaje, setMensaje] = useState('');
  const [error, setError] = useState('');
  const [ocupado, setOcupado] = useState(false);

  async function cargar() {
    setLista(await solicitar('/admin/portada', { token }));
  }

  useEffect(() => {
    cargar().catch((err) => setError(err.message));
  }, [token]);

  useEffect(() => {
    if (!archivo) {
      setVistaArchivo('');
      return undefined;
    }
    const url = URL.createObjectURL(archivo);
    setVistaArchivo(url);
    return () => URL.revokeObjectURL(url);
  }, [archivo]);

  const vista = useMemo(() => ({
    tipo: form.tipo,
    url: form.tipo === 'imagen' || form.origen === 'enlace' ? form.enlace : vistaArchivo,
    incrustado: form.tipo === 'video' && form.origen === 'enlace' ? incrustarVideo(form.enlace) : '',
    poster: posterUrl || '/bus-lamana.jpg',
    titulo: form.titulo || 'Título de la portada',
    subtitulo: form.subtitulo,
  }), [form, vistaArchivo, posterUrl]);

  function cambiar(campo, valor) {
    setForm((actual) => ({ ...actual, [campo]: valor }));
  }

  async function guardar(event) {
    event.preventDefault();
    setError('');
    setMensaje('');
    if (form.titulo.trim().length < 3) {
      setError('Escriba un título de al menos 3 caracteres.');
      return;
    }
    const esImagen = form.tipo === 'imagen';
    if (esImagen && !form.enlace.trim()) {
      setError('Suba una imagen o pegue su URL.');
      return;
    }
    if (!esImagen && form.origen === 'archivo' && !archivo) {
      setError('Elija el archivo de la diapositiva.');
      return;
    }
    if (!esImagen && form.origen === 'enlace' && !form.enlace.trim()) {
      setError('Pegue el enlace del video.');
      return;
    }
    const datos = new FormData();
    datos.set('tipo', form.tipo);
    datos.set('origen', esImagen ? 'enlace' : form.origen);
    datos.set('titulo', form.titulo.trim());
    datos.set('subtitulo', form.subtitulo.trim());
    datos.set('texto_boton', form.texto_boton.trim());
    datos.set('enlace_boton', form.enlace_boton.trim());
    datos.set('enlace', form.enlace.trim());
    datos.set('orden', String(form.orden || 0));
    datos.set('activo', form.activo ? '1' : '0');
    datos.set('ambito', form.ambito || 'portal');
    if (!esImagen && archivo) datos.set('archivo', archivo);
    if (posterUrl.trim()) datos.set('poster_enlace', posterUrl.trim());
    setOcupado(true);
    try {
      await enviarFormulario('/admin/portada', { token, datos });
      setMensaje('Diapositiva guardada.');
      setArchivo(null);
      setPosterUrl('');
      await cargar();
    } catch (err) {
      setError(err.message);
    } finally {
      setOcupado(false);
    }
  }

  async function alternar(item) {
    setError('');
    try {
      await solicitar(`/admin/portada/${item.id}`, {
        method: 'PATCH',
        token,
        body: {
          titulo: item.titulo,
          subtitulo: item.subtitulo,
          texto_boton: item.texto_boton,
          enlace_boton: item.enlace_boton,
          enlace: item.enlace,
          orden: item.orden,
          activo: !item.activo,
          ambito: item.ambito || 'portal',
        },
      });
      await cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  async function quitar(item) {
    if (!window.confirm(`¿Quitar la diapositiva «${item.titulo}»?`)) return;
    setError('');
    try {
      await solicitar(`/admin/portada/${item.id}`, { method: 'DELETE', token });
      await cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="rejilla-admin">
      <form className="panel-form" noValidate onSubmit={guardar}>
        <h2>Nueva diapositiva</h2>
        <div className="dos">
          <label>
            Tipo
            <select value={form.tipo} onChange={(e) => cambiar('tipo', e.target.value)} aria-label="Tipo de diapositiva">
              <option value="imagen">Imagen</option>
              <option value="video">Video</option>
            </select>
          </label>
          {form.tipo === 'video' && (
            <label>
              Origen
              <select value={form.origen} onChange={(e) => cambiar('origen', e.target.value)} aria-label="Origen del medio">
                <option value="enlace">Enlace</option>
                <option value="archivo">Archivo</option>
              </select>
            </label>
          )}
        </div>
        {form.tipo === 'imagen' ? (
          <CampoImagen
            token={token}
            valor={form.enlace}
            onChange={(url) => cambiar('enlace', url)}
            etiqueta="Imagen de la portada"
            onSubiendo={(activo) => setSubidas((n) => Math.max(0, n + (activo ? 1 : -1)))}
          />
        ) : form.origen === 'enlace' ? (
          <label>
            YouTube, Vimeo, MP4 o WebM
            <input value={form.enlace} onChange={(e) => cambiar('enlace', e.target.value)} aria-label="Enlace del medio" />
          </label>
        ) : (
          <label>
            Video MP4 o WebM
            <input
              type="file"
              accept="video/mp4,video/webm"
              aria-label="Archivo de la diapositiva"
              onChange={(e) => setArchivo(e.target.files?.[0] || null)}
            />
          </label>
        )}
        {form.tipo === 'video' && (
          <CampoImagen
            token={token}
            valor={posterUrl}
            onChange={setPosterUrl}
            etiqueta="Imagen de respaldo"
            onSubiendo={(activo) => setSubidas((n) => Math.max(0, n + (activo ? 1 : -1)))}
          />
        )}
        <label>
          Título
          <input value={form.titulo} onChange={(e) => cambiar('titulo', e.target.value)} aria-label="Título de la portada" />
        </label>
        <label>
          Subtítulo
          <input value={form.subtitulo} onChange={(e) => cambiar('subtitulo', e.target.value)} aria-label="Subtítulo de la portada" />
        </label>
        <div className="dos">
          <label>
            Texto del botón
            <input value={form.texto_boton} onChange={(e) => cambiar('texto_boton', e.target.value)} aria-label="Texto del botón" />
          </label>
          <label>
            Enlace del botón
            <input value={form.enlace_boton} onChange={(e) => cambiar('enlace_boton', e.target.value)} aria-label="Enlace del botón" />
          </label>
        </div>
        <label>
          Orden
          <input type="number" value={form.orden} onChange={(e) => cambiar('orden', Number(e.target.value))} aria-label="Orden de la diapositiva" />
        </label>
        <label>
          Dónde se ve
          <select value={form.ambito} onChange={(e) => cambiar('ambito', e.target.value)} aria-label="Ámbito de la diapositiva">
            <option value="portal">Portada del portal</option>
            <option value="transporte">Portada de Transporte</option>
          </select>
        </label>
        <label className="check">
          <input type="checkbox" checked={form.activo} onChange={(e) => cambiar('activo', e.target.checked)} aria-label="Diapositiva activa" />
          Activa
        </label>
        <button type="submit" className="btn btn-pino" disabled={ocupado || subidas > 0} aria-label="Guardar diapositiva">
          {subidas > 0 ? 'Subiendo imagen…' : (ocupado ? 'Guardando…' : 'Guardar diapositiva')}
        </button>
        {mensaje && <p className="aviso-ok" role="status">{mensaje}</p>}
        {error && <p className="aviso" role="alert">{error}</p>}
      </form>

      <section className="panel-form vista-portada" aria-label="Vista previa de la portada">
        <h2>Vista previa</h2>
        <div className="hero hero-previa">
          <div className="hero-medio" aria-hidden="true"><MedioHero slide={vista} /></div>
          <div className="hero-velo" />
          <div className="hero-contenido">
            <div className="hero-texto">
              <h3>{vista.titulo}</h3>
              {vista.subtitulo && <p>{vista.subtitulo}</p>}
            </div>
          </div>
        </div>
        <ul className="lista-admin">
          {lista.map((item) => (
            <li key={item.id}>
              <strong>{item.titulo}</strong>
              <span className="meta">{item.tipo} · {item.ambito === 'transporte' ? 'Transporte' : 'Portal'} · {item.activo ? 'activa' : 'oculta'} · orden {item.orden}</span>
              <button type="button" onClick={() => alternar(item)} aria-label={`${item.activo ? 'Ocultar' : 'Activar'} ${item.titulo}`}>
                {item.activo ? 'Ocultar' : 'Activar'}
              </button>
              <button type="button" onClick={() => quitar(item)} aria-label={`Quitar ${item.titulo}`}>Quitar</button>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
