function maximo(valores) {
  return Math.max(1, ...valores.map((valor) => Number(valor) || 0));
}

export function GraficoLinea({ puntos, titulo }) {
  if (!puntos?.length || puntos.every((punto) => !Number(punto.total))) {
    return null;
  }
  const ancho = 360;
  const alto = 168;
  const pad = { l: 4, r: 4, t: 14, b: 22 };
  const tope = maximo(puntos.map((punto) => punto.total));
  const pasos = Math.max(puntos.length - 1, 1);
  const coords = puntos.map((punto, indice) => {
    const x = pad.l + (indice / pasos) * (ancho - pad.l - pad.r);
    const y = pad.t + (1 - (Number(punto.total) || 0) / tope) * (alto - pad.t - pad.b);
    return [x, y];
  });
  const linea = coords.map((punto, indice) => `${indice ? 'L' : 'M'}${punto[0].toFixed(1)} ${punto[1].toFixed(1)}`).join(' ');
  const area = `${linea} L${coords.at(-1)[0].toFixed(1)} ${alto - pad.b} L${coords[0][0].toFixed(1)} ${alto - pad.b} Z`;
  const primero = puntos[0].fecha.slice(5);
  const ultimo = puntos.at(-1).fecha.slice(5);
  return (
    <svg className="grafico" viewBox={`0 0 ${ancho} ${alto}`} role="img" aria-label={`${titulo}. Máximo ${tope.toFixed(2)} dólares.`}>
      <title>{titulo}</title>
      <path className="grafico-area" d={area} />
      <path className="grafico-linea" d={linea} />
      <text x={pad.l} y={alto - 4} className="grafico-eje">{primero}</text>
      <text x={ancho - pad.r} y={alto - 4} textAnchor="end" className="grafico-eje">{ultimo}</text>
    </svg>
  );
}

export function GraficoBarras({ puntos, titulo, sufijo = '%' }) {
  if (!puntos?.length) return null;
  const ancho = 360;
  const alto = Math.max(120, puntos.length * 44 + 8);
  const tope = maximo(puntos.map((punto) => punto.valor));
  return (
    <svg className="grafico" viewBox={`0 0 ${ancho} ${alto}`} role="img" aria-label={titulo}>
      <title>{titulo}</title>
      {puntos.map((punto, indice) => {
        const y = 6 + indice * 44;
        const largo = Math.max(4, ((Number(punto.valor) || 0) / tope) * (ancho - 52));
        return (
          <g key={punto.nombre}>
            <text x="0" y={y + 12} className="grafico-eje" fontSize="12">{punto.nombre}</text>
            <rect x="0" y={y + 18} width={largo} height="12" rx="6" className="grafico-barra" />
            <text x={ancho - 2} y={y + 29} textAnchor="end" className="grafico-eje" fontSize="12">{punto.detalle || `${punto.valor}${sufijo}`}</text>
          </g>
        );
      })}
    </svg>
  );
}

export function GraficoHoras({ puntos, titulo }) {
  if (!puntos?.length || puntos.every((punto) => !punto.total)) return null;
  const ancho = 360;
  const alto = 150;
  const tope = maximo(puntos.map((punto) => punto.total));
  const hueco = ancho / puntos.length;
  return (
    <svg className="grafico" viewBox={`0 0 ${ancho} ${alto}`} role="img" aria-label={titulo}>
      <title>{titulo}</title>
      {puntos.map((punto, indice) => {
        const altoBarra = ((Number(punto.total) || 0) / tope) * 110;
        const x = indice * hueco + 2;
        return (
          <g key={punto.hora}>
            <rect x={x} y={120 - altoBarra} width={Math.max(hueco - 4, 2)} height={Math.max(altoBarra, 0)} rx="3" className="grafico-barra" />
            {indice % 3 === 0 && <text x={x} y="140" className="grafico-eje">{punto.hora}</text>}
          </g>
        );
      })}
    </svg>
  );
}
