import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { solicitar, urlSocket } from '../api';
import { useAuth } from '../contexto/AuthContext';
import { cuentaRegresiva, formatearFechaHora, formatearPesos, instanteColombia } from '../formato';

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

  async function pagar(event) {
    event.preventDefault();
    if (!reserva || restante === 0) return;
    setOcupado(true);
    setError('');
    try {
      const data = await solicitar(`/boletos/${reserva.codigo}/pagar`, {
        method: 'POST',
        token,
        body: { referencia_ext: referencia },
      });
      setPago(data);
      setQr(data.qr_png_base64);
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
                  <label>
                    Referencia de pago simulada
                    <input
                      value={referencia}
                      onChange={(e) => setReferencia(e.target.value)}
                      required
                      minLength={4}
                      maxLength={64}
                      aria-label="Referencia de pago simulada"
                    />
                  </label>
                </>
              )}
              {error && <p className="aviso" role="alert">{error}</p>}
              {aviso && <p className="nota" role="status">{aviso}</p>}
              {!usuario && !reserva && (
                <p className="nota">Para reservar necesitas <Link to={`/ingresar?siguiente=/viajes/${id}`}>ingresar</Link>.</p>
              )}
              {reserva ? (
                <div className="acciones">
                  <button
                    type="submit"
                    className="btn btn-arcilla"
                    disabled={ocupado || restante === 0 || referencia.trim().length < 4}
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
