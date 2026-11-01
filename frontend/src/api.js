function mensajeDe(data) {
  if (!data) return 'No se pudo completar la operación';
  if (typeof data.detail === 'string') return data.detail;
  if (Array.isArray(data.detail)) {
    return data.detail
      .map((item) => item.msg || 'Dato inválido')
      .join('. ');
  }
  return 'No se pudo completar la operación';
}

async function interpretar(respuesta) {
  if (respuesta.status === 204) return null;
  const texto = await respuesta.text();
  let data = null;
  if (texto) {
    try {
      data = JSON.parse(texto);
    } catch {
      data = { detail: texto };
    }
  }
  if (!respuesta.ok) {
    const error = new Error(mensajeDe(data));
    error.status = respuesta.status;
    throw error;
  }
  return data;
}

export async function solicitar(ruta, opciones = {}) {
  const { method = 'GET', body, form, token } = opciones;
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  let payload;
  if (form) {
    payload = new URLSearchParams(form);
    headers['Content-Type'] = 'application/x-www-form-urlencoded';
  } else if (body !== undefined) {
    payload = JSON.stringify(body);
    headers['Content-Type'] = 'application/json';
  }
  const respuesta = await fetch(`/api${ruta}`, { method, headers, body: payload });
  return interpretar(respuesta);
}

export async function enviarFormulario(ruta, opciones = {}) {
  const headers = {};
  if (opciones.token) headers.Authorization = `Bearer ${opciones.token}`;
  const respuesta = await fetch(`/api${ruta}`, {
    method: opciones.method || 'POST',
    headers,
    body: opciones.datos,
  });
  return interpretar(respuesta);
}

export async function traerArchivo(ruta, token) {
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  const respuesta = await fetch(`/api${ruta}`, { headers });
  if (!respuesta.ok) {
    const error = new Error('No se pudo descargar el archivo');
    error.status = respuesta.status;
    throw error;
  }
  return respuesta.blob();
}

export function urlSocket(viajeId) {
  const protocolo = window.location.protocol === 'https:' ? 'wss' : 'ws';
  return `${protocolo}://${window.location.host}/ws/viajes/${viajeId}`;
}
