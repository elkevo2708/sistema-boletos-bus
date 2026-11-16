import { useEffect, useState } from 'react';
import { solicitar } from '../api';
import { Aviso, EstadoVacio, Insignia } from '../ui/ui';

const ESTADOS = ['inscrito', 'confirmado', 'asistio', 'certificado', 'cancelado'];

export default function AdminCursos({ token }) {
  const [datos, setDatos] = useState(null);
  const [cursoId, setCursoId] = useState('');
  const [inscritos, setInscritos] = useState([]);
  const [aviso, setAviso] = useState('');
  const [error, setError] = useState('');
  const [moduloId, setModuloId] = useState('');

  async function cargar() {
    const catalogo = await solicitar('/admin/cursos/catalogo', { token });
    setDatos(catalogo);
    if (!cursoId && catalogo.cursos[0]) setCursoId(String(catalogo.cursos[0].id));
  }

  useEffect(() => {
    cargar().catch((err) => setError(err.message));
  }, [token]);

  useEffect(() => {
    if (!cursoId) return;
    solicitar(`/admin/cursos/${cursoId}/inscritos`, { token }).then(setInscritos).catch((err) => setError(err.message));
  }, [cursoId, token]);

  async function enviar(ruta, cuerpo, mensaje) {
    setError('');
    try {
      await solicitar(ruta, { method: 'POST', token, body: cuerpo });
      setAviso(mensaje);
      await cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  async function cambiarEstado(id, estado) {
    await solicitar(`/admin/cursos/inscripciones/${id}`, { method: 'PATCH', token, body: { estado } });
    setInscritos(await solicitar(`/admin/cursos/${cursoId}/inscritos`, { token }));
    setAviso('Estado actualizado.');
  }

  if (!datos) return <p>Cargando cursos…</p>;

  return (
    <div className="editor-textos">
      {aviso && <p className="toast" role="status">{aviso}</p>}
      {error && <Aviso>{error}</Aviso>}
      <form className="panel-form" onSubmit={(evento) => {
        evento.preventDefault();
        const datosForm = new FormData(evento.currentTarget);
        enviar('/admin/cursos', {
          titulo: datosForm.get('titulo'),
          resumen: datosForm.get('resumen'),
          descripcion: datosForm.get('resumen'),
          categoria_id: Number(datosForm.get('categoria_id')) || null,
          modalidad: datosForm.get('modalidad'),
          nivel: datosForm.get('nivel'),
          duracion_horas: Number(datosForm.get('duracion_horas')),
          cupos: Number(datosForm.get('cupos')),
          gratis: datosForm.get('gratis') === '1',
          costo: datosForm.get('gratis') === '1' ? null : Number(datosForm.get('costo') || 0),
          lugar: datosForm.get('lugar'),
          inicio: datosForm.get('inicio') || null,
          certificado: datosForm.get('certificado') === 'on',
          destacado: datosForm.get('destacado') === 'on',
        }, 'Curso publicado. Ya se ve en Aprende.');
        evento.currentTarget.reset();
      }}>
        <h3>Nuevo curso</h3>
        <p className="meta">Aparece en /aprende en cuanto queda activo.</p>
        <label>Título<input name="titulo" required aria-label="Título del curso" placeholder="Ejemplo: taller de atención" /></label>
        <label>Resumen<input name="resumen" required maxLength={400} aria-label="Resumen del curso" /></label>
        <label>Categoría
          <select name="categoria_id" aria-label="Categoría del curso">
            <option value="">Sin categoría</option>
            {datos.categorias.map((item) => <option key={item.id} value={item.id}>{item.nombre}</option>)}
          </select>
        </label>
        <div className="dos">
          <label>Modalidad
            <select name="modalidad" aria-label="Modalidad"><option value="presencial">Presencial</option><option value="virtual">Virtual</option><option value="mixta">Mixta</option></select>
          </label>
          <label>Nivel
            <select name="nivel" aria-label="Nivel"><option value="basico">Básico</option><option value="intermedio">Intermedio</option><option value="avanzado">Avanzado</option></select>
          </label>
        </div>
        <div className="dos">
          <label>Horas<input name="duracion_horas" type="number" min="1" defaultValue="4" aria-label="Duración en horas" /></label>
          <label>Cupos<input name="cupos" type="number" min="1" defaultValue="20" aria-label="Cupos" /></label>
        </div>
        <label>¿Es gratis?
          <select name="gratis" aria-label="Gratuidad"><option value="1">Gratis</option><option value="0">Con costo</option></select>
        </label>
        <label>Costo en USD si no es gratis<input name="costo" type="number" min="0" step="0.01" aria-label="Costo" /></label>
        <label>Lugar o enlace de la sede<input name="lugar" aria-label="Lugar" placeholder="Salón, finca o enlace de la clase" /></label>
        <label>Fecha de inicio<input name="inicio" type="date" aria-label="Inicio del curso" /></label>
        <label className="check"><input name="certificado" type="checkbox" /> Ofrece certificado</label>
        <label className="check"><input name="destacado" type="checkbox" /> Destacado en la portada de Aprende</label>
        <button type="submit" className="btn btn-pino">Publicar curso</button>
      </form>

      <h3>Cursos</h3>
      {datos.cursos.length === 0 && <EstadoVacio titulo="Aún no hay cursos" texto="Publica el primero con el formulario de arriba." />}
      <ul className="lista-admin">
        {datos.cursos.map((curso) => (
          <li key={curso.id}>
            <strong>{curso.titulo}</strong>
            {curso.ejemplo && <Insignia>Ejemplo</Insignia>}
            <Insignia tono={curso.activo ? 'verde' : 'amarillo'}>{curso.activo ? 'Publicado' : 'Oculto'}</Insignia>
            <span className="meta">{curso.ocupados}/{curso.cupos} cupos</span>
            <button type="button" onClick={() => setCursoId(String(curso.id))}>Ver inscritos</button>
            <button type="button" onClick={() => solicitar(`/admin/cursos/${curso.id}`, { method: 'PATCH', token, body: { activo: !curso.activo } }).then(cargar)}>
              {curso.activo ? 'Ocultar' : 'Publicar'}
            </button>
          </li>
        ))}
      </ul>

      <form className="panel-form" onSubmit={(evento) => {
        evento.preventDefault();
        const titulo = new FormData(evento.currentTarget).get('titulo');
        if (!cursoId) return;
        enviar(`/admin/cursos/${cursoId}/modulos`, { titulo, orden: 1 }, 'Módulo agregado.');
        evento.currentTarget.reset();
      }}>
        <h3>Módulo del curso seleccionado</h3>
        <p className="meta">Elige el curso en la lista y agrega un bloque del temario.</p>
        <label>Título del módulo<input name="titulo" aria-label="Título del módulo" required /></label>
        <button type="submit" className="btn btn-fantasma" disabled={!cursoId}>Agregar módulo</button>
      </form>
      <form className="panel-form" onSubmit={(evento) => {
        evento.preventDefault();
        const datosForm = new FormData(evento.currentTarget);
        enviar(`/admin/cursos/modulos/${datosForm.get('modulo_id')}/lecciones`, {
          titulo: datosForm.get('titulo'),
          tipo: datosForm.get('tipo'),
          cuerpo: datosForm.get('cuerpo'),
          video_url: datosForm.get('video_url'),
          pdf_url: datosForm.get('pdf_url'),
        }, 'Lección publicada.');
      }}>
        <h3>Lección</h3>
        <label>Id del módulo<input name="modulo_id" value={moduloId} onChange={(e) => setModuloId(e.target.value)} aria-label="Id del módulo" required /></label>
        <p className="meta">El id aparece al crear el módulo. Texto, video de YouTube o Vimeo, o enlace de PDF.</p>
        <label>Título<input name="titulo" aria-label="Título de la lección" required /></label>
        <label>Tipo
          <select name="tipo" aria-label="Tipo de lección"><option value="texto">Texto</option><option value="video">Video</option><option value="pdf">PDF</option></select>
        </label>
        <label>Contenido<textarea name="cuerpo" rows={4} aria-label="Contenido de la lección" /></label>
        <label>Enlace de video<input name="video_url" placeholder="https://www.youtube.com/watch?v=" aria-label="Enlace de video" /></label>
        <label>Enlace del PDF<input name="pdf_url" aria-label="Enlace del PDF" /></label>
        <button type="submit" className="btn btn-fantasma">Agregar lección</button>
      </form>

      <form className="panel-form" onSubmit={(evento) => {
        evento.preventDefault();
        const datosForm = new FormData(evento.currentTarget);
        enviar('/admin/cursos/articulos', {
          titulo: datosForm.get('titulo'),
          resumen: datosForm.get('resumen'),
          cuerpo: datosForm.get('cuerpo'),
          categoria: datosForm.get('categoria'),
          destacado: datosForm.get('destacado') === 'on',
        }, 'Artículo publicado en Conoce La Maná.');
        evento.currentTarget.reset();
      }}>
        <h3>Artículo de divulgación</h3>
        <label>Título<input name="titulo" required aria-label="Título del artículo" /></label>
        <label>Resumen<input name="resumen" required aria-label="Resumen del artículo" /></label>
        <label>Texto<textarea name="cuerpo" rows={4} required aria-label="Texto del artículo" /></label>
        <label>Categoría<input name="categoria" defaultValue="ciudadania" aria-label="Categoría del artículo" /></label>
        <label className="check"><input name="destacado" type="checkbox" /> Destacado</label>
        <button type="submit" className="btn btn-pino">Publicar artículo</button>
      </form>

      <h3>Inscritos {cursoId ? `del curso ${cursoId}` : ''}</h3>
      {cursoId && <p><a href={`/api/admin/cursos/${cursoId}/inscritos.csv`} onClick={async (evento) => {
        evento.preventDefault();
        const respuesta = await fetch(`/api/admin/cursos/${cursoId}/inscritos.csv`, { headers: { Authorization: `Bearer ${token}` } });
        const blob = await respuesta.blob();
        const url = URL.createObjectURL(blob);
        const enlace = document.createElement('a');
        enlace.href = url;
        enlace.download = `inscritos-${cursoId}.csv`;
        enlace.click();
        URL.revokeObjectURL(url);
      }}>Exportar CSV</a></p>}
      {inscritos.length === 0 && <EstadoVacio titulo="Nadie inscrito" texto="Cuando alguien use el formulario del curso, aparece aquí." />}
      <ul className="lista-admin">
        {inscritos.map((persona) => (
          <li key={persona.id}>
            <strong>{persona.nombre}</strong>
            <span className="meta">{persona.documento} · {persona.email}</span>
            <label>Estado
              <select value={persona.estado} aria-label={`Estado de ${persona.nombre}`} onChange={(e) => cambiarEstado(persona.id, e.target.value)}>
                {ESTADOS.map((estado) => <option key={estado} value={estado}>{estado}</option>)}
              </select>
            </label>
          </li>
        ))}
      </ul>
    </div>
  );
}
