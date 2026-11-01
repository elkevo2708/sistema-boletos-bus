function Simbolo({ tinta, puerta, ola }) {
  return (
    <>
      <circle cx="47" cy="14.5" r="6.2" fill="#f2c200" />
      <path d="M27 40.5 40 16.5 54 40.5Z" fill="#146624" />
      <path d="M38 40.5 51 21.5 64.5 40.5Z" fill="#1f8a32" />
      <path d="M3.2 32.5c6.2-2.2 9.4 2.6 5.2 7.6-5.2 2.4-9.6-1.6-5.2-7.6Z" fill="#1f8a32" />
      <path d="M1.2 41.2c5.4.2 8.2 4.2 4.2 7.8-5.4 1.8-9.4-2.2-4.2-7.8Z" fill="#146624" />
      <path d="M9 39.8h17.2v16.4H9Z" fill="#fff" stroke={tinta} strokeWidth="1.45" strokeLinejoin="round" />
      <path d="M12.8 27.6h9.6v12.2h-9.6Z" fill="#fff" stroke={tinta} strokeWidth="1.45" strokeLinejoin="round" />
      <path d="M12.8 27.8c0-6.4 9.6-6.4 9.6 0" fill="#1497b8" stroke={tinta} strokeWidth="1.35" />
      <path d="M17.6 14.6v7.4M14.6 17.6h6" fill="none" stroke={tinta} strokeWidth="1.75" strokeLinecap="round" />
      <path d="M15.1 49.4h5.1V56h-5.1Z" fill={puerta} />
      <circle cx="17.6" cy="33" r="1.35" fill="#1497b8" />
      <path d="M1.5 53.2c7.2-5.2 13.2 5.2 20.4 0s13.2-5.2 20.4 0 13.2 5.2 20.2 0" fill="none" stroke="#1497b8" strokeWidth="2.25" strokeLinecap="round" />
      <path d="M1.5 59.4c7.2-4.6 13.2 4.6 20.4 0s13.2-4.6 20.4 0 13.2 4.6 20.2 0" fill="none" stroke={ola} strokeWidth="1.85" strokeLinecap="round" />
    </>
  );
}

export default function LogoRecorres({ variante = 'horizontal', clara = false, decorativo = false }) {
  const tinta = clara ? '#f4fbfe' : '#0c2f6b';
  const acento = clara ? '#7ad4ea' : '#1497b8';
  const trazo = clara ? '#d7f4fb' : '#0c2f6b';
  const puerta = clara ? '#1497b8' : '#0c2f6b';
  const ola = clara ? '#f2c200' : '#0c2f6b';
  const accesible = decorativo
    ? { 'aria-hidden': true }
    : { role: 'img', 'aria-label': 'La Maná Recorres' };

  if (variante === 'isotipo') {
    return (
      <svg className="logo-recorres logo-isotipo" viewBox="0 0 64 64" {...accesible}>
        <Simbolo tinta={trazo} puerta={puerta} ola={ola} />
      </svg>
    );
  }

  return (
    <svg className="logo-recorres logo-horizontal" viewBox="0 0 408 68" {...accesible}>
      <svg x="0" y="2" width="64" height="64" viewBox="0 0 64 64" aria-hidden="true">
        <Simbolo tinta={trazo} puerta={puerta} ola={ola} />
      </svg>
      <text x="74" y="40" style={{ fontFamily: 'Montserrat, sans-serif' }}>
        <tspan fontSize="26" fontWeight="800" fill={tinta}>La Maná</tspan>
        <tspan dx="8" fontSize="26" fontWeight="700" fill={acento}>Recorres</tspan>
      </text>
      <path d="M76 53c78 9 168-3 248 3" fill="none" stroke={clara ? '#f2c200' : '#1497b8'} strokeWidth="2.4" strokeLinecap="round" />
    </svg>
  );
}
