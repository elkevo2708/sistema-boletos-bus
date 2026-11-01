import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { solicitar } from '../api';
import { RUTA_TIPO } from '../iconosTurismo';
import { EncabezadoPagina, EstadoVacio } from '../ui/ui';

export default function PortalMapa() {
  const [puntos, setPuntos] = useState([]);

  useEffect(() => {
    solicitar('/turismo/mapa').then(setPuntos).catch(() => {});
  }, []);

  const marco = '-79.55,-1.20,-78.95,-0.70';
  return (
    <>
      <EncabezadoPagina titulo="Mapa" bajada="El recuadro usa OpenStreetMap. El punto es una referencia de la cabecera, no un levantamiento." />
    <section className="portal-bloque">
      <div className="portal-mapa">
        <iframe
          title="Mapa de La Maná en OpenStreetMap"
          src={`https://www.openstreetmap.org/export/embed.html?bbox=${marco}&layer=mapnik&marker=-0.9406,-79.2344`}
        />
        <ul>
          {puntos.map((punto) => (
            <li key={`${punto.tipo}-${punto.slug}`}>
              <Link to={`${RUTA_TIPO[punto.tipo]}/${punto.slug}`}>{punto.nombre}</Link>
              <span>{punto.zona}</span>
            </li>
          ))}
          {puntos.length === 0 && <li><EstadoVacio titulo="Sin coordenadas" texto="Todavía no hay puntos publicados." /></li>}
        </ul>
      </div>
    </section>
    </>
  );
}
