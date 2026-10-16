import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { solicitar, traerArchivo, urlSocket } from '../api';
import FacturacionCampos from '../componentes/FacturacionCampos';
import { useAuth } from '../contexto/AuthContext';
import { cuentaRegresiva, formatearFechaHora, formatearPesos, instanteColombia } from '../formato';
import { identificacionValida } from '../identificacion';

const ETIQUETA = {
  libre: 'libre',
  ocupado: 'ocupado',
  bloqueado: 'bloqueado',
  seleccionado: 'seleccionado',
};

export default function Asientos() {
  const { id } = useParams();
  const { usuario, token } = useAuth();
  const navegar = useNavigate();
  const [viaje, setViaje] = useState(null);
  const [asientos, setAsientos] = useState([]);
  const [piso, setPiso] = useState(1);
  const [seleccionado, setSeleccionado] = useState(null);
  const [pasajero, setPasajero] = useState({ nombre: '', documento: '' });
  const [reserva, setReserva] = useState(null);
  const [referencia, setReferencia] = useState('');
  const [qr, setQr] = useState('');
  const [pago, setPago] = useState(null);
  const [restante, setRestante] = useState(0);
  const [error, setError] = useState('');
  const [aviso, setAviso] = useState('');
  const [ocupado, setOcupado] = useState(false);
  const [metodo, setMetodo] = useState('tarjeta');
  const [tarjeta, setTarjeta] = useState({ numero: '', vence: '', cvv: '', nombre: '' });
  const [celular, setCelular] = useState('');
  const [facturaDatos, setFacturaDatos] = useState({
    tipo: 'cedula',
    identificacion: '',
    razon_social: '',
    direccion: '',
    email: '',
    telefono: '',
  });
  const [rideUrl, setRideUrl] = useState('');

  useEffect(() => {
    let vivo = true;
    solicitar(`/viajes/${id}/asientos`)
      .then((data) => {
        if (!vivo) return;
        setViaje(data.viaje);
        setAsientos(data.asientos);
        setPiso(data.asientos[0]?.piso ?? 1);
        const guardada = sessionStorage.getItem(`viaandina_reserva_${id}`);
        if (guardada) {
          const previa = JSON.parse(guardada);
          if (instanteColombia(previa.reservado_hasta) > Date.now()) {
            setReserva(previa);
            setSeleccionado(previa.asiento_id);
            setReferencia(previa.referencia || nuevaReferencia());
            setPasajero({ nombre: previa.pasajero_nombre, documento: previa.pasajero_documento });
          } else {
            sessionStorage.removeItem(`viaandina_reserva_${id}`);
          }
        }
      })
      .catch((err) => vivo && setError(err.message));
    return () => {
      vivo = false;
    };
  }, [id]);

  useEffect(() => {
    let vivo = true;
    let socket;
    let espera;
    const conectar = () => {
      socket = new WebSocket(urlSocket(id));
      socket.onmessage = (evento) => {
        const mensaje = JSON.parse(evento.data);
        if (mensaje.tipo !== 'asiento') return;
        setAsientos((actual) => actual.map((asiento) => (
          asiento.id === mensaje.asiento_id ? { ...asiento, estado: mensaje.estado } : asiento
        )));
        setSeleccionado((actual) => {
          if (actual === mensaje.asiento_id && mensaje.estado === 'ocupado') {
            const mia = sessionStorage.getItem(`viaandina_reserva_${id}`);
            if (!mia) setAviso('Ese asiento acaba de ocuparse. Elige otro.');
            if (!mia) return null;
          }
          if (actual === mensaje.asiento_id && mensaje.estado === 'libre') return null;
          return actual;
        });
      };
      socket.onclose = () => {
        if (vivo) espera = setTimeout(conectar, 1500);
      };
    };
    conectar();
    return () => {
      vivo = false;
      clearTimeout(espera);
      socket?.close();
    };
  }, [id]);

  useEffect(() => {
    if (usuario?.email) {
      setFacturaDatos((actual) => (actual.email ? actual : { ...actual, email: usuario.email }));
    }
  }, [usuario]);

  useEffect(() => () => {
    if (rideUrl) URL.revokeObjectURL(rideUrl);
  }, [rideUrl]);

  useEffect(() => {
    if (!reserva?.reservado_hasta || qr) return undefined;
    const fin = instanteColombia(reserva.reservado_hasta);
    const tick = () => setRestante(Math.max(0, fin - Date.now()));
    tick();
    const reloj = setInterval(tick, 250);
    return () => clearInterval(reloj);
  }, [reserva, qr]);

  const pisos = useMemo(
    () => [...new Set(asientos.map((asiento) => asiento.piso))].sort((a, b) => a - b),
    [asientos],
  );
  const delPiso = asientos.filter((asiento) => asiento.piso === piso);
  const asientoActivo = asientos.find((asiento) => asiento.id === seleccionado);

  function elegir(asiento) {
    if (reserva || qr) return;
    if (asiento.estado !== 'libre' && asiento.id !== seleccionado) return;
    setAviso('');
    setSeleccionado((actual) => (actual === asiento.id ? null : asiento.id));
  }

  async function reservar(event) {
    event.preventDefault();
    if (!token) {
      navegar(`/ingresar?siguiente=/viajes/${id}`);
      return;
    }
    if (!seleccionado) return;
    setOcupado(true);
    setError('');
    try {
      const data = await solicitar('/boletos/reservar', {
        method: 'POST',
        token,
        body: {
          viaje_id: Number(id),
          asiento_id: seleccionado,
          pasajero_nombre: pasajero.nombre,
          pasajero_documento: pasajero.documento,
        },
      });
      const ref = nuevaReferencia();
      const guardada = { ...data, referencia: ref };
      sessionStorage.setItem(`viaandina_reserva_${id}`, JSON.stringify(guardada));
      setReserva(guardada);
      setReferencia(ref);
      setAsientos((actual) => actual.map((asiento) => (
        asiento.id === data.asiento_id ? { ...asiento, estado: 'ocupado' } : asiento
      )));
    } catch (err) {
      setError(err.message);
      if (err.status === 401) navegar(`/ingresar?siguiente=/viajes/${id}`);
    } finally {
      setOcupado(false);
    }
  }

  function referenciaDePago() {
    if (metodo === 'tarjeta') {
      const ultimos = tarjeta.numero.replace(/\D/g, '').slice(-4);
      return `TARJ-${ultimos}-${referencia.slice(-6)}`;
    }
    if (metodo === 'payphone') return `PAY-${celular.replace(/\D/g, '').slice(-6)}-${referencia.slice(-4)}`;
    if (metodo === 'efectivo') return `VENT-${referencia.slice(-8)}`;
    return referencia;
  }

  function facturacionLista() {
    const direccion = facturaDatos.direccion.trim().length >= 4;
    const correo = !facturaDatos.email.trim() || facturaDatos.email.includes('@');
    if (facturaDatos.tipo === 'consumidor_final') return direccion && correo;
    return direccion && correo
      && identificacionValida(facturaDatos.tipo, facturaDatos.identificacion)
      && facturaDatos.razon_social.trim().length >= 3;
  }

  function pagoValido() {
    if (!facturacionLista()) return false;
    if (metodo === 'tarjeta') {
      const numero = tarjeta.numero.replace(/\D/g, '');
      return numero.length >= 15 && tarjeta.vence.length >= 4 && tarjeta.cvv.length >= 3 && tarjeta.nombre.trim().length > 2;
    }
    if (metodo === 'payphone') return celular.replace(/\D/g, '').length >= 10;
    if (metodo === 'transferencia') return referencia.trim().length >= 4;
    return true;
  }

  async function pagar(event) {
    event.preventDefault();
    if (!reserva || restante === 0 || !pagoValido()) return;
    setOcupado(true);
    setError('');
    try {
      const data = await solicitar(`/boletos/${reserva.codigo}/pagar`, {
        method: 'POST',
        token,
        body: {
          referencia_ext: referenciaDePago(),
          metodo,
          facturacion: {
            tipo: facturaDatos.tipo,
            identificacion: facturaDatos.identificacion.trim(),
            razon_social: facturaDatos.razon_social.trim(),
            direccion: facturaDatos.direccion.trim(),
            email: facturaDatos.email.trim() || null,
            telefono: facturaDatos.telefono.trim() || null,
          },
        },
      });
      setPago(data);
      setQr(data.qr_png_base64);
      if (data.factura?.id) {
        const blob = await traerArchivo(`/facturacion/${data.factura.id}/ride`, token);
        setRideUrl(URL.createObjectURL(blob));
      }
      sessionStorage.removeItem(`viaandina_reserva_${id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setOcupado(false);
    }
  }

  async function cancelar() {
    if (!reserva) return;
    setOcupado(true);
    setError('');
    try {
      await solicitar(`/boletos/${reserva.codigo}/cancelar`, { method: 'POST', token });
      sessionStorage.removeItem(`viaandina_reserva_${id}`);
      setReserva(null);
      setSeleccionado(null);
      setAsientos((actual) => actual.map((asiento) => (
        asiento.id === reserva.asiento_id ? { ...asiento, estado: 'libre' } : asiento
      )));
      setAviso('Reserva cancelada. El asiento volvió a quedar libre.');
    } catch (err) {
      setError(err.message);
    } finally {
      setOcupado(false);
    }
  }

  if (!viaje && !error) return <p className="pagina">Cargando mapa del bus…</p>;
  if (!viaje) return <p className="pagina aviso" role="alert">{error}</p>;

  return (
    <div className="pagina">
      <p className="miga"><Link to="/">Salidas</Link> / {viaje.origen} → {viaje.destino}</p>
      <header className="cabecera-viaje">
        <div>
          <h1>{viaje.origen} → {viaje.destino}</h1>
          <p>
            Sale {formatearFechaHora(viaje.salida)} · llega {formatearFechaHora(viaje.llegada_est)}
            · disco {viaje.numero_disco}
          </p>
        </div>
        <p className="precio-grande">{formatearPesos(viaje.precio)}</p>
      </header>

      <div className="asientos-layout">
        <section className="bus" aria-label="Mapa de asientos">
          <div className="parabrisas" aria-hidden="true">Conductor</div>
          {pisos.length > 1 && (
            <div className="pisos" role="tablist" aria-label="Pisos del bus">
              {pisos.map((numero) => (
                <button
                  key={numero}
                  type="button"
                  role="tab"
                  aria-selected={piso === numero}
                  className={piso === numero ? 'activo' : ''}
                  onClick={() => setPiso(numero)}
                  aria-label={`Ver piso ${numero}`}
                >
                  Piso {numero}
                </button>
              ))}
            </div>
          )}
          <div className="rejilla">
            {delPiso.map((asiento) => {
              const esMio = seleccionado === asiento.id;
              const visual = esMio && asiento.estado === 'libre' ? 'seleccionado' : asiento.estado;
              return (
                <button
                  key={asiento.id}
                  type="button"
                  className={`asiento ${visual}`}
                  style={{ gridColumn: asiento.columna > 2 ? asiento.columna + 1 : asiento.columna, gridRow: asiento.fila }}
                  disabled={visual === 'ocupado' || visual === 'bloqueado' || Boolean(reserva)}
                  aria-pressed={esMio}
                  aria-label={`Asiento ${asiento.numero}, ${ETIQUETA[visual]}, ${asiento.tipo}, piso ${asiento.piso}`}
                  onClick={() => elegir(asiento)}
                >
                  {asiento.numero}
                </button>
              );
            })}
          </div>
          <ul className="leyenda">
            <li><i className="muestra libre" /> Libre</li>
            <li><i className="muestra seleccionado" /> Seleccionado</li>
            <li><i className="muestra ocupado" /> Ocupado</li>
            <li><i className="muestra bloqueado" /> Bloqueado</li>
          </ul>
        </section>

        <section className="panel-pasajero">
          {qr ? (
            <div className="exito">
              <p className="sobrelinea">Pago aprobado</p>
              <h2>Boleto {pago.codigo}</h2>
              <p>
                {pago.pasajero_nombre} · asiento {pago.asiento_numero}<br />
                {pago.origen} → {pago.destino} · {formatearFechaHora(pago.salida)}
              </p>
              <img src={`data:image/png;base64,${qr}`} alt={`Código QR del boleto ${pago.codigo}`} />
              <p className="meta">Referencia {pago.pago.referencia_ext}</p>
              {pago.factura && (
                <div className="factura-exito">
                  <p className="sobrelinea">Factura {pago.factura.numero}</p>
                  <p>
                    {pago.factura.razon_social_comprador}<br />
                    Clave de acceso {pago.factura.clave_acceso}
                  </p>
                  <p>
                    <span className={`estado estado-${pago.factura.estado}`}>{pago.factura.estado}</span>
                    {' '}· IVA {formatearPesos(pago.factura.iva)} · total {formatearPesos(pago.factura.total)}
                  </p>
                  <p><Link to="/mis-facturas">Mis facturas</Link></p>
                  {rideUrl && (
                    <iframe className="ride-frame" title={`RIDE ${pago.factura.numero}`} src={rideUrl} />
                  )}
                </div>
              )}
            </div>
          ) : (
            <form onSubmit={reserva ? pagar : reservar}>
              <h2>{reserva ? 'Confirmar pago' : 'Datos del pasajero'}</h2>
              {asientoActivo && (
                <p className="meta">
                  Asiento {asientoActivo.numero} · {asientoActivo.tipo} · piso {asientoActivo.piso}
                </p>
              )}
              <label>
                Nombre del pasajero
                <input
                  value={pasajero.nombre}
                  onChange={(e) => setPasajero({ ...pasajero, nombre: e.target.value })}
                  required
                  minLength={3}
                  maxLength={180}
                  disabled={Boolean(reserva)}
                  autoComplete="name"
                  aria-label="Nombre del pasajero"
                />
              </label>
              <label>
                Documento
                <input
                  value={pasajero.documento}
                  onChange={(e) => setPasajero({ ...pasajero, documento: e.target.value })}
                  required
                  minLength={5}
                  maxLength={20}
                  disabled={Boolean(reserva)}
                  autoComplete="off"
                  aria-label="Documento del pasajero"
                />
              </label>
              {reserva && (
                <>
                  <p className="reloj" aria-live="polite">
                    {restante > 0
                      ? `Reserva ${reserva.codigo} vigente por ${cuentaRegresiva(restante)}`
                      : 'La reserva expiró'}
                  </p>
                  <fieldset className="metodos">
                    <legend>Método de pago</legend>
                    {METODOS.map((opcion) => (
                      <label key={opcion.id} className={metodo === opcion.id ? 'metodo activo' : 'metodo'}>
                        <input
                          type="radio"
                          name="metodo"
                          value={opcion.id}
                          checked={metodo === opcion.id}
                          onChange={() => setMetodo(opcion.id)}
                        />
                        <MetodoIcono id={opcion.id} />
                        <span>
                          <strong>{opcion.titulo}</strong>
                          <small>{opcion.detalle}</small>
                        </span>
                      </label>
                    ))}
                  </fieldset>
                  {metodo === 'tarjeta' && (
                    <div className="datos-pago">
                      <label>
                        Número de tarjeta
                        <input inputMode="numeric" autoComplete="off" aria-label="Número de tarjeta" value={tarjeta.numero} onChange={(e) => setTarjeta({ ...tarjeta, numero: e.target.value })} placeholder="ACCT-000015" />
                      </label>
                      <div className="dos">
                        <label>
                          Vence
                          <input autoComplete="off" aria-label="Vencimiento" value={tarjeta.vence} onChange={(e) => setTarjeta({ ...tarjeta, vence: e.target.value })} placeholder="MM/AA" />
                        </label>
                        <label>
                          CVV
                          <input autoComplete="off" aria-label="Código de seguridad" value={tarjeta.cvv} onChange={(e) => setTarjeta({ ...tarjeta, cvv: e.target.value })} placeholder="123" />
                        </label>
                      </div>
                      <label>
                        Nombre en la tarjeta
                        <input autoComplete="off" aria-label="Nombre en la tarjeta" value={tarjeta.nombre} onChange={(e) => setTarjeta({ ...tarjeta, nombre: e.target.value })} />
                      </label>
                      <p className="meta">El número no sale de este navegador. El cargo es simulado.</p>
                    </div>
                  )}
                  {metodo === 'transferencia' && (
                    <div className="datos-pago">
                      <p>Banco del Pacífico · Cooperativa La Maná · cuenta corriente 2100456789. Use esta referencia al transferir.</p>
                      <label>
                        Referencia de la transferencia
                        <input value={referencia} onChange={(e) => setReferencia(e.target.value)} required minLength={4} maxLength={64} aria-label="Referencia de la transferencia" />
                      </label>
                    </div>
                  )}
                  {metodo === 'payphone' && (
                    <div className="datos-pago">
                      <label>
                        Celular de la billetera
                        <input inputMode="tel" aria-label="Celular PayPhone" value={celular} onChange={(e) => setCelular(e.target.value)} placeholder="0991234567" />
                      </label>
                      <p className="meta">En producción aquí se abriría PayPhone. Esta pasarela está simulada.</p>
                    </div>
                  )}
                  {metodo === 'efectivo' && (
                    <p className="aviso-ok">Pague en la ventanilla del terminal de La Maná antes de la salida. El QR es su orden de pago.</p>
                  )}
                  <FacturacionCampos valor={facturaDatos} onChange={setFacturaDatos} token={token} />
                </>
              )}
              {error && <p className="aviso" role="alert">{error}</p>}
              {aviso && <p className="aviso-ok" role="status">{aviso}</p>}
              {!usuario && !reserva && (
                <p className="aviso-ok">Para reservar necesitas <Link to={`/ingresar?siguiente=/viajes/${id}`}>ingresar</Link>.</p>
              )}
              {reserva ? (
                <div className="acciones">
                  <button
                    type="submit"
                    className="btn btn-arcilla"
                    disabled={ocupado || restante === 0 || !pagoValido()}
                    aria-label="Pagar reserva"
                  >
                    Pagar {formatearPesos(reserva.precio)}
                  </button>
                  <button type="button" className="btn btn-fantasma" onClick={cancelar} disabled={ocupado} aria-label="Cancelar reserva">
                    Cancelar reserva
                  </button>
                </div>
              ) : (
                <button
                  type="submit"
                  className="btn btn-arcilla"
                  disabled={!seleccionado || ocupado}
                  aria-label="Reservar asiento seleccionado"
                >
                  Reservar por 10 minutos
                </button>
              )}
            </form>
          )}
        </section>
      </div>
    </div>
  );
}

function nuevaReferencia() {
  const aleatorio = crypto.randomUUID().replace(/-/g, '').slice(0, 12).toUpperCase();
  return `SIM-${aleatorio}`;
}

const METODOS = [
  { id: 'tarjeta', titulo: 'Tarjeta de crédito o débito', detalle: 'Cargo simulado, listo para una pasarela real' },
  { id: 'transferencia', titulo: 'Transferencia bancaria', detalle: 'Banco del Pacífico' },
  { id: 'payphone', titulo: 'PayPhone / billeteras', detalle: 'Confirme el cobro en el celular' },
  { id: 'efectivo', titulo: 'Efectivo en ventanilla', detalle: 'Terminal de La Maná' },
];

function MetodoIcono({ id }) {
  const comun = { width: 36, height: 24, viewBox: '0 0 36 24', 'aria-hidden': true };
  if (id === 'tarjeta') {
    return <svg {...comun}><rect width="36" height="24" rx="4" fill="#163e75" /><rect y="6" width="36" height="5" fill="#e4c98a" /></svg>;
  }
  if (id === 'transferencia') {
    return <svg {...comun}><rect width="36" height="24" rx="4" fill="#0f3d32" /><path d="M8 16h20M12 8h12" stroke="#fff" strokeWidth="2" /></svg>;
  }
  if (id === 'payphone') {
    return <svg {...comun}><rect x="10" y="1" width="16" height="22" rx="3" fill="#1f6f78" /><rect x="13" y="4" width="10" height="12" rx="1" fill="#f6f1e7" /></svg>;
  }
  return <svg {...comun}><rect width="36" height="24" rx="4" fill="#b5522a" /><circle cx="18" cy="12" r="5" fill="#f6f1e7" /></svg>;
}
