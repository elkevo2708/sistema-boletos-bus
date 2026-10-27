import { lazy, Suspense } from 'react';
import { Navigate, Route, Routes, useParams } from 'react-router-dom';
import Layout from './componentes/Layout';
import PortalLayout from './componentes/PortalLayout';
import PortalInicio from './paginas/PortalInicio';
import { Esqueleto } from './ui/ui';

const Admin = lazy(() => import('./paginas/Admin'));
const Asientos = lazy(() => import('./paginas/Asientos'));
const Blog = lazy(() => import('./paginas/Blog'));
const BlogDetalle = lazy(() => import('./paginas/BlogDetalle'));
const Buscar = lazy(() => import('./paginas/Buscar'));
const Encomiendas = lazy(() => import('./paginas/Encomiendas'));
const Galeria = lazy(() => import('./paginas/Galeria'));
const Login = lazy(() => import('./paginas/Login'));
const MisFacturas = lazy(() => import('./paginas/MisFacturas'));
const PortalAgenda = lazy(() => import('./paginas/PortalAgenda'));
const PortalEvento = lazy(() => import('./paginas/PortalAgenda').then((modulo) => ({ default: modulo.PortalEvento })));
const PortalContacto = lazy(() => import('./paginas/PortalContacto'));
const PortalExplorar = lazy(() => import('./paginas/PortalExplorar'));
const PortalFicha = lazy(() => import('./paginas/PortalFicha'));
const PortalGaleria = lazy(() => import('./paginas/PortalGaleria'));
const PortalLista = lazy(() => import('./paginas/PortalLista'));
const PortalMapa = lazy(() => import('./paginas/PortalMapa'));
const Taxi = lazy(() => import('./paginas/Taxi'));
const Conductor = lazy(() => import('./paginas/Conductor'));

function Carga({ children }) {
  return <Suspense fallback={<div className="portal-bloque esqueleto-pagina"><Esqueleto /></div>}>{children}</Suspense>;
}

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
        <Route path="/" element={<Carga><PortalInicio /></Carga>} />
        <Route path="/explorar" element={<Carga><PortalExplorar /></Carga>} />
        <Route path="/aprende" element={<Carga><PortalLista tipo="guia" titulo="Aprende" bajada="Cómo llegar, el clima y lo práctico, sin cifras inventadas." /></Carga>} />
        <Route path="/aprende/:slug" element={<Carga><PortalFicha tipo="guia" volver="Aprende" /></Carga>} />
        <Route path="/atractivos" element={<Carga><PortalLista tipo="atractivo" titulo="Descubre" bajada="Río, cascadas, pueblo y fincas del cantón." imagen="/turismo/panoramica.jpg" /></Carga>} />
        <Route path="/atractivos/:slug" element={<Carga><PortalFicha tipo="atractivo" volver="Descubre" /></Carga>} />
        <Route path="/parroquias" element={<Carga><PortalLista tipo="parroquia" titulo="Parroquias" bajada="La cabecera y las parroquias rurales de La Maná." /></Carga>} />
        <Route path="/parroquias/:slug" element={<Carga><PortalFicha tipo="parroquia" volver="Parroquias" /></Carga>} />
        <Route path="/gastronomia" element={<Carga><PortalLista tipo="gastronomia" titulo="Gastronomía" bajada="La mesa del subtrópico, sin un local decretado." imagen="/turismo/cacao.jpg" /></Carga>} />
        <Route path="/emprendimientos" element={<Carga><PortalLista tipo="emprendimiento" titulo="Emprendimientos" bajada="Fichas de muestra hasta que un operador publique un negocio real." imagen="/turismo/cacao.jpg" /></Carga>} />
        <Route path="/emprendimientos/:slug" element={<Carga><PortalFicha tipo="emprendimiento" volver="Emprendimientos" /></Carga>} />
        <Route path="/directorio" element={<Carga><PortalLista tipo="directorio" titulo="Directorio" bajada="Servicios de ejemplo. Los negocios reales se cargan en el panel." /></Carga>} />
        <Route path="/directorio/:slug" element={<Carga><PortalFicha tipo="directorio" volver="Directorio" /></Carga>} />
        <Route path="/gastronomia/:slug" element={<Carga><PortalFicha tipo="gastronomia" volver="Gastronomía" /></Carga>} />
        <Route path="/hospedaje" element={<Carga><PortalLista tipo="hospedaje" titulo="Hospedaje" bajada="Tipos de alojamiento. Los nombres concretos se cargan en taquilla." /></Carga>} />
        <Route path="/hospedaje/:slug" element={<Carga><PortalFicha tipo="hospedaje" volver="Hospedaje" /></Carga>} />
        <Route path="/actividades" element={<Carga><PortalLista tipo="actividad" titulo="Vive" bajada="Caminata, río y bosque." imagen="/turismo/fauna.jpg" /></Carga>} />
        <Route path="/actividades/:slug" element={<Carga><PortalFicha tipo="actividad" volver="Vive" /></Carga>} />
        <Route path="/rutas" element={<Carga><PortalLista tipo="ruta" titulo="Rutas" bajada="Una jornada en el cantón y el modo de llegar." /></Carga>} />
        <Route path="/rutas/:slug" element={<Carga><PortalFicha tipo="ruta" volver="Rutas" /></Carga>} />
        <Route path="/agenda" element={<Carga><PortalAgenda /></Carga>} />
        <Route path="/agenda/:slug" element={<Carga><PortalEvento /></Carga>} />
        <Route path="/galeria" element={<Carga><PortalGaleria /></Carga>} />
        <Route path="/mapa" element={<Carga><PortalMapa /></Carga>} />
        <Route path="/contacto" element={<Carga><PortalContacto /></Carga>} />
        <Route path="/taxi" element={<Carga><Taxi /></Carga>} />
      </Route>
      <Route path="/conductor" element={<Carga><Conductor /></Carga>} />
      <Route path="/viajes/:id" element={<ViajeViejo />} />
      <Route path="/noticias/:slug" element={<NotaVieja />} />
      <Route path="/noticias" element={<Navigate to="/transporte/noticias" replace />} />
      <Route path="/encomiendas" element={<Navigate to="/transporte/encomiendas" replace />} />
      <Route element={<Layout />}>
        <Route path="/transporte" element={<Carga><Buscar /></Carga>} />
        <Route path="/transporte/viajes/:id" element={<Carga><Asientos /></Carga>} />
        <Route path="/transporte/noticias" element={<Carga><Blog /></Carga>} />
        <Route path="/transporte/noticias/:slug" element={<Carga><BlogDetalle /></Carga>} />
        <Route path="/transporte/galeria" element={<Carga><Galeria /></Carga>} />
        <Route path="/transporte/encomiendas" element={<Carga><Encomiendas /></Carga>} />
        <Route path="/ingresar" element={<Carga><Login /></Carga>} />
        <Route path="/mis-facturas" element={<Carga><MisFacturas /></Carga>} />
        <Route path="/admin" element={<Carga><Admin /></Carga>} />
      </Route>
    </Routes>
  );
}
