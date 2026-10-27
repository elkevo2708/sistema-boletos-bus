import { useState } from 'react';
import { solicitar } from '../api';

const VACIO = { nombre: '', email: '', mensaje: '' };

export default function PortalContacto() {
  const [datos, setDatos] = useState(VACIO);
  const [aviso, setAviso] = useState('');
  const [error, setError] = useState('');
  const [ocupado, setOcupado] = useState(false);

  async function enviar(event) {
    event.preventDefault();
    setError('');
    setAviso('');
    if (datos.nombre.trim().length < 3 || datos.mensaje.trim().length < 8 || !datos.email.includes('@')) {
      setError('Escriba nombre, un correo válido y un mensaje de al menos 8 caracteres.');
      return;
    }
    setOcupado(true);
    try {
      await solicitar('/turismo/contacto', { method: 'POST', body: datos });
      setAviso('Mensaje recibido. Taquilla lo verá en la sección Turismo.');
      setDatos(VACIO);
    } catch (err) {
      setError(err.message);
    } finally {
      setOcupado(false);
    }
  }

  return (
    <section className="portal-bloque portal-contacto">
      <div>
        <p className="sobrelinea">La Maná</p>
        <h1>Contacto</h1>
        <p>Este buzón es del portal de turismo. No confirma una reserva de finca ni un pasaje. Los pasajes se compran en Transporte.</p>
        <p><a href="mailto:turismo@lamana.ec">turismo@lamana.ec</a></p>
      </div>
      <form className="panel-form" noValidate onSubmit={enviar}>
        <h2>Enviar un mensaje</h2>
        <label>
          Nombre
          <input value={datos.nombre} onChange={(e) => setDatos({ ...datos, nombre: e.target.value })} aria-label="Nombre" />
        </label>
        <label>
          Correo
          <input type="email" value={datos.email} onChange={(e) => setDatos({ ...datos, email: e.target.value })} aria-label="Correo" />
        </label>
        <label>
          Mensaje
          <textarea value={datos.mensaje} onChange={(e) => setDatos({ ...datos, mensaje: e.target.value })} aria-label="Mensaje" rows={5} />
        </label>
        {error && <p className="aviso" role="alert">{error}</p>}
        {aviso && <p className="aviso-ok" role="status">{aviso}</p>}
        <button type="submit" className="btn btn-portal" disabled={ocupado} aria-label="Enviar mensaje">
          {ocupado ? 'Enviando…' : 'Enviar mensaje'}
        </button>
      </form>
    </section>
  );
}
