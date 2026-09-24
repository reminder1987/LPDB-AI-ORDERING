export type DashboardNavigationItem = {
  label: string;
  href: string;
  description: string;
  enabled: boolean;
};

export const dashboardNavigation: DashboardNavigationItem[] = [
  {
    label: "Resumen",
    href: "/",
    description: "Vista general de la operación",
    enabled: false,
  },
  {
    label: "Pedidos",
    href: "/",
    description: "Pedidos y operación en tiempo real",
    enabled: true,
  },
  {
    label: "Operaciones",
    href: "/operaciones",
    description: "Incidentes y salud operacional",
    enabled: false,
  },
  {
    label: "Métricas",
    href: "/metricas",
    description: "Indicadores operativos y comerciales",
    enabled: false,
  },
  {
    label: "Configuración",
    href: "/configuracion",
    description: "Restaurante, integraciones y usuarios",
    enabled: false,
  },
];
