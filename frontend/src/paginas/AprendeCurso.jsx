import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { solicitar } from '../api';
import { useConsultaIdentificacion } from '../consultaIdentificacion';
import { useAuth } from '../contexto/AuthContext';
import { Aviso, EncabezadoPagina, Esqueleto, Insignia } from '../ui/ui';

function videoIncrustado(url) {
  if (!url) return '';
  const youtube = url.match(/(?:v=|youtu\.be\/|embed\/)([\w-]{6,})/);
  if (youtube) return `https://www.youtube.com/embed/${youtube[1]}`;
  const vimeo = url.match(/vimeo\.com\/(\d+)/);
  if (vimeo) return `https://player.vimeo.com/video/${vimeo[1]}`;
  return '';
}

export default function AprendeCurso() {
  const { slug } = useParams();
  const { token, usuario } = useAuth();
  const [curso, setCurso] = useState(null);
  const [error, setError] = useState('');
  const [aviso, setAviso] = useState('');
  const [form, setForm] = useState({ nombre: '', documento: '', email: usuario?.email || '', telefono: '' });
  const [hechas, setHechas] = useState([]);
  const consulta = useConsultaIdentificacion({
    token,
    tipo: 'cedula',
    identificacion: form.documento,
    onEncontrado: (dato) => setForm((actual) => ({ ...actual, nombre: dato.razon_social || actual.nombre })),
  });

  useEffect(() => {
    setCurso(null);
    solicitar(`/aprende/cursos/${slug}`).then(setCurso).catch((err) => setError(err.message));
  }, [slug]);

  useEffect(() => {
    if (!token) return;
    solicitar(`/aprende/progreso/${slug}`, { token }).then((dato) => setHechas(dato.lecciones || [])).catch(() => {});
  }, [token, slug]);

  async function inscribir(evento) {
    evento.preventDefault();
    setError('');
    setAviso('');
    try {
      const respuesta = await solicitar(`/aprende/cursos/${slug}/inscripcion`, { method: 'POST', body: form });
      setAviso(`Inscripción recibida en «${respuesta.curso}». Quedan ${respuesta.cupos_restantes} cupos.`);
      setCurso(await solicitar(`/aprende/cursos/${slug}`));
    } catch (err) {
      setError(err.message);
    }
  }

  async function completar(leccionId) {
    if (!token) return;
    await solicitar(`/aprende/lecciones/${leccionId}/completar`, { method: 'POST', token });
    setHechas((actual) => (actual.includes(leccionId) ? actual : [...actual, leccionId]));
  }

  if (error && !curso) return <p className="pagina aviso" role="alert">{error}</p>;
  if (!curso) return <div className="pagina"><Esqueleto lineas={4} /></div>;
  const lleno = curso.ocupados >= curso.cupos;

  return (
    <>
      <EncabezadoPagina
        kicker={curso.categoria || 'Curso'}
        titulo={curso.titulo}
        bajada={curso.resumen}
        imagen={curso.imagen || '/turismo/cacao.jpg'}
        miga={<><Link to="/aprende">Aprende</Link> / {curso.titulo}</>}
      />
      <article className="portal-bloque ficha-cuerpo">
        <p className="curso-meta">
          <Insignia tono="turquesa">{curso.modalidad}</Insignia>
          <Insignia>{curso.nivel}</Insignia>
          <Insignia tono="verde">{curso.duracion_horas} h</Insignia>
          {curso.certificado && <Insignia tono="amarillo">Con certificado</Insignia>}
          {curso.ejemplo && <Insignia>Ejemplo</Insignia>}
        </p>
        <p>{curso.descripcion}</p>
        <p><strong>Instructor:</strong> {curso.instructor || 'Por confirmar'} {curso.institucion && `· ${curso.institucion}`}</p>
        <p><strong>Cupos:</strong> {curso.ocupados} de {curso.cupos}. {curso.lugar && `Lugar: ${curso.lugar}.`} {curso.inicio && ` Inicia ${curso.inicio}.`}</p>
        <h2>Objetivos</h2>
        {curso.objetivos.split('\n').filter(Boolean).map((linea) => <p key={linea}>{linea}</p>)}
        {curso.requisitos && <p><strong>Requisitos:</strong> {curso.requisitos}</p>}
        <h2>Temario</h2>
        {curso.modulos.map((modulo) => (
          <section key={modulo.id}>
            <h3>{modulo.titulo}</h3>
            {modulo.lecciones.map((leccion) => {
              const video = videoIncrustado(leccion.video_url);
              return (
                <article key={leccion.id} className="panel-form">
                  <h4>{leccion.titulo}</h4>
                  <p>{leccion.cuerpo}</p>
                  {video && <iframe title={leccion.titulo} src={video} className="curso-video" allowFullScreen />}
                  {leccion.pdf_url && <p><a href={leccion.pdf_url}>Descargar PDF</a></p>}
                  {curso.modalidad !== 'presencial' && (
                    token ? (
                      <button type="button" className="btn btn-fantasma" disabled={hechas.includes(leccion.id)} onClick={() => completar(leccion.id)}>
                        {hechas.includes(leccion.id) ? 'Lección completada' : 'Marcar como completada'}
                      </button>
                    ) : <p className="meta"><Link to={`/ingresar?siguiente=/aprende/cursos/${slug}`}>Ingresa</Link> para guardar tu progreso.</p>
                  )}
                </article>
              );
            })}
          </section>
        ))}
        <h2>Inscripción</h2>
        {lleno ? <Aviso>Ya no quedan cupos.</Aviso> : (
          <form className="panel-form" noValidate onSubmit={inscribir}>
            <label>Nombre
              <input value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} aria-label="Nombre" required />
            </label>
            <p className="meta">Si iniciaste sesión, al escribir la cédula buscamos el nombre.</p>
            <label>Cédula
              <input value={form.documento} inputMode="numeric" onChange={(e) => setForm({ ...form, documento: e.target.value })} aria-label="Cédula" required />
            </label>
            {consulta.aviso && <p className="meta">{consulta.aviso}</p>}
            <label>Correo
              <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} aria-label="Correo" required />
            </label>
            <label>Teléfono
              <input value={form.telefono} onChange={(e) => setForm({ ...form, telefono: e.target.value })} aria-label="Teléfono" />
            </label>
            {error && <Aviso>{error}</Aviso>}
            {aviso && <Aviso tono="ok">{aviso}</Aviso>}
            <button type="submit" className="btn btn-portal">Inscribirme</button>
          </form>
        )}
      </article>
    </>
  );
}
