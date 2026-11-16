import { Bus, Car, Compass, LayoutDashboard } from 'lucide-react';

export default function InicioEspacios({ puede, onEntrar }) {
  const tarjetas = [
    puede.turismo && {
      id: 'portal',
      titulo: 'Portal del cantón La Maná',
      texto: 'Portada, textos del inicio, atractivos, agenda, galería y contacto.',
      Icono: Compass,
    },
    puede.transporte && {
      id: 'transporte',
      titulo: 'Transporte (boletos de bus)',
      texto: 'Viajes, flota, tarifas, pagos, facturas y los textos de la página de boletos.',
      Icono: Bus,
    },
    puede.taxi && {
      id: 'taxi',
      titulo: 'Taxis',
      texto: 'Compañías, tarifas de ejemplo, unidades y el texto de la página /taxi.',
      Icono: Car,
    },
  ].filter(Boolean);

  return (
    <div className="inicio-espacios">
      <button type="button" className="espacio-tarjeta resumen" onClick={() => onEntrar('resumen', 'resumen')} aria-label="Abrir el resumen general">
        <LayoutDashboard size={28} aria-hidden="true" />
        <strong>Resumen general</strong>
        <span>Ventas, ocupación, taxis y lo publicado. Es lo primero que conviene mirar.</span>
      </button>
      {tarjetas.map((tarjeta) => (
        <button key={tarjeta.id} type="button" className={`espacio-tarjeta ${tarjeta.id}`} onClick={() => onEntrar(tarjeta.id, 'textos')} aria-label={`Entrar a ${tarjeta.titulo}`}>
          <tarjeta.Icono size={28} aria-hidden="true" />
          <strong>{tarjeta.titulo}</strong>
          <span>{tarjeta.texto}</span>
        </button>
      ))}
    </div>
  );
}
