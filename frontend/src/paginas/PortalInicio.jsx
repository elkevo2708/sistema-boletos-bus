import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { solicitar } from '../api';
import HeroPortada from '../componentes/HeroPortada';
import TarjetaTurismo from '../componentes/TarjetaTurismo';
import { ICONOS_PRACTICOS, MENU_EXTRA } from '../iconosTurismo';
import { Seccion } from '../ui/ui';

export default function PortalInicio() {
  const [resumen, setResumen] = useState(null);
  const [parroquias, setParroquias] = useState([]);
  const [comida, setComida] = useState([]);
  const [actividades, setActividades] = useState([]);
  const [fotos, setFotos] = useState([]);

  useEffect(() => {
    solicitar('/turismo/resumen').then(setResumen).catch(() => {});
    solicitar('/turismo/fichas?tipo=parroquia').then(setParroquias).catch(() => {});
    solicitar('/turismo/fichas?tipo=gastronomia').then(setComida).catch(() => {});
    solicitar('/turismo/fichas?tipo=actividad').then(setActividades).catch(() => {});
    solicitar('/turismo/galeria').then(setFotos).catch(() => {});
  }, []);

  return (
    <>
      <HeroPortada ambito="portal" />
      <Seccion kicker="Cantón La Maná" titulo="Qué puedes recorrer">
        {resumen ? (
          <div className="rejilla-turismo">
            {(resumen.destacados || []).map((ficha) => <TarjetaTurismo key={`${ficha.tipo}-${ficha.id}`} ficha={ficha} />)}
          </div>
        ) : (
          <div className="rejilla-esqueleto" aria-hidden="true">
            <span className="esqueleto-tarjeta" /><span className="esqueleto-tarjeta" /><span className="esqueleto-tarjeta" />
          </div>
        )}
      </Seccion>

      <Seccion titulo="Qué debes saber sobre La Maná" clara>
        <div className="portal-saber">
          <article>
            <h3>Dónde queda</h3>
            <p>La Maná es un cantón de Cotopaxi en el piso cálido, entre la sierra y la llanura que sigue hacia Quevedo. No es el páramo del volcán: es subtrópico húmedo, de finca y de río.</p>
          </article>
          <article>
            <h3>Cómo se divide</h3>
            <p>La cabecera lleva el nombre del cantón. Las parroquias rurales son Guasaganda, Pucayacu y El Carmen. Cada una tiene su ficha, editable desde taquilla.</p>
          </article>
          <article>
            <h3>Qué hacer</h3>
            <p>Bajar al río San Pablo, caminar hacia cascadas como Zapanal, Tilipulo o Manguilita, y ver cacao o banano en una finca que acepte visita. El bus de la cooperativa está aparte, en Transporte.</p>
          </article>
        </div>
        <ul className="portal-practico">
          {ICONOS_PRACTICOS.map((item) => (
            <li key={item.texto}>
              <item.Icono size={22} aria-hidden="true" />
              <Link to="/aprende">{item.texto}</Link>
            </li>
          ))}
        </ul>
      </Seccion>

      <Seccion titulo="Para quién es el viaje">
        <div className="portal-perfiles">
          <article>
            <h3>Quien busca río y sombra</h3>
            <p>La tarde en una orilla del San Pablo alcanza si el plan es simple. Mire el caudal antes de entrar al agua.</p>
          </article>
          <article>
            <h3>Quien camina</h3>
            <p>Las cascadas del entorno piden calzado cerrado y tiempo de sobra. No hay aquí un horario único de sendero.</p>
          </article>
          <article>
            <h3>Quien viene de paso</h3>
            <p>La cabecera sirve de escala entre Latacunga y Quevedo. El pasaje se compra en Transporte, con el asiento ya elegido.</p>
          </article>
        </div>
      </Seccion>

      <Seccion titulo="Parroquias" clara accion={<Link to="/parroquias">Ver todas</Link>}>
        <div className="rejilla-turismo">
          {parroquias.map((ficha) => <TarjetaTurismo key={ficha.id} ficha={ficha} />)}
        </div>
      </Seccion>

      <Seccion titulo="Gastronomía" accion={<Link to="/gastronomia">Ver la mesa</Link>}>
        <div className="rejilla-turismo">
          {comida.map((ficha) => <TarjetaTurismo key={ficha.id} ficha={ficha} />)}
        </div>
      </Seccion>

      <Seccion titulo="Actividades" clara accion={<Link to="/actividades">Ver el plan</Link>}>
        <div className="rejilla-turismo">
          {actividades.map((ficha) => <TarjetaTurismo key={ficha.id} ficha={ficha} />)}
        </div>
      </Seccion>

      <Seccion titulo="Agenda" accion={<Link to="/agenda">Ver fechas</Link>}>
        <ul className="portal-agenda">
          {(resumen?.eventos || []).map((evento) => (
            <li key={evento.id}>
              <time dateTime={evento.inicio}>{evento.inicio}</time>
              <div>
                <h3><Link to={`/agenda/${evento.slug}`}>{evento.titulo}</Link></h3>
                <p>{evento.resumen}</p>
              </div>
            </li>
          ))}
        </ul>
      </Seccion>

      <Seccion titulo="Galería" clara accion={<Link to="/galeria">Abrir</Link>}>
        <div className="tira-fotos">
          {fotos.map((foto) => (
            <figure key={foto.id}>
              <img src={foto.url} alt={foto.titulo} loading="lazy" decoding="async" />
              <figcaption>{foto.titulo}</figcaption>
            </figure>
          ))}
        </div>
      </Seccion>

      <Seccion titulo="Mapa y contacto">
        <div className="portal-dos">
          <Link className="portal-atajo" to="/mapa">
            <h3>Mapa del cantón</h3>
            <p>La cabecera marcada sobre un mapa abierto. Las cascadas se agregan cuando tengan coordenada propia.</p>
          </Link>
          <Link className="portal-atajo" to="/contacto">
            <h3>Escribir</h3>
            <p>El mensaje queda en taquilla. No reserva finca ni pasaje: el pasaje se compra en Transporte.</p>
          </Link>
        </div>
        <ul className="portal-extra">
          {MENU_EXTRA.map((item) => (
            <li key={item.to}><Link to={item.to}><item.Icono size={18} aria-hidden="true" /> {item.label}</Link></li>
          ))}
          <li><Link to="/transporte">Transporte</Link></li>
        </ul>
      </Seccion>
    </>
  );
}
