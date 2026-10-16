import { Route, Routes } from 'react-router-dom';
import Layout from './componentes/Layout';
import Admin from './paginas/Admin';
import Asientos from './paginas/Asientos';
import Blog from './paginas/Blog';
import BlogDetalle from './paginas/BlogDetalle';
import Buscar from './paginas/Buscar';
import Encomiendas from './paginas/Encomiendas';
import Galeria from './paginas/Galeria';
import Login from './paginas/Login';
import MisFacturas from './paginas/MisFacturas';

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Buscar />} />
        <Route path="/viajes/:id" element={<Asientos />} />
        <Route path="/noticias" element={<Blog />} />
        <Route path="/noticias/:slug" element={<BlogDetalle />} />
        <Route path="/galeria" element={<Galeria />} />
        <Route path="/encomiendas" element={<Encomiendas />} />
        <Route path="/ingresar" element={<Login />} />
        <Route path="/mis-facturas" element={<MisFacturas />} />
        <Route path="/admin" element={<Admin />} />
      </Route>
    </Routes>
  );
}
