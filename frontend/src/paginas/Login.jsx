import { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { solicitar } from '../api';
import { useAuth } from '../contexto/AuthContext';

export default function Login() {
  const [modo, setModo] = useState('ingresar');
  const [error, setError] = useState('');
  const [ocupado, setOcupado] = useState(false);
  const { iniciar } = useAuth();
  const navegar = useNavigate();
  const [params] = useSearchParams();
  const siguiente = params.get('siguiente') || '/';

  async function alEnviar(event) {
    event.preventDefault();
    const datos = new FormData(event.currentTarget);
    setOcupado(true);
    setError('');
    try {
      const respuesta = modo === 'ingresar'
        ? await solicitar('/auth/login', {
          method: 'POST',
          form: { username: datos.get('email'), password: datos.get('password') },
        })
        : await solicitar('/auth/registro', {
          method: 'POST',
          body: {
            nombre: datos.get('nombre'),
            apellido: datos.get('apellido'),
            documento: datos.get('documento'),
            email: datos.get('email'),
            password: datos.get('password'),
            telefono: datos.get('telefono') || null,
          },
        });
      iniciar(respuesta);
      navegar(siguiente.startsWith('/') ? siguiente : '/');
    } catch (err) {
      setError(err.message);
    } finally {
      setOcupado(false);
    }
  }

  return (
    <div className="pagina estrecha">
      <div className="pestanas" role="tablist" aria-label="Acceso">
        <button type="button" role="tab" aria-selected={modo === 'ingresar'} className={modo === 'ingresar' ? 'activo' : ''} onClick={() => setModo('ingresar')} aria-label="Ingresar con una cuenta existente">
          Ingresar
        </button>
        <button type="button" role="tab" aria-selected={modo === 'crear'} className={modo === 'crear' ? 'activo' : ''} onClick={() => setModo('crear')} aria-label="Crear una cuenta nueva">
          Crear cuenta
        </button>
      </div>
      <form className="panel-form" onSubmit={alEnviar}>
        <h1>{modo === 'ingresar' ? 'Bienvenida de nuevo' : 'Crea tu cuenta'}</h1>
        {modo === 'crear' && (
          <>
            <div className="dos">
              <label>
                Nombre
                <input name="nombre" required minLength={1} maxLength={120} autoComplete="given-name" aria-label="Nombre" />
              </label>
              <label>
                Apellido
                <input name="apellido" required minLength={1} maxLength={120} autoComplete="family-name" aria-label="Apellido" />
              </label>
            </div>
            <label>
              Documento
              <input name="documento" required minLength={5} maxLength={20} aria-label="Documento" />
            </label>
            <label>
              Teléfono
              <input name="telefono" maxLength={30} autoComplete="tel" aria-label="Teléfono" />
            </label>
          </>
        )}
        <label>
          Correo
          <input name="email" type="email" required autoComplete="email" aria-label="Correo electrónico" />
        </label>
        <label>
          Contraseña
          <input
            name="password"
            type="password"
            required
            minLength={8}
            maxLength={72}
            autoComplete={modo === 'ingresar' ? 'current-password' : 'new-password'}
            aria-label="Contraseña"
          />
        </label>
        {error && <p className="aviso" role="alert">{error}</p>}
        <button type="submit" className="btn btn-arcilla" disabled={ocupado} aria-label={modo === 'ingresar' ? 'Ingresar' : 'Crear cuenta'}>
          {ocupado ? 'Un momento…' : (modo === 'ingresar' ? 'Ingresar' : 'Crear cuenta')}
        </button>
        <p className="meta"><Link to="/transporte">Volver a las salidas</Link> · <Link to="/">Portal de turismo</Link></p>
      </form>
    </div>
  );
}
