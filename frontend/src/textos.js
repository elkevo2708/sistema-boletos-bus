import { useEffect, useState } from 'react';
import { solicitar } from './api';

export function useTextos(espacio) {
  const [mapa, setMapa] = useState({});

  useEffect(() => {
    let vivo = true;
    solicitar(`/textos?espacio=${espacio}`)
      .then((datos) => { if (vivo) setMapa(datos || {}); })
      .catch(() => {});
    return () => { vivo = false; };
  }, [espacio]);

  return (clave, respaldo) => (mapa[clave] == null || mapa[clave] === '' ? respaldo : mapa[clave]);
}
