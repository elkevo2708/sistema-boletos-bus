export function rumboEntre(desde, hasta) {
  if (!desde || !hasta) return null;
  const dLat = hasta.lat - desde.lat;
  const dLng = hasta.lng - desde.lng;
  if (Math.abs(dLat) < 0.00001 && Math.abs(dLng) < 0.00001) return null;
  const y = Math.sin((dLng * Math.PI) / 180) * Math.cos((hasta.lat * Math.PI) / 180);
  const x = Math.cos((desde.lat * Math.PI) / 180) * Math.sin((hasta.lat * Math.PI) / 180)
    - Math.sin((desde.lat * Math.PI) / 180) * Math.cos((hasta.lat * Math.PI) / 180) * Math.cos((dLng * Math.PI) / 180);
  return (Math.atan2(y, x) * 180) / Math.PI;
}

export function recordarRumbo(memoria, id, punto, rumboServidor) {
  const previo = memoria.get(id);
  memoria.set(id, { lat: punto.lat, lng: punto.lng });
  const calculado = rumboEntre(previo, punto);
  if (calculado != null) return Math.round((calculado + 360) % 360);
  return rumboServidor ?? 0;
}

function carro(color, letrero) {
  return `<svg viewBox="0 0 64 64" width="48" height="48" aria-hidden="true">
    <ellipse cx="32" cy="58" rx="16" ry="3.5" fill="rgba(12,47,107,.28)"/>
    <rect x="20" y="16" width="24" height="36" rx="8" fill="${color}" stroke="#0c2f6b" stroke-width="2"/>
    <rect x="24" y="22" width="16" height="9" rx="2.5" fill="#e7f6fb" stroke="#0c2f6b" stroke-width="1.2"/>
    <rect x="24" y="36" width="16" height="8" rx="2" fill="#fff8dc" stroke="#0c2f6b" stroke-width="1"/>
    <rect x="22" y="7" width="20" height="9" rx="2" fill="#0c2f6b"/>
    <text x="32" y="13.5" text-anchor="middle" font-size="6" font-family="Montserrat, sans-serif" font-weight="700" fill="${letrero}">TAXI</text>
    <circle cx="22" cy="20" r="2.4" fill="#142033"/><circle cx="42" cy="20" r="2.4" fill="#142033"/>
    <circle cx="22" cy="48" r="2.4" fill="#142033"/><circle cx="42" cy="48" r="2.4" fill="#142033"/>
  </svg>`;
}

export function htmlTaxi({ estado = 'disponible', rumbo = 0, propio = false }) {
  const ocupado = estado === 'ocupado';
  const color = ocupado ? '#9aa3ad' : '#f2c200';
  const letrero = ocupado ? '#e7eef6' : '#f2c200';
  const clase = propio ? 'mapa-taxi propio' : ocupado ? 'mapa-taxi ocupado' : 'mapa-taxi';
  return `<div class="${clase}" style="transform:rotate(${Number(rumbo) || 0}deg)">${carro(color, letrero)}</div>`;
}

export function iconoTaxi(L, opciones) {
  return L.divIcon({
    className: 'mapa-taxi-icono',
    html: htmlTaxi(opciones),
    iconSize: [48, 48],
    iconAnchor: [24, 28],
  });
}

export function iconoPin(L, tipo) {
  const esDestino = tipo === 'destino';
  const color = esDestino ? '#1f8a32' : '#0c2f6b';
  const letra = esDestino ? 'B' : 'A';
  return L.divIcon({
    className: 'mapa-pin-icono',
    iconSize: [32, 42],
    iconAnchor: [16, 40],
    html: `<div class="mapa-pin ${tipo}" style="--pin:${color}"><span>${letra}</span></div>`,
  });
}

export function ponerMarca(L, mapa, registro, clave, latlng, icono, extra) {
  const actual = registro.get(clave);
  if (actual) {
    actual.setLatLng(latlng);
    actual.setIcon(icono);
    return actual;
  }
  const marca = L.marker(latlng, { icon: icono, ...extra }).addTo(mapa);
  registro.set(clave, marca);
  return marca;
}

export function limpiarMarcas(registro, conservar) {
  for (const [clave, marca] of registro) {
    if (!conservar.has(clave)) {
      marca.remove();
      registro.delete(clave);
    }
  }
}
