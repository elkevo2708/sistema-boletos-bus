import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Bell, Bus, Car, Compass, CreditCard, FileText, Images, LayoutDashboard, LogOut,
  Mail, Map, Megaphone, Moon, Newspaper, PanelLeft, Route, Search, Settings, Sun, Image as ImagenIcon,
} from 'lucide-react';
import { solicitar } from '../api';
import MarcaPortal from '../componentes/MarcaPortal';
import { useAuth } from '../contexto/AuthContext';
import { ahoraBogotaInput, fechaBogota, formatearFechaHora, formatearPesos } from '../formato';
import LogoRecorres from '../ui/LogoRecorres';
import { PanelAnuncios, PanelBlog, PanelGaleria } from './AdminContenido';
import { PanelEmisor, PanelFacturas } from './AdminFacturas';
import PanelFlota from './AdminFlota';
import AdminPagos from './AdminPagos';
import AdminPortada from './AdminPortada';
import AdminTaxis from './AdminTaxis';
import AdminTurismo from './AdminTurismo';
import EditorTextos from './EditorTextos';
import InicioEspacios from './InicioEspacios';
import PanelResumen from './PanelResumen';
import { MarcoEdicion } from '../ui/MarcoEdicion';

const ROLES = {
  administrador: 'Administración',
  operador_turismo: 'Operador de turismo',
  operador_transporte: 'Operador de transporte',
  operador_taxi: 'Operador de taxis',
};

function ficha(id, etiqueta, ver, frase, aparece, Icono) {
  return { id, etiqueta, ver, frase, aparece, Icono, titulo: etiqueta };
}

function menuDe(puede) {
  return {
    portal: puede.turismo ? [
      ficha('textos', 'Textos del inicio', '/', 'Los títulos y párrafos que están escritos en la página de inicio.', 'Inicio del portal, debajo de la portada.', Compass),
      ficha('sitio', 'Nombre del sitio', '/', 'El nombre que aparece en la pestaña del navegador.', 'La pestaña del navegador.', Settings),
      ficha('portada', 'Portada', '/', 'Las fotos grandes de arriba de todo.', 'Lo primero que se ve al abrir el portal.', ImagenIcon),
      ficha('atractivo', 'Atractivos', '/atractivos', 'Río, cascadas y pueblo.', 'Descubre y las tarjetas del inicio.', Map),
      ficha('parroquia', 'Parroquias', '/parroquias', 'La cabecera y las parroquias rurales.', 'Página Parroquias.', Map),
      ficha('gastronomia', 'Gastronomía', '/gastronomia', 'La mesa del subtrópico.', 'Página Gastronomía.', Map),
      ficha('hospedaje', 'Hospedaje', '/hospedaje', 'Tipos de alojamiento.', 'Página Hospedaje.', Map),
      ficha('actividad', 'Actividades', '/actividades', 'Caminata, río y bosque.', 'Página Vive.', Map),
      ficha('ruta', 'Rutas del cantón', '/rutas', 'Recorridos de un día, no los buses.', 'Página Rutas del portal.', Route),
      ficha('guia', 'Aprende', '/aprende', 'Cómo llegar y lo práctico.', 'Página Aprende.', Compass),
      ficha('emprendimiento', 'Emprendimientos', '/emprendimientos', 'Fichas de negocios. Las de ejemplo siguen marcadas.', 'Página Emprendimientos.', Map),
      ficha('directorio', 'Directorio', '/directorio', 'Servicios del cantón.', 'Página Directorio.', FileText),
      ficha('agenda', 'Agenda', '/agenda', 'Fechas que se publican en el inicio.', 'Agenda y el bloque de fechas del inicio.', Newspaper),
      ficha('galeria', 'Galería', '/galeria', 'Fotos del cantón.', 'Galería del portal.', Images),
      ficha('mensajes', 'Mensajes', '/contacto', 'Lo que escribe la gente desde Contacto.', 'No se publica; solo lo ves tú.', Mail),
      ficha('contacto', 'Datos de contacto', '/contacto', 'Correo, título y la frase del buzón.', 'Página Contacto y el pie.', Mail),
    ] : [],
    transporte: puede.transporte ? [
      ficha('textos', 'Textos de la página', '/transporte', 'Frases de la búsqueda y del pie.', 'Página de boletos y su pie.', Bus),
      ficha('portada', 'Portada', '/transporte', 'La foto grande de Transporte.', 'Arriba de la búsqueda de pasajes.', ImagenIcon),
      ficha('operacion', 'Viajes y tarifas', '/transporte', 'Crear salidas y cambiar el precio de una ruta.', 'La búsqueda pública de pasajes.', Route),
      ficha('flota', 'Buses', '/transporte', 'Unidades, asientos y estado.', 'El mapa de asientos de cada viaje.', Bus),
      ficha('pagos', 'Métodos de pago', '/transporte', 'Activar DeUna, tarjeta o PayPhone.', 'El paso de pago del pasaje.', CreditCard),
      ficha('facturas', 'Facturas', '/mis-facturas', 'Consultar y reenviar comprobantes.', 'Mis facturas, para quien compró.', FileText),
      ficha('emisor', 'Emisor SRI', '/transporte', 'Datos de quien emite la factura.', 'El PDF y el XML del pasaje.', Settings),
      ficha('blog', 'Noticias', '/transporte/noticias', 'Notas de la cooperativa.', 'Noticias de Transporte.', Newspaper),
      ficha('anuncios', 'Aviso promocional', '/transporte', 'La ventana que sale al entrar.', 'Una ventana sobre Transporte.', Megaphone),
      ficha('galeria', 'Galería', '/transporte/galeria', 'Fotos de buses y terminales.', 'Galería de Transporte.', Images),
    ] : [],
    taxi: puede.taxi ? [
      ficha('textos', 'Textos de la página', '/taxi', 'El título y la ayuda del mapa.', 'La hoja de pedido en /taxi.', Car),
      ficha('operacion', 'Compañías y tarifas', '/taxi', 'Arranque, kilómetro, minuto, mínima y recargo nocturno.', 'La cotización que ve quien pide el taxi. Las de ejemplo siguen marcadas.', Car),
    ] : [],
  };
}

export default function Admin() {
  const { usuario, token, refreshToken, cerrar } = useAuth();
  const navegar = useNavigate();
  const [rutas, setRutas] = useState([]);
  const [buses, setBuses] = useState([]);
  const [viajes, setViajes] = useState([]);
  const [ventas, setVentas] = useState(null);
  const [fecha, setFecha] = useState(fechaBogota(0));
  const [mensaje, setMensaje] = useState('');
  const [error, setError] = useState('');
  const [ocupado, setOcupado] = useState(false);
  const [modulo, setModulo] = useState('resumen');
  const [espacio, setEspacio] = useState('inicio');
  const [seccion, setSeccion] = useState('textos');
  const [menu, setMenu] = useState(false);
  const [pestana, setPestana] = useState('operacion');
  const [tablero, setTablero] = useState(null);
  const [cargandoTablero, setCargandoTablero] = useState(false);
  const [errorTablero, setErrorTablero] = useState('');
  const [rango, setRango] = useState({ desde: fechaBogota(-29), hasta: fechaBogota(0) });
  const [consulta, setConsulta] = useState('');
  const [avisosAbiertos, setAvisosAbiertos] = useState(false);
  const [oscuro, setOscuro] = useState(() => localStorage.getItem('lamana_panel_tema') === 'oscuro');
  const [colapsado, setColapsado] = useState(() => localStorage.getItem('lamana_panel_lado') === 'cerrado');

  const puede = {
    turismo: usuario?.rol === 'administrador' || usuario?.rol === 'operador_turismo',
    transporte: usuario?.rol === 'administrador' || usuario?.rol === 'operador_transporte',
    taxi: usuario?.rol === 'administrador' || usuario?.rol === 'operador_taxi',
  };
  const puedeTransporte = puede.transporte;
  const menus = useMemo(() => menuDe(puede), [usuario?.rol]);
  const menuActual = menus[espacio] || [];
  const carga = useRef(0);

  function recargarCatalogo() {
    const id = carga.current + 1;
    carga.current = id;
    return Promise.all([
      solicitar('/admin/rutas', { token }),
      solicitar('/admin/buses', { token }),
      solicitar('/admin/viajes', { token }),
    ]).then(([listaRutas, listaBuses, listaViajes]) => {
      if (carga.current !== id) return;
      setRutas(listaRutas);
      setBuses(listaBuses);
      setViajes(listaViajes);
    });
  }

  function consultarTablero(desde = rango.desde, hasta = rango.hasta) {
    if (!token) return;
    setRango({ desde, hasta });
    setCargandoTablero(true);
    setErrorTablero('');
    solicitar(`/admin/dashboard/resumen?desde=${desde}&hasta=${hasta}`, { token })
      .then(setTablero)
      .catch((err) => setErrorTablero(err.message))
      .finally(() => setCargandoTablero(false));
  }

  useEffect(() => {
    if (!token || !usuario) return;
    consultarTablero(fechaBogota(-29), fechaBogota(0));
  }, [token, usuario]);

  useEffect(() => {
    localStorage.setItem('lamana_panel_tema', oscuro ? 'oscuro' : 'claro');
  }, [oscuro]);

  useEffect(() => {
    localStorage.setItem('lamana_panel_lado', colapsado ? 'cerrado' : 'abierto');
  }, [colapsado]);

  useEffect(() => {
    if (!puedeTransporte) return;
    const id = carga.current + 1;
    carga.current = id;
    Promise.all([
      solicitar('/admin/rutas', { token }),
      solicitar('/admin/buses', { token }),
      solicitar('/admin/viajes', { token }),
      solicitar(`/admin/ventas?fecha=${fechaBogota(0)}`, { token }),
    ]).then(([listaRutas, listaBuses, listaViajes, reporte]) => {
      if (carga.current !== id) return;
      setRutas(listaRutas);
      setBuses(listaBuses);
      setViajes(listaViajes);
      setVentas(reporte);
    }).catch((err) => setError(err.message));
  }, [puedeTransporte, token]);

  async function crearViaje(event) {
    event.preventDefault();
    const datos = new FormData(event.currentTarget);
    const rutaId = datos.get('ruta_id');
    const busId = datos.get('bus_id');
    const salida = String(datos.get('salida') || '');
    const precio = String(datos.get('precio') || '').trim();
    setError('');
    setMensaje('');
    if (!rutaId) {
      setError('Selecciona la ruta del viaje.');
      return;
    }
    if (!busId) {
      setError('Selecciona el bus del viaje.');
      return;
    }
    if (!salida) {
      setError('Indica la fecha y hora de salida.');
      return;
    }
    if (salida <= ahoraBogotaInput()) {
      setError('La salida debe ser futura.');
      return;
    }
    if (precio && Number(precio) <= 0) {
      setError('El precio debe ser mayor que cero.');
      return;
    }
    const formulario = event.currentTarget;
    setOcupado(true);
    try {
      const creado = await solicitar('/admin/viajes', {
        method: 'POST',
        token,
        body: {
          ruta_id: Number(rutaId),
          bus_id: Number(busId),
          salida,
          precio: precio || null,
        },
      });
      setMensaje(`Viaje ${creado.id} creado. Llega ${formatearFechaHora(creado.llegada_est)} a ${formatearPesos(creado.precio)}.`);
      formulario.reset();
      await recargarCatalogo();
    } catch (err) {
      setError(err.message);
    } finally {
      setOcupado(false);
    }
  }

  async function cambiarTarifa(event) {
    event.preventDefault();
    const datos = new FormData(event.currentTarget);
    const rutaId = datos.get('ruta_id');
    const precio = String(datos.get('precio_base') || '').trim();
    setError('');
    setMensaje('');
    if (!rutaId) {
      setError('Selecciona la ruta a retarifar.');
      return;
    }
    if (!precio || Number(precio) <= 0) {
      setError('La tarifa debe ser mayor que cero.');
      return;
    }
    setOcupado(true);
    try {
      const actualizada = await solicitar(`/admin/rutas/${rutaId}/tarifa`, {
        method: 'PATCH',
        token,
        body: { precio_base: precio },
      });
      setMensaje(`Tarifa actualizada a ${formatearPesos(actualizada.precio_base)}. Quedó registro en auditoría.`);
      setRutas((actual) => actual.map((ruta) => (
        String(ruta.id) === String(rutaId) ? { ...ruta, precio_base: actualizada.precio_base } : ruta
      )));
    } catch (err) {
      setError(err.message);
    } finally {
      setOcupado(false);
    }
  }

  async function cancelarViaje(viaje) {
    if (!window.confirm(`¿Cancelar el viaje ${viaje.origen} → ${viaje.destino}?`)) return;
    setError('');
    setMensaje('');
    setOcupado(true);
    try {
      await solicitar(`/admin/viajes/${viaje.id}`, { method: 'DELETE', token });
      setMensaje(`Viaje ${viaje.id} cancelado.`);
      await recargarCatalogo();
    } catch (err) {
      setError(err.message);
    } finally {
      setOcupado(false);
    }
  }

  async function generarHorario() {
    setError('');
    setMensaje('');
    setOcupado(true);
    try {
      const resultado = await solicitar('/admin/horarios/generar', { method: 'POST', token });
      setMensaje(resultado.creados
        ? `Se programaron ${resultado.creados} salidas nuevas para los próximos 30 días.`
        : 'El horario de los próximos 30 días ya estaba completo.');
      await recargarCatalogo();
    } catch (err) {
      setError(err.message);
    } finally {
      setOcupado(false);
    }
  }

  async function consultarVentas(event) {
    event?.preventDefault();
    setOcupado(true);
    setError('');
    try {
      setVentas(await solicitar(`/admin/ventas?fecha=${fecha}`, { token }));
    } catch (err) {
      setError(err.message);
    } finally {
      setOcupado(false);
    }
  }

  async function salir() {
    if (refreshToken) {
      try {
        await solicitar('/auth/logout', { method: 'POST', body: { refresh_token: refreshToken } });
      } catch {
        /* la sesión local se cierra igual */
      }
    }
    cerrar();
    navegar('/');
  }

  function ir(siguienteEspacio, siguienteSeccion = 'textos') {
    setEspacio(siguienteEspacio);
    setSeccion(siguienteSeccion);
    setModulo(siguienteEspacio === 'portal' ? 'turismo' : siguienteEspacio);
    setPestana(siguienteSeccion);
    setMenu(false);
    setConsulta('');
    setAvisosAbiertos(false);
  }

  if (!usuario) {
    return (
      <div className="pagina estrecha">
        <MarcaPortal />
        <h1>Panel</h1>
        <p>Un solo ingreso para turismo, transporte y taxis.</p>
        <Link className="btn btn-pino" to="/ingresar?siguiente=/admin" aria-label="Ingresar al panel">Ingresar</Link>
      </div>
    );
  }

  if (!puede.turismo && !puede.transporte && !puede.taxi) {
    return (
      <div className="pagina estrecha">
        <MarcaPortal />
        <h1>Panel</h1>
        <p className="aviso" role="alert">Esta cuenta no administra un módulo.</p>
      </div>
    );
  }

  const entradas = [
    { id: 'inicio', etiqueta: 'Inicio', espacio: 'inicio' },
    { id: 'resumen', etiqueta: 'Resumen', espacio: 'resumen' },
    ...Object.entries(menus).flatMap(([clave, items]) => items.map((item) => ({ ...item, espacio: clave }))),
  ];
  const coincidencias = consulta.trim()
    ? entradas.filter((item) => item.etiqueta.toLowerCase().includes(consulta.trim().toLowerCase()))
    : [];
  const actual = menuActual.find((item) => item.id === seccion);
  const titulo = espacio === 'inicio' ? 'Elige un espacio' : espacio === 'resumen' ? 'Resumen' : (actual?.titulo || 'Panel');
  const iniciales = `${usuario.nombre?.[0] || ''}${usuario.apellido?.[0] || ''}`.toUpperCase();
  const iconoSolo = colapsado && !menu;
  const acento = ['portal', 'transporte', 'taxi'].includes(espacio) ? ` acento-${espacio}` : '';

  return (
    <div className={`saas${oscuro ? ' oscuro' : ''}${colapsado ? ' colapsado' : ''}${acento}`}>
      {menu && <button type="button" className="drawer-fondo" aria-label="Cerrar módulos" onClick={() => setMenu(false)} />}
      <aside className={menu ? 'saas-lado abierto' : 'saas-lado'} aria-label="Módulos del panel">
        <div className="saas-marca">
          <Link to="/" aria-label="La Maná Recorres, inicio">
            <LogoRecorres variante={iconoSolo ? 'isotipo' : 'horizontal'} clara decorativo />
          </Link>
          <button type="button" className="saas-colapsar" onClick={() => setColapsado((valor) => !valor)} aria-label={colapsado ? 'Expandir menú lateral' : 'Contraer menú lateral'}>
            <PanelLeft size={20} aria-hidden="true" />
          </button>
        </div>
        <nav className="saas-nav">
          <button type="button" className={espacio === 'inicio' ? 'activo' : ''} onClick={() => ir('inicio')} aria-label="Volver al inicio del panel">
            <LayoutDashboard size={20} strokeWidth={1.75} aria-hidden="true" />
            <span className="saas-etiqueta">Inicio</span>
          </button>
          <button type="button" className={espacio === 'resumen' ? 'activo' : ''} onClick={() => ir('resumen', 'resumen')} aria-label="Abrir resumen">
            <LayoutDashboard size={20} strokeWidth={1.75} aria-hidden="true" />
            <span className="saas-etiqueta">Resumen</span>
          </button>
          <button type="button" className="saas-tema-lado" onClick={() => setOscuro((valor) => !valor)} aria-pressed={oscuro} aria-label={oscuro ? 'Usar modo claro' : 'Usar modo oscuro'}>
            {oscuro ? <Sun size={20} aria-hidden="true" /> : <Moon size={20} aria-hidden="true" />}
            <span className="saas-etiqueta">{oscuro ? 'Modo claro' : 'Modo oscuro'}</span>
          </button>
          {menuActual.length > 0 && (
            <div className="saas-grupo">
              <p className="saas-grupo-titulo"><span>{espacio === 'portal' ? 'Portal del cantón' : espacio === 'transporte' ? 'Transporte' : 'Taxis'}</span></p>
              {menuActual.map((item) => (
                <button key={item.id} type="button" className={seccion === item.id ? 'activo' : ''} onClick={() => ir(espacio, item.id)} aria-label={`Abrir ${item.etiqueta}`}>
                  <item.Icono size={20} strokeWidth={1.75} aria-hidden="true" />
                  <span className="saas-etiqueta">{item.etiqueta}</span>
                </button>
              ))}
            </div>
          )}
        </nav>
      </aside>
      <div className="saas-principal">
      <header className="saas-top">
        <button type="button" className="btn btn-fantasma saas-abrir" onClick={() => setMenu(true)} aria-label="Abrir módulos del panel">
          <PanelLeft size={18} aria-hidden="true" /> <span>Módulos</span>
        </button>
        <div className="saas-espacios" role="group" aria-label="Cambiar de espacio">
          <button type="button" className={espacio === 'inicio' ? 'activo' : ''} onClick={() => ir('inicio')}>Inicio</button>
          {puede.turismo && <button type="button" className={espacio === 'portal' ? 'activo' : ''} onClick={() => ir('portal')}>Portal</button>}
          {puede.transporte && <button type="button" className={espacio === 'transporte' ? 'activo' : ''} onClick={() => ir('transporte')}>Transporte</button>}
          {puede.taxi && <button type="button" className={espacio === 'taxi' ? 'activo' : ''} onClick={() => ir('taxi')}>Taxis</button>}
        </div>
        <form className="saas-buscar" role="search" onSubmit={(evento) => { evento.preventDefault(); if (coincidencias[0]) ir(coincidencias[0].espacio, coincidencias[0].id); }}>
          <Search size={18} aria-hidden="true" />
          <input value={consulta} onChange={(evento) => setConsulta(evento.target.value)} placeholder="Buscar módulo" aria-label="Buscar en el panel" />
          {consulta.trim() && (
            <div className="saas-resultados">
              {coincidencias.length ? coincidencias.map((item) => (
                <button key={`${item.espacio}-${item.id}`} type="button" onClick={() => ir(item.espacio, item.id)}>{item.etiqueta}</button>
              )) : <p>Sin módulos con ese nombre.</p>}
            </div>
          )}
        </form>
        <button type="button" className="btn btn-fantasma saas-icono saas-tema" onClick={() => setOscuro((valor) => !valor)} aria-pressed={oscuro} aria-label={oscuro ? 'Usar modo claro' : 'Usar modo oscuro'}>
          {oscuro ? <Sun size={18} aria-hidden="true" /> : <Moon size={18} aria-hidden="true" />}
        </button>
        <div className="saas-avisos">
          <button type="button" className="btn btn-fantasma saas-icono" aria-expanded={avisosAbiertos} aria-label="Notificaciones" onClick={() => setAvisosAbiertos((valor) => !valor)}>
            <Bell size={18} aria-hidden="true" />
            {tablero?.avisos?.length ? <span className="saas-campana">{tablero.avisos.length}</span> : null}
          </button>
          {avisosAbiertos && (
            <div className="saas-resultados" role="status">
              {(tablero?.avisos || []).map((aviso) => <p key={aviso.id}>{aviso.texto}</p>)}
              {!tablero?.avisos?.length && <p>Sin avisos nuevos.</p>}
            </div>
          )}
        </div>
        <div className="saas-usuario">
          <span className="saas-avatar" aria-hidden="true">{iniciales}</span>
          <span className="saas-quien">
            <strong>{usuario.nombre}</strong>
            <small>{ROLES[usuario.rol] || usuario.rol}</small>
          </span>
        </div>
        <button type="button" className="btn btn-fantasma saas-icono" onClick={salir} aria-label="Cerrar sesión">
          <LogOut size={18} aria-hidden="true" />
        </button>
      </header>
      <div className="saas-contenido">
      <h1>{titulo}</h1>
      {mensaje && <p className="aviso-ok" role="status">{mensaje}</p>}
      {error && <p className="aviso" role="alert">{error}</p>}
      {espacio === 'inicio' && <InicioEspacios puede={puede} onEntrar={ir} />}
      {espacio === 'resumen' && (
        <PanelResumen
          tablero={tablero}
          cargando={cargandoTablero}
          error={errorTablero}
          rango={rango}
          onRango={setRango}
          onConsultar={consultarTablero}
          onIr={(mod, sub) => ir(mod === 'turismo' ? 'portal' : mod, sub === 'turismo' ? 'atractivo' : (sub || 'textos'))}
          puede={puede}
        />
      )}
      {actual && espacio !== 'inicio' && espacio !== 'resumen' && (
        <MarcoEdicion
          miga={<>{espacio === 'portal' ? 'Portal' : espacio === 'transporte' ? 'Transporte' : 'Taxis'} / {actual.etiqueta}</>}
          titulo={actual.titulo}
          frase={actual.frase}
          aparece={actual.aparece}
          ver={actual.ver}
        >
          {espacio === 'portal' && seccion === 'textos' && <EditorTextos token={token} espacio="portal" />}
          {espacio === 'portal' && seccion === 'sitio' && <EditorTextos token={token} espacio="sitio" />}
          {espacio === 'portal' && seccion === 'contacto' && <EditorTextos token={token} espacio="portal" prefijo="portal.contacto" />}
          {espacio === 'portal' && seccion === 'portada' && <AdminPortada token={token} />}
          {espacio === 'portal' && ['atractivo', 'parroquia', 'gastronomia', 'hospedaje', 'actividad', 'ruta', 'guia', 'emprendimiento', 'directorio'].includes(seccion) && (
            <AdminTurismo token={token} vista="fichas" tipo={seccion} fijo />
          )}
          {espacio === 'portal' && seccion === 'agenda' && <AdminTurismo token={token} vista="eventos" fijo />}
          {espacio === 'portal' && seccion === 'galeria' && <AdminTurismo token={token} vista="galeria" fijo />}
          {espacio === 'portal' && seccion === 'mensajes' && <AdminTurismo token={token} vista="mensajes" fijo />}
          {espacio === 'transporte' && seccion === 'textos' && <EditorTextos token={token} espacio="transporte" />}
          {espacio === 'transporte' && seccion === 'portada' && <AdminPortada token={token} />}
          {espacio === 'transporte' && seccion === 'pagos' && <AdminPagos token={token} />}
          {espacio === 'transporte' && seccion === 'flota' && <PanelFlota token={token} onCambio={recargarCatalogo} />}
          {espacio === 'transporte' && seccion === 'facturas' && <PanelFacturas token={token} />}
          {espacio === 'transporte' && seccion === 'emisor' && <PanelEmisor token={token} />}
          {espacio === 'transporte' && seccion === 'blog' && <PanelBlog token={token} />}
          {espacio === 'transporte' && seccion === 'anuncios' && <PanelAnuncios token={token} />}
          {espacio === 'transporte' && seccion === 'galeria' && <PanelGaleria token={token} />}
          {espacio === 'taxi' && seccion === 'textos' && <EditorTextos token={token} espacio="taxi" />}
          {espacio === 'taxi' && seccion === 'operacion' && <AdminTaxis token={token} />}
        </MarcoEdicion>
      )}

      {espacio === 'transporte' && seccion === 'operacion' && (
      <>
      <div className="rejilla-admin">
        <form className="panel-form" noValidate onSubmit={crearViaje}>
          <h2>Crear viaje</h2>
          <label>
            Ruta
            <select name="ruta_id" defaultValue="" aria-label="Ruta del viaje">
              <option value="">Selecciona</option>
              {rutas.map((ruta) => (
                <option key={ruta.id} value={ruta.id}>
                  {ruta.origen} → {ruta.destino} · {ruta.duracion_min} min · {formatearPesos(ruta.precio_base)}
                </option>
              ))}
            </select>
          </label>
          <label>
            Bus
            <select name="bus_id" defaultValue="" aria-label="Bus del viaje">
              <option value="">Selecciona</option>
              {buses.map((bus) => (
                <option key={bus.id} value={bus.id} disabled={bus.estado !== 'operativo'}>
                  Disco {bus.numero_disco} · {bus.placa} · {bus.capacidad} puestos · {bus.estado}
                </option>
              ))}
            </select>
          </label>
          <label>
            Salida
            <input type="datetime-local" name="salida" aria-label="Fecha y hora de salida" />
          </label>
          <label>
            Precio (opcional, usa la tarifa de la ruta)
            <input type="number" name="precio" min="1" step="0.01" aria-label="Precio del viaje" />
          </label>
          <button type="submit" className="btn btn-arcilla" disabled={ocupado} aria-label="Crear viaje">Crear viaje</button>
        </form>

        <form className="panel-form" noValidate onSubmit={cambiarTarifa}>
          <h2>Cambiar tarifa</h2>
          <label>
            Ruta
            <select name="ruta_id" defaultValue="" aria-label="Ruta a retarifar">
              <option value="">Selecciona</option>
              {rutas.map((ruta) => (
                <option key={ruta.id} value={ruta.id}>
                  {ruta.origen} → {ruta.destino} · hoy {formatearPesos(ruta.precio_base)}
                </option>
              ))}
            </select>
          </label>
          <label>
            Nueva tarifa base
            <input type="number" name="precio_base" min="0.01" step="0.01" aria-label="Nueva tarifa base" />
          </label>
          <button type="submit" className="btn btn-pino" disabled={ocupado} aria-label="Actualizar tarifa">Actualizar tarifa</button>
        </form>
      </div>

      <section className="panel-form">
        <h2>Horario recurrente</h2>
        <p className="meta">Cada par de ciudades tiene dos salidas al día. Generar completa los próximos 30 días y no duplica las que ya existen.</p>
        <button type="button" className="btn btn-pino" onClick={generarHorario} disabled={ocupado} aria-label="Generar salidas de los próximos 30 días">
          Generar salidas
        </button>
      </section>

      <section className="panel-form">
        <h2>Viajes próximos</h2>
        <ul className="lista-admin">
          {viajes.length ? viajes.map((viaje) => (
            <li key={viaje.id}>
              <strong>{viaje.origen} → {viaje.destino}</strong>
              <span>
                {formatearFechaHora(viaje.salida)} · disco {viaje.numero_disco} · {formatearPesos(viaje.precio)} · {viaje.estado}
              </span>
              {viaje.estado === 'programado' && (
                <div>
                  <button type="button" onClick={() => cancelarViaje(viaje)} disabled={ocupado} aria-label={`Cancelar viaje ${viaje.id}`}>
                    Cancelar
                  </button>
                </div>
              )}
            </li>
          )) : <li>No hay viajes en la ventana reciente.</li>}
        </ul>
      </section>

      <section className="panel-form ventas">
        <div className="ventas-cabeza">
          <h2>Ventas del día</h2>
          <form onSubmit={consultarVentas} className="fila-fecha">
            <label>
              Fecha
              <input type="date" value={fecha} onChange={(e) => setFecha(e.target.value)} aria-label="Fecha del reporte de ventas" />
            </label>
            <button type="submit" className="btn btn-pino" disabled={ocupado} aria-label="Consultar ventas del día">Consultar</button>
          </form>
        </div>
        <div className="tabla-wrap">
          <table>
            <caption>Pagos aprobados {ventas ? `del ${ventas.fecha}` : ''}</caption>
            <thead>
              <tr>
                <th>Ruta</th>
                <th>Boletos</th>
                <th>Total</th>
              </tr>
            </thead>
            <tbody>
              {ventas?.filas.length ? ventas.filas.map((fila) => (
                <tr key={fila.ruta_id}>
                  <td data-label="Ruta">{fila.origen} → {fila.destino}</td>
                  <td data-label="Boletos">{fila.boletos_pagados}</td>
                  <td data-label="Total">{formatearPesos(fila.total)}</td>
                </tr>
              )) : (
                <tr>
                  <td colSpan={3}>Aún no hay pagos aprobados en esta fecha.</td>
                </tr>
              )}
            </tbody>
            <tfoot>
              <tr>
                <th colSpan={2}>Total</th>
                <th>{formatearPesos(ventas?.total || 0)}</th>
              </tr>
            </tfoot>
          </table>
        </div>
      </section>
      </>
      )}
      </div>
      </div>
    </div>
  );
}
