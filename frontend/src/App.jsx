import { Navigate, Route, Routes, useParams } from 'react-router-dom';
import Layout from './componentes/Layout';
import PortalLayout from './componentes/PortalLayout';
import Admin from './paginas/Admin';
import Asientos from './paginas/Asientos';
import Blog from './paginas/Blog';
import BlogDetalle from './paginas/BlogDetalle';
import Buscar from './paginas/Buscar';
import Encomiendas from './paginas/Encomiendas';
import Galeria from './paginas/Galeria';
import Login from './paginas/Login';
import MisFacturas from './paginas/MisFacturas';
import PortalAgenda, { PortalEvento } from './paginas/PortalAgenda';
import PortalContacto from './paginas/PortalContacto';
import PortalExplorar from './paginas/PortalExplorar';
import PortalFicha from './paginas/PortalFicha';
import PortalGaleria from './paginas/PortalGaleria';
import PortalInicio from './paginas/PortalInicio';
import PortalLista from './paginas/PortalLista';
import PortalMapa from './paginas/PortalMapa';
import Taxi from './paginas/Taxi';
import Conductor from './paginas/Conductor';

function ViajeViejo() {
  const { id } = useParams();
  return <Navigate to={`/transporte/viajes/${id}`} replace />;
}

function NotaVieja() {
  const { slug } = useParams();
  return <Navigate to={`/transporte/noticias/${slug}`} replace />;
}

export default function App() {
  return (
    <Routes>
      <Route element={<PortalLayout />}>
        <Route path="/" element={<PortalInicio />} />
        <Route path="/explorar" element={<PortalExplorar />} />
        <Route path="/aprende" element={<PortalLista tipo="guia" titulo="Aprende" bajada="Cómo llegar, el clima y lo práctico, sin cifras inventadas." />} />
        <Route path="/aprende/:slug" element={<PortalFicha tipo="guia" volver="Aprende" />} />
        <Route path="/atractivos" element={<PortalLista tipo="atractivo" titulo="Descubre" bajada="Río, cascadas, pueblo y fincas del cantón." />} />
        <Route path="/atractivos/:slug" element={<PortalFicha tipo="atractivo" volver="Descubre" />} />
        <Route path="/parroquias" element={<PortalLista tipo="parroquia" titulo="Parroquias" bajada="La cabecera y las parroquias rurales de La Maná." />} />
        <Route path="/parroquias/:slug" element={<PortalFicha tipo="parroquia" volver="Parroquias" />} />
        <Route path="/gastronomia" element={<PortalLista tipo="gastronomia" titulo="Gastronomía" bajada="La mesa del subtrópico, sin un local decretado." />} />
        <Route path="/emprendimientos" element={<PortalLista tipo="emprendimiento" titulo="Emprendimientos" bajada="Fichas de muestra hasta que un operador publique un negocio real." />} />
        <Route path="/emprendimientos/:slug" element={<PortalFicha tipo="emprendimiento" volver="Emprendimientos" />} />
        <Route path="/directorio" element={<PortalLista tipo="directorio" titulo="Directorio" bajada="Servicios de ejemplo. Los negocios reales se cargan en el panel." />} />
        <Route path="/directorio/:slug" element={<PortalFicha tipo="directorio" volver="Directorio" />} />
        <Route path="/gastronomia/:slug" element={<PortalFicha tipo="gastronomia" volver="Gastronomía" />} />
        <Route path="/hospedaje" element={<PortalLista tipo="hospedaje" titulo="Hospedaje" bajada="Tipos de alojamiento. Los nombres concretos se cargan en taquilla." />} />
        <Route path="/hospedaje/:slug" element={<PortalFicha tipo="hospedaje" volver="Hospedaje" />} />
        <Route path="/actividades" element={<PortalLista tipo="actividad" titulo="Vive" bajada="Caminata, río y bosque." />} />
        <Route path="/actividades/:slug" element={<PortalFicha tipo="actividad" volver="Vive" />} />
        <Route path="/rutas" element={<PortalLista tipo="ruta" titulo="Rutas" bajada="Una jornada en el cantón y el modo de llegar." />} />
        <Route path="/rutas/:slug" element={<PortalFicha tipo="ruta" volver="Rutas" />} />
        <Route path="/agenda" element={<PortalAgenda />} />
        <Route path="/agenda/:slug" element={<PortalEvento />} />
        <Route path="/galeria" element={<PortalGaleria />} />
        <Route path="/mapa" element={<PortalMapa />} />
        <Route path="/contacto" element={<PortalContacto />} />
        <Route path="/taxi" element={<Taxi />} />
      </Route>
      <Route path="/conductor" element={<Conductor />} />
      <Route path="/viajes/:id" element={<ViajeViejo />} />
      <Route path="/noticias/:slug" element={<NotaVieja />} />
      <Route path="/noticias" element={<Navigate to="/transporte/noticias" replace />} />
      <Route path="/encomiendas" element={<Navigate to="/transporte/encomiendas" replace />} />
      <Route element={<Layout />}>
        <Route path="/transporte" element={<Buscar />} />
        <Route path="/transporte/viajes/:id" element={<Asientos />} />
        <Route path="/transporte/noticias" element={<Blog />} />
        <Route path="/transporte/noticias/:slug" element={<BlogDetalle />} />
        <Route path="/transporte/galeria" element={<Galeria />} />
        <Route path="/transporte/encomiendas" element={<Encomiendas />} />
        <Route path="/ingresar" element={<Login />} />
        <Route path="/mis-facturas" element={<MisFacturas />} />
        <Route path="/admin" element={<Admin />} />
      </Route>
    </Routes>
  );
}
