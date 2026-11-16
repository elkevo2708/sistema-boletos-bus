import { CONSUMIDOR_FINAL, validarIdentificacion } from '../identificacion';
import { useConsultaIdentificacion } from '../consultaIdentificacion';

const TIPOS = [
  ['cedula', 'Cédula'],
  ['ruc', 'RUC'],
  ['pasaporte', 'Pasaporte'],
  ['consumidor_final', 'Consumidor final'],
];

export default function FacturacionCampos({ valor, onChange, token }) {
  const error = valor.identificacion
    ? validarIdentificacion(valor.tipo, valor.identificacion)
    : '';
  const consulta = useConsultaIdentificacion({
    token,
    tipo: valor.tipo,
    identificacion: valor.identificacion,
    onEncontrado: (data) => {
      onChange((actual) => {
        if (actual.identificacion.trim() !== data.identificacion) return actual;
        return {
          ...actual,
          razon_social: data.razon_social || actual.razon_social,
          direccion: data.direccion || actual.direccion,
          email: data.email || actual.email,
          telefono: data.telefono || actual.telefono,
        };
      });
    },
  });

  function cambiarTipo(tipo) {
    if (tipo === 'consumidor_final') {
      onChange({
        ...valor,
        tipo,
        identificacion: CONSUMIDOR_FINAL,
        razon_social: 'CONSUMIDOR FINAL',
      });
      return;
    }
    onChange({
      ...valor,
      tipo,
      identificacion: valor.tipo === 'consumidor_final' ? '' : valor.identificacion,
      razon_social: valor.tipo === 'consumidor_final' ? '' : valor.razon_social,
    });
  }

  const bloqueado = valor.tipo === 'consumidor_final';

  return (
    <fieldset className="facturacion">
      <legend>Datos de facturación</legend>
      <label>
        Tipo de identificación
        <select
          value={valor.tipo}
          onChange={(e) => cambiarTipo(e.target.value)}
          aria-label="Tipo de identificación"
        >
          {TIPOS.map(([id, etiqueta]) => (
            <option key={id} value={id}>{etiqueta}</option>
          ))}
        </select>
      </label>
      <label>
        Identificación
        <input
          value={valor.identificacion}
          onChange={(e) => onChange({ ...valor, identificacion: e.target.value })}
          required
          minLength={5}
          maxLength={20}
          disabled={bloqueado}
          autoComplete="off"
          aria-label="Identificación del comprador"
          inputMode={valor.tipo === 'pasaporte' ? 'text' : 'numeric'}
        />
      </label>
      {error && <p className="aviso" role="alert">{error}</p>}
      {!error && consulta.estado === 'consultando' && (
        <p className="consultando" role="status">{consulta.aviso}</p>
      )}
      {!error && consulta.estado === 'vacio' && (
        <p className="aviso" role="status">No encontrado, ingréselo manualmente.</p>
      )}
      {!error && consulta.estado === 'encontrado' && (
        <p className="aviso-ok" role="status">{consulta.aviso}</p>
      )}
      {!error && consulta.estado === 'error' && (
        <p className="aviso" role="status">{consulta.aviso}</p>
      )}
      <label>
        Nombres o razón social
        <input
          value={valor.razon_social}
          aria-busy={consulta.estado === 'consultando'}
          onChange={(e) => onChange({ ...valor, razon_social: e.target.value })}
          required
          minLength={3}
          maxLength={300}
          disabled={bloqueado}
          autoComplete="organization"
          aria-label="Razón social"
        />
      </label>
      <label>
        Dirección
        <input
          value={valor.direccion}
          onChange={(e) => onChange({ ...valor, direccion: e.target.value })}
          required
          minLength={4}
          maxLength={300}
          autoComplete="street-address"
          aria-label="Dirección del comprador"
        />
      </label>
      <div className="dos">
        <label>
          Correo
          <input
            type="email"
            value={valor.email}
            onChange={(e) => onChange({ ...valor, email: e.target.value })}
            autoComplete="email"
            aria-label="Correo para la factura"
          />
        </label>
        <label>
          Teléfono
          <input
            value={valor.telefono}
            onChange={(e) => onChange({ ...valor, telefono: e.target.value })}
            autoComplete="tel"
            aria-label="Teléfono del comprador"
          />
        </label>
      </div>
    </fieldset>
  );
}
