import { Link } from 'react-router-dom';

const CIUDADES = [
  'La Maná',
  'Quevedo',
  'Quinsaloma',
  'Moraspungo',
  'Latacunga',
  'Ambato',
  'Quito',
  'Guayaquil',
  'Durán',
  'Empalme',
];

export default function Encomiendas() {
  return (
    <div className="pagina">
      <p className="sobrelinea">Encomiendas</p>
      <h1>Paquetes en la misma unidad del pasaje.</h1>
      <p className="lead">
        La cooperativa recibe y entrega encomiendas entre la costa y la sierra.
        El afiche de la oficina tiene el mapa y los teléfonos de cada punto.
      </p>
      <div className="encomiendas">
        <img
          src="/encomiendas-lamana.png"
          alt="Afiche de encomiendas de Trans La Maná, con el mapa de cobertura y los teléfonos de Guayaquil, Durán, Quevedo y la matriz de La Maná"
        />
        <div>
          <h2>Cobertura</h2>
          <ul className="lista-cobertura">
            {CIUDADES.map((ciudad) => <li key={ciudad}>{ciudad}</li>)}
          </ul>
          <h2>Teléfonos</h2>
          <p className="telefonos">
            <a href="tel:+593994127992">Matriz La Maná · 099 412 7992</a>
            <a href="tel:+593980405468">Quevedo · 098 040 5468</a>
            <a href="tel:+593991175522">Guayaquil · 099 117 5522</a>
            <a href="tel:+593991172085">Durán · 099 117 2085</a>
          </p>
          <p className="meta">La matriz está en La Maná, Cotopaxi. Horario de taquilla: 05:00 a 21:00.</p>
          <Link className="btn btn-pino" to={{ pathname: '/', hash: 'buscar' }}>Comprar un pasaje</Link>
        </div>
      </div>
    </div>
  );
}
