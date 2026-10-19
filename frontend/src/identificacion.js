export const CONSUMIDOR_FINAL = '9999999999999';

function provinciaValida(digitos) {
  const provincia = Number(digitos.slice(0, 2));
  return (provincia >= 1 && provincia <= 24) || provincia === 30;
}

function modulo10(nueve) {
  const coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2];
  let total = 0;
  coeficientes.forEach((coeficiente, indice) => {
    let producto = Number(nueve[indice]) * coeficiente;
    if (producto >= 10) producto -= 9;
    total += producto;
  });
  return (10 - (total % 10)) % 10;
}

function modulo11(digitos, coeficientes) {
  const total = coeficientes.reduce(
    (suma, coeficiente, indice) => suma + Number(digitos[indice]) * coeficiente,
    0,
  );
  const residuo = total % 11;
  const verificador = residuo === 0 ? 0 : 11 - residuo;
  if (verificador === 10) return null;
  return verificador;
}

export function cedulaValida(numero) {
  if (numero.length !== 10 || !/^\d+$/.test(numero)) return false;
  if (!provinciaValida(numero)) return false;
  if (Number(numero[2]) > 5) return false;
  return modulo10(numero.slice(0, 9)) === Number(numero[9]);
}

function rucNatural(numero) {
  return cedulaValida(numero.slice(0, 10)) && numero.slice(10) !== '000';
}

function rucPrivado(numero) {
  if (Number(numero[2]) !== 9 || numero.slice(10) === '000') return false;
  const verificador = modulo11(numero.slice(0, 9), [4, 3, 2, 7, 6, 5, 4, 3, 2]);
  return verificador !== null && verificador === Number(numero[9]);
}

function rucPublico(numero) {
  if (Number(numero[2]) !== 6 || numero.slice(9) === '0000') return false;
  const verificador = modulo11(numero.slice(0, 8), [3, 2, 7, 6, 5, 4, 3, 2]);
  return verificador !== null && verificador === Number(numero[8]);
}

export function rucValido(numero) {
  if (numero.length !== 13 || !/^\d+$/.test(numero) || !provinciaValida(numero)) return false;
  const tercer = Number(numero[2]);
  if (tercer < 6) return rucNatural(numero);
  if (tercer === 6) return rucPublico(numero);
  if (tercer === 9) return rucPrivado(numero);
  return false;
}

export function validarIdentificacion(tipo, identificacion) {
  const numero = (identificacion || '').trim().toUpperCase();
  if (!['cedula', 'ruc', 'pasaporte', 'consumidor_final'].includes(tipo)) {
    return 'Tipo de identificación no reconocido';
  }
  if (tipo === 'consumidor_final') {
    if (numero !== CONSUMIDOR_FINAL) return 'El consumidor final usa la identificación 9999999999999';
    return null;
  }
  if (tipo === 'pasaporte') {
    if (!/^[A-Z0-9]{5,20}$/.test(numero)) return 'El pasaporte debe tener entre 5 y 20 letras o números';
    return null;
  }
  if (tipo === 'cedula') {
    if (!cedulaValida(numero)) return 'La cédula no supera el dígito verificador módulo 10';
    return null;
  }
  if (!rucValido(numero)) return 'El RUC no corresponde a persona natural, sociedad privada ni sociedad pública';
  return null;
}

export function identificacionValida(tipo, identificacion) {
  return validarIdentificacion(tipo, identificacion) === null;
}
