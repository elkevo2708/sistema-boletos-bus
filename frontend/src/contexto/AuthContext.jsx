import { createContext, useContext, useMemo, useState } from 'react';

const AuthContext = createContext(null);
const CLAVE = 'viaandina_sesion';

function leer() {
  try {
    return JSON.parse(localStorage.getItem(CLAVE) || 'null');
  } catch {
    return null;
  }
}

export function AuthProvider({ children }) {
  const [sesion, setSesion] = useState(leer);

  const valor = useMemo(
    () => ({
      usuario: sesion?.usuario ?? null,
      token: sesion?.access_token ?? null,
      refreshToken: sesion?.refresh_token ?? null,
      iniciar(datos) {
        const siguiente = {
          access_token: datos.access_token,
          refresh_token: datos.refresh_token,
          usuario: datos.usuario,
        };
        localStorage.setItem(CLAVE, JSON.stringify(siguiente));
        setSesion(siguiente);
      },
      cerrar() {
        localStorage.removeItem(CLAVE);
        setSesion(null);
      },
    }),
    [sesion],
  );

  return <AuthContext.Provider value={valor}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
