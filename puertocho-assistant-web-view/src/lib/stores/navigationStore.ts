import { writable } from 'svelte/store';

export type ViewType = 'home' | 'config' | 'history' | 'logs' | 'settings';

export type NavigationItem = {
  id: ViewType;
  label: string;
  icon: string;
  description?: string;
};

export const navigationItems: NavigationItem[] = [
  { id: 'home', label: 'Inicio', icon: 'home_icon', description: 'Panel principal' },
  { id: 'config', label: 'Configuración', icon: 'configuration_icon', description: 'Configuración del asistente' },
  { id: 'history', label: 'Historial', icon: 'historial_icon', description: 'Historial de comandos' },
  { id: 'logs', label: 'Registros', icon: 'registro_icon', description: 'Logs del sistema' },
  { id: 'settings', label: 'Sistema', icon: 'sistema_icon', description: 'Configuración del sistema' }
];

// Store para la vista activa
export const activeView = writable<ViewType>('home');

// Store para controlar la visibilidad de la navegación lateral
export const sideNavVisible = writable<boolean>(true);

// Funciones de utilidad
export const navigationStore = {
  setActiveView: (view: ViewType) => {
    activeView.set(view);
  },
  
  toggleSideNav: () => {
    sideNavVisible.update(visible => !visible);
  },
  
  getNavigationItem: (id: ViewType): NavigationItem | undefined => {
    return navigationItems.find(item => item.id === id);
  }
};
