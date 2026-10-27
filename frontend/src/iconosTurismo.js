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
  Landmark,
  Mail,
  Map,
  MapPinned,
  Route,
  Search,
  Signpost,
  Sun,
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
};

export const MENU_PORTAL = [
  { to: '/', label: 'La Maná', Icono: Landmark, fin: true, concepto: 'Lugar del destino' },
  { to: '/aprende', label: 'Aprende', Icono: BookOpen, tipo: 'guia', concepto: 'Estudio' },
  { to: '/atractivos', label: 'Descubre', Icono: Compass, tipo: 'atractivo', concepto: 'Explorar' },
  { to: '/parroquias', label: 'Parroquias', Icono: Map, tipo: 'parroquia', concepto: 'Territorio' },
  { to: '/gastronomia', label: 'Gastronomía', Icono: UtensilsCrossed, tipo: 'gastronomia', concepto: 'Mesa' },
  { to: '/actividades', label: 'Vive', Icono: Sun, tipo: 'actividad', concepto: 'Experiencia' },
  { to: '/agenda', label: 'Agenda', Icono: CalendarDays, tipo: 'evento', concepto: 'Calendario' },
];

export const MENU_EXTRA = [
  { to: '/hospedaje', label: 'Hospedaje', Icono: BedDouble },
  { to: '/rutas', label: 'Rutas', Icono: Route },
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

export { Search, Bus };
