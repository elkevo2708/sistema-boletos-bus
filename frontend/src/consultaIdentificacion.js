import { useEffect, useRef, useState } from 'react';
import { solicitar } from './api';
import { identificacionValida } from './identificacion';

export function useConsultaIdentificacion({ token, tipo, identificacion, onEncontrado }) {
  const [estado, setEstado] = useState('idle');
  const [aviso, setAviso] = useState('');
  const callback = useRef(onEncontrado);
  callback.current = onEncontrado;

  useEffect(() => {
    if (!token || (tipo !== 'cedula' && tipo !== 'ruc') || !identificacionValida(tipo, identificacion)) {
      setEstado('idle');
      setAviso('');
      return undefined;
    }
    const buscada = identificacion.trim();
    let vivo = true;
    setEstado('consultando');
    setAviso('Consultando identificación…');
    const reloj = setTimeout(async () => {
      try {
        const data = await solicitar(
          `/facturacion/consulta?tipo=${encodeURIComponent(tipo)}&identificacion=${encodeURIComponent(buscada)}`,
          { token },
        );
        if (!vivo) return;
        if (data.encontrado) {
          callback.current?.(data);
          setEstado('encontrado');
          setAviso(data.origen === 'local' ? 'Nombre tomado de una compra anterior.' : 'Nombre consultado.');
        } else {
          setEstado('vacio');
          setAviso('No encontrado, ingréselo manualmente.');
        }
      } catch {
        if (!vivo) return;
        setEstado('error');
        setAviso('No se pudo consultar. Puede escribir los datos a mano.');
      }
    }, 400);
    return () => {
      vivo = false;
      clearTimeout(reloj);
    };
  }, [token, tipo, identificacion]);

  return { estado, aviso };
}
