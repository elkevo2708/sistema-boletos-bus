import { useEffect, useMemo, useState } from 'react';
import { solicitar } from '../api';

function MapaPrevio({ pisos, filas }) {
  const cupo = pisos * filas * 4;
  if (!Number.isFinite(cupo) || pisos < 1 || filas < 1) return null;
  if (cupo > 100) {
    return <p className="aviso" role="alert">El bus no puede tener más de 100 asientos.</p>;
  }
  return (
    <div className="mapa-previo" aria-label="Vista previa de asientos">
      {Array.from({ length: pisos }, (_, indicePiso) => (
        <div key={indicePiso}>
          <p className="parabrisas">Piso {indicePiso + 1}</p>
          <div className="rejilla">
            {Array.from({ length: filas }, (_, fila) => (
              [1, 2, 3, 4].map((columna) => {
                const numero = indicePiso * filas * 4 + fila * 4 + columna;
                return (
                  <span
                    key={`${indicePiso}-${numero}`}
                    className={`puesto-previo ${columna === 1 || columna === 4 ? 'ventana' : 'pasillo'}`}
                    style={{ gridColumn: columna > 2 ? columna + 1 : columna, gridRow: fila + 1 }}
                  >
                    {numero}
                  </span>
                );
              })
            ))}
          </div>
        </div>
      ))}
      <p className="meta">{cupo} puestos. Verde es ventana y naranja es pasillo.</p>
    </div>
  );
}

export default function PanelFlota({ token, onCambio }) {
  const [ciudades, setCiudades] = useState([]);
  const [rutas, setRutas] = useState([]);
  const [buses, setBuses] = useState([]);
  const [error, setError] = useState('');
  const [aviso, setAviso] = useState('');
  const [pisos, setPisos] = useState(1);
  const [filas, setFilas] = useState(10);

  async function cargar() {
    const [listaCiudades, listaRutas, listaBuses] = await Promise.all([
      solicitar('/admin/ciudades', { token }),
      solicitar('/admin/rutas', { token }),
      solicitar('/admin/buses', { token }),
    ]);
    setCiudades(listaCiudades);
    setRutas(listaRutas);
    setBuses(listaBuses);
  }

  useEffect(() => {
    cargar().catch((err) => setError(err.message));
  }, [token]);

  function limpiar() {
    setError('');
    setAviso('');
  }

  async function crearCiudad(event) {
    event.preventDefault();
    const datos = new FormData(event.currentTarget);
    const nombre = String(datos.get('nombre') || '').trim();
    const departamento = String(datos.get('departamento') || '').trim();
    limpiar();
    if (nombre.length < 2 || departamento.length < 2) {
      setError('La ciudad y la provincia necesitan al menos 2 caracteres.');
      return;
    }
    try {
      const creada = await solicitar('/admin/ciudades', {
        method: 'POST',
        token,
        body: { nombre, departamento },
      });
      setAviso(`Ciudad ${creada.nombre} registrada.`);
      event.currentTarget.reset();
      await cargar();
      onCambio?.();
    } catch (err) {
      setError(err.message);
    }
  }

  async function borrarCiudad(ciudad) {
    if (!window.confirm(`¿Eliminar ${ciudad.nombre}?`)) return;
    limpiar();
    try {
      await solicitar(`/admin/ciudades/${ciudad.id}`, { method: 'DELETE', token });
      setAviso(`${ciudad.nombre} eliminada.`);
      await cargar();
      onCambio?.();
    } catch (err) {
      setError(err.message);
    }
  }

  async function crearRuta(event) {
    event.preventDefault();
    const datos = new FormData(event.currentTarget);
    const origen = Number(datos.get('origen_id'));
    const destino = Number(datos.get('destino_id'));
    const duracion = Number(datos.get('duracion_min'));
    const precio = String(datos.get('precio_base') || '').trim();
    limpiar();
    if (!origen || !destino) {
      setError('Selecciona el origen y el destino de la ruta.');
      return;
    }
    if (origen === destino) {
      setError('El origen y el destino deben ser distintos.');
      return;
    }
    if (!duracion || duracion < 1) {
      setError('La duración debe ser de al menos 1 minuto.');
      return;
    }
    if (!precio || Number(precio) <= 0) {
      setError('La tarifa base debe ser mayor que cero.');
      return;
    }
    try {
      const creada = await solicitar('/admin/rutas', {
        method: 'POST',
        token,
        body: { origen_id: origen, destino_id: destino, duracion_min: duracion, precio_base: precio },
      });
      setAviso(`Ruta ${creada.id} creada a ${precio} USD.`);
      event.currentTarget.reset();
      await cargar();
      onCambio?.();
    } catch (err) {
      setError(err.message);
    }
  }

  async function borrarRuta(ruta) {
    if (!window.confirm(`¿Eliminar ${ruta.origen} → ${ruta.destino}?`)) return;
    limpiar();
    try {
      await solicitar(`/admin/rutas/${ruta.id}`, { method: 'DELETE', token });
      setAviso(`Ruta ${ruta.origen} → ${ruta.destino} eliminada.`);
      await cargar();
      onCambio?.();
    } catch (err) {
      setError(err.message);
    }
  }

  async function crearBus(event) {
    event.preventDefault();
    const datos = new FormData(event.currentTarget);
    const placa = String(datos.get('placa') || '').trim();
    const disco = String(datos.get('numero_disco') || '').trim();
    const pisosBus = Number(datos.get('pisos'));
    const filasBus = Number(datos.get('filas'));
    limpiar();
    if (placa.length < 4) {
      setError('La placa debe tener al menos 4 caracteres.');
      return;
    }
    if (!disco) {
      setError('Indica el número de disco.');
      return;
    }
    if (![1, 2].includes(pisosBus) || filasBus < 1 || filasBus > 20) {
      setError('Usa 1 o 2 pisos y entre 1 y 20 filas.');
      return;
    }
    if (pisosBus * filasBus * 4 > 100) {
      setError('El bus no puede tener más de 100 asientos.');
      return;
    }
    try {
      const creado = await solicitar('/admin/buses', {
        method: 'POST',
        token,
        body: {
          placa,
          numero_disco: disco,
          pisos: pisosBus,
          filas: filasBus,
          estado: datos.get('estado'),
        },
      });
      setAviso(`Bus disco ${creado.numero_disco} creado con ${creado.asientos} asientos.`);
      event.currentTarget.reset();
      setPisos(1);
      setFilas(10);
      await cargar();
      onCambio?.();
    } catch (err) {
      setError(err.message);
    }
  }

  async function cambiarEstado(bus, estado) {
    limpiar();
    try {
      await solicitar(`/admin/buses/${bus.id}`, { method: 'PATCH', token, body: { estado } });
      setAviso(`Disco ${bus.numero_disco} quedó ${estado}.`);
      await cargar();
      onCambio?.();
    } catch (err) {
      setError(err.message);
    }
  }

  async function borrarBus(bus) {
    if (!window.confirm(`¿Eliminar el disco ${bus.numero_disco}?`)) return;
    limpiar();
    try {
      await solicitar(`/admin/buses/${bus.id}`, { method: 'DELETE', token });
      setAviso(`Disco ${bus.numero_disco} eliminado.`);
      await cargar();
      onCambio?.();
    } catch (err) {
      setError(err.message);
    }
  }

  const cupo = useMemo(() => pisos * filas * 4, [pisos, filas]);

  return (
    <div>
      {aviso && <p className="aviso-ok" role="status">{aviso}</p>}
      {error && <p className="aviso" role="alert">{error}</p>}
      <div className="rejilla-admin">
        <form className="panel-form" noValidate onSubmit={crearCiudad}>
          <h2>Nueva ciudad</h2>
          <label>
            Ciudad
            <input name="nombre" aria-label="Nombre de la ciudad" />
          </label>
          <label>
            Provincia
            <input name="departamento" aria-label="Provincia de la ciudad" />
          </label>
          <button type="submit" className="btn btn-arcilla" aria-label="Guardar ciudad">Guardar ciudad</button>
        </form>
        <form className="panel-form" noValidate onSubmit={crearRuta}>
          <h2>Nueva ruta</h2>
          <label>
            Origen
            <select name="origen_id" defaultValue="" aria-label="Ciudad de origen">
              <option value="">Selecciona</option>
              {ciudades.map((ciudad) => (
                <option key={ciudad.id} value={ciudad.id}>{ciudad.nombre} · {ciudad.departamento}</option>
              ))}
            </select>
          </label>
          <label>
            Destino
            <select name="destino_id" defaultValue="" aria-label="Ciudad de destino">
              <option value="">Selecciona</option>
              {ciudades.map((ciudad) => (
                <option key={ciudad.id} value={ciudad.id}>{ciudad.nombre} · {ciudad.departamento}</option>
              ))}
            </select>
          </label>
          <div className="dos">
            <label>
              Duración (min)
              <input name="duracion_min" type="number" min="1" defaultValue="90" aria-label="Duración de la ruta en minutos" />
            </label>
            <label>
              Tarifa base
              <input name="precio_base" type="number" min="0.01" step="0.01" aria-label="Tarifa base de la ruta" />
            </label>
          </div>
          <button type="submit" className="btn btn-arcilla" aria-label="Guardar ruta">Guardar ruta</button>
        </form>
      </div>

      <div className="rejilla-admin">
        <form className="panel-form" noValidate onSubmit={crearBus}>
          <h2>Nuevo bus</h2>
          <p className="meta">Cuatro asientos por fila. Las columnas 1 y 4 son ventana; 2 y 3 son pasillo.</p>
          <div className="dos">
            <label>
              Placa
              <input name="placa" aria-label="Placa del bus" />
            </label>
            <label>
              Disco
              <input name="numero_disco" aria-label="Número de disco" />
            </label>
          </div>
          <div className="dos">
            <label>
              Pisos
              <select name="pisos" value={pisos} onChange={(e) => setPisos(Number(e.target.value))} aria-label="Cantidad de pisos">
                <option value={1}>1 piso</option>
                <option value={2}>2 pisos</option>
              </select>
            </label>
            <label>
              Filas por piso
              <input name="filas" type="number" min="1" max="20" value={filas} onChange={(e) => setFilas(Number(e.target.value))} aria-label="Filas por piso" />
            </label>
          </div>
          <label>
            Estado
            <select name="estado" defaultValue="operativo" aria-label="Estado del bus">
              <option value="operativo">Operativo</option>
              <option value="mantenimiento">Mantenimiento</option>
              <option value="inactivo">Inactivo</option>
            </select>
          </label>
          <p className="meta">{cupo > 0 ? `${cupo} asientos` : 'Indica las filas'}.</p>
          <button type="submit" className="btn btn-arcilla" aria-label="Guardar bus">Guardar bus</button>
        </form>
        <MapaPrevio pisos={Number(pisos) || 0} filas={Number(filas) || 0} />
      </div>

      <section className="panel-form">
        <h2>Ciudades</h2>
        <ul className="lista-admin">
          {ciudades.map((ciudad) => (
            <li key={ciudad.id}>
              <strong>{ciudad.nombre}</strong>
              <span>{ciudad.departamento}</span>
              <div>
                <button type="button" onClick={() => borrarCiudad(ciudad)} aria-label={`Eliminar ciudad ${ciudad.nombre}`}>Eliminar</button>
              </div>
            </li>
          ))}
        </ul>
      </section>

      <section className="panel-form">
        <h2>Rutas</h2>
        <ul className="lista-admin">
          {rutas.map((ruta) => (
            <li key={ruta.id}>
              <strong>{ruta.origen} → {ruta.destino}</strong>
              <span>{ruta.duracion_min} min · {ruta.precio_base} USD</span>
              <div>
                <button type="button" onClick={() => borrarRuta(ruta)} aria-label={`Eliminar ruta ${ruta.origen} ${ruta.destino}`}>Eliminar</button>
              </div>
            </li>
          ))}
        </ul>
      </section>

      <section className="panel-form">
        <h2>Buses</h2>
        <ul className="lista-admin">
          {buses.map((bus) => (
            <li key={bus.id}>
              <strong>Disco {bus.numero_disco} · {bus.placa}</strong>
              <span>{bus.asientos} asientos · {bus.pisos} piso{bus.pisos > 1 ? 's' : ''} · {bus.estado}</span>
              <div>
                <button type="button" onClick={() => cambiarEstado(bus, bus.estado === 'operativo' ? 'mantenimiento' : 'operativo')} aria-label={`Cambiar estado del disco ${bus.numero_disco}`}>
                  {bus.estado === 'operativo' ? 'A mantenimiento' : 'Marcar operativo'}
                </button>
                <button type="button" onClick={() => borrarBus(bus)} aria-label={`Eliminar disco ${bus.numero_disco}`}>Eliminar</button>
              </div>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
