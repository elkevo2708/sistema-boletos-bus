import { Route, Routes } from 'react-router-dom';
import Layout from './componentes/Layout';
import Admin from './paginas/Admin';
import Asientos from './paginas/Asientos';
import Buscar from './paginas/Buscar';
import Login from './paginas/Login';

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Buscar />} />
        <Route path="/viajes/:id" element={<Asientos />} />
        <Route path="/ingresar" element={<Login />} />
        <Route path="/admin" element={<Admin />} />
      </Route>
    </Routes>
  );
}
