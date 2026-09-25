export type DashboardNavigationItem = {
  label: string;
  href: string;
  description: string;
  enabled: boolean;
};

export type DashboardNavigationContext = {
  tenantSlug: string;
  role: string;
};

const dashboardNavigationItems: DashboardNavigationItem[] = [
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
    enabled: true,
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

export function getDashboardNavigation(
  context: DashboardNavigationContext,
): DashboardNavigationItem[] {
  void context;

  return dashboardNavigationItems;
}

export function isDashboardNavigationItemActive(
  pathname: string,
  href: string,
): boolean {
  if (href === "/") {
    return pathname === "/";
  }

  return (
    pathname === href ||
    pathname.startsWith(`${href}/`)
  );
}