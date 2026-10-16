const MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];

export function fechaBogota(dias = 0) {
  const formato = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'America/Bogota',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
  return formato.format(new Date(Date.now() + dias * 24 * 60 * 60 * 1000));
}

export function ahoraBogotaInput() {
  const formato = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'America/Bogota',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  });
  const partes = Object.fromEntries(formato.formatToParts(new Date()).map((parte) => [parte.type, parte.value]));
  return `${partes.year}-${partes.month}-${partes.day}T${partes.hour}:${partes.minute}`;
}

export function formatearFechaHora(valor) {
  if (!valor) return '';
  const [fecha, horaCompleta] = valor.replace(' ', 'T').split('T');
  const [, mes, dia] = fecha.split('-');
  const hora = (horaCompleta || '').slice(0, 5);
  return `${Number(dia)} ${MESES[Number(mes) - 1]} · ${hora}`;
}

export function formatearDinero(valor) {
  const numero = Number(valor);
  if (Number.isNaN(numero)) return valor;
  return new Intl.NumberFormat('es-EC', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
  }).format(numero);
}

export const formatearPesos = formatearDinero;

export function cuentaRegresiva(ms) {
  const total = Math.max(0, Math.ceil(ms / 1000));
  const minutos = Math.floor(total / 60);
  const segundos = total % 60;
  return `${String(minutos).padStart(2, '0')}:${String(segundos).padStart(2, '0')}`;
}

export function instanteColombia(valor) {
  if (!valor) return NaN;
  const normalizado = valor.replace(' ', 'T');
  return new Date(`${normalizado}-05:00`).getTime();
}
