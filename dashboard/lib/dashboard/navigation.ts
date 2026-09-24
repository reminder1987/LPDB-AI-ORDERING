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
    description: "Vista general de la operacion",
    enabled: false,
  },
  {
    label: "Pedidos",
    href: "/pedidos",
    description: "Pedidos y operacion en tiempo real",
    enabled: true,
  },
  {
    label: "Operaciones",
    href: "/operaciones",
    description: "Incidentes y salud operacional",
    enabled: false,
  },
  {
    label: "Metricas",
    href: "/metricas",
    description: "Indicadores operativos y comerciales",
    enabled: false,
  },
  {
    label: "Configuracion",
    href: "/configuracion",
    description: "Restaurante, integraciones y usuarios",
    enabled: false,
  },
];
