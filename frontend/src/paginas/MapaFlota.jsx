import { useEffect, useRef } from 'react';
import { iconoPin, iconoTaxi, limpiarMarcas, ponerMarca, recordarRumbo } from '../ui/mapaTaxi';

export default function MapaFlota({ unidades = [], destino = null, propioId = null, altura = 280 }) {
  const caja = useRef(null);
  const mapa = useRef(null);
  const marcas = useRef(new Map());
  const rumbos = useRef(new Map());
  const firma = unidades.map((unidad) => `${unidad.id}:${unidad.lat}:${unidad.lng}:${unidad.estado}:${unidad.rumbo}`).join('|');

  useEffect(() => {
    let cancelado = false;
    (async () => {
      const leaflet = await import('leaflet');
      await import('leaflet/dist/leaflet.css');
      if (cancelado || !caja.current) return;
      const L = leaflet.default ?? leaflet;
      if (!mapa.current) {
        mapa.current = L.map(caja.current, { zoomControl: false }).setView([-0.9406, -79.2344], 15);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '&copy; OpenStreetMap',
          maxZoom: 19,
        }).addTo(mapa.current);
        setTimeout(() => mapa.current.invalidateSize(), 200);
      }
      const vistos = new Set();
      unidades.filter((unidad) => unidad.lat != null).forEach((unidad) => {
        const clave = `taxi-${unidad.id}`;
        vistos.add(clave);
        const rumbo = recordarRumbo(rumbos.current, unidad.id, unidad, unidad.rumbo);
        const marca = ponerMarca(
          L, mapa.current, marcas.current, clave, [unidad.lat, unidad.lng],
          iconoTaxi(L, { estado: unidad.estado, rumbo, propio: propioId === unidad.id }),
        );
        marca.bindTooltip(`Unidad ${unidad.unidad || unidad.numero_unidad || ''}`);
      });
      if (destino?.lat != null) {
        vistos.add('destino');
        ponerMarca(L, mapa.current, marcas.current, 'destino', [destino.lat, destino.lng], iconoPin(L, 'destino'));
      }
      limpiarMarcas(marcas.current, vistos);
    })();
    return () => { cancelado = true; };
  }, [firma, destino?.lat, destino?.lng, propioId]);

  useEffect(() => () => { mapa.current?.remove(); mapa.current = null; }, []);

  return <div ref={caja} className="saas-mapa" style={{ height: altura }} role="img" aria-label="Mapa de taxis" />;
}
