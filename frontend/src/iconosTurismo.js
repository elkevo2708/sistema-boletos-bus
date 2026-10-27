import {
  BedDouble,
  BookOpen,
  Bus,
  CalendarDays,
  CloudSun,
  Coins,
  Compass,
  FileText,
  Images,
  Mail,
  Map,
  MapPin,
  MapPinned,
  Route,
  Search,
  Signpost,
  Store,
  Sun,
  UserRound,
  UtensilsCrossed,
} from 'lucide-react';

export const RUTA_TIPO = {
  atractivo: '/atractivos',
  gastronomia: '/gastronomia',
  hospedaje: '/hospedaje',
  actividad: '/actividades',
  ruta: '/rutas',
  parroquia: '/parroquias',
  guia: '/aprende',
  emprendimiento: '/emprendimientos',
  directorio: '/directorio',
};

export const IDIOMAS = {
  es: {
    lamana: 'La Maná',
    aprende: 'Aprende',
    emprendimientos: 'Emprendimientos',
    directorio: 'Directorio',
    vive: 'Vive',
    descubre: 'Descubre',
    destinos: 'Destinos',
    transporte: 'Transporte',
    taxi: 'Taxi',
    login: 'Login',
    buscar: 'Buscar en La Maná',
  },
  en: {
    lamana: 'La Maná',
    aprende: 'Learn',
    emprendimientos: 'Business',
    directorio: 'Directory',
    vive: 'Live',
    descubre: 'Discover',
    destinos: 'Places',
    transporte: 'Transport',
    taxi: 'Taxi',
    login: 'Login',
    buscar: 'Search La Maná',
  },
};

export const MENU_PORTAL = [
  { to: '/', clave: 'lamana', Icono: MapPin, fin: true, conteo: 'lamana' },
  { to: '/aprende', clave: 'aprende', Icono: BookOpen, tipo: 'guia' },
  { to: '/emprendimientos', clave: 'emprendimientos', Icono: Store, tipo: 'emprendimiento' },
  { to: '/directorio', clave: 'directorio', Icono: FileText, tipo: 'directorio' },
  { to: '/actividades', clave: 'vive', Icono: Sun, tipo: 'actividad' },
  { to: '/atractivos', clave: 'descubre', Icono: Compass, tipo: 'atractivo' },
  { to: '/parroquias', clave: 'destinos', Icono: Map, tipo: 'parroquia' },
  { to: '/transporte', clave: 'transporte', Icono: Bus, tipo: 'transporte' },
  { to: '/taxi', clave: 'taxi', Icono: MapPinned, tipo: 'taxi' },
];

export const MENU_EXTRA = [
  { to: '/hospedaje', label: 'Hospedaje', Icono: BedDouble },
  { to: '/gastronomia', label: 'Gastronomía', Icono: UtensilsCrossed },
  { to: '/rutas', label: 'Rutas', Icono: Route },
  { to: '/agenda', label: 'Agenda', Icono: CalendarDays },
  { to: '/galeria', label: 'Galería', Icono: Images },
  { to: '/mapa', label: 'Mapa', Icono: MapPinned },
  { to: '/contacto', label: 'Contacto', Icono: Mail },
];

export const ICONOS_PRACTICOS = [
  { Icono: Signpost, texto: 'Cómo llegar' },
  { Icono: CloudSun, texto: 'Clima' },
  { Icono: Coins, texto: 'Dinero' },
  { Icono: FileText, texto: 'Papeles' },
];

export { Search, Bus, UserRound };
