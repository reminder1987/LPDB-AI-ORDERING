import { DashboardState } from "@/components/ui/dashboard-state";
import type {
  IncidentCategory,
  IncidentSeverity,
  IncidentStatus,
  OperationalIncident,
} from "@/lib/operational/incidents";

type IncidentsTableProps = {
  incidents: OperationalIncident[];
  loading: boolean;
  error: string | null;
  onOpenIncident: (incidentId: string) => void;
};

const statusLabels: Record<IncidentStatus, string> = {
  open: "Abierto",
  resolved: "Resuelto",
};

const severityLabels: Record<IncidentSeverity, string> = {
  info: "Informacion",
  warning: "Advertencia",
  critical: "Critico",
};

const categoryLabels: Record<IncidentCategory, string> = {
  provider: "Proveedor",
  payment: "Pago",
  order: "Pedido",
  webhook: "Webhook",
  reconciliation: "Reconciliacion",
  system: "Sistema",
};

export function IncidentsTable({
  incidents,
  loading,
  error,
  onOpenIncident,
}: IncidentsTableProps) {
  if (loading) {
    return (
      <section className="overflow-hidden rounded-2xl border border-zinc-200 bg-white">
        <DashboardState
          variant="loading"
          title="Cargando incidentes..."
          description="Consultando el estado operacional del tenant."
        />
      </section>
    );
  }

  if (error) {
    return (
      <section className="overflow-hidden rounded-2xl border border-zinc-200 bg-white">
        <DashboardState
          variant="error"
          title="No fue posible cargar los incidentes."
          description={formatOperationalError(error)}
        />
      </section>
    );
  }

  if (incidents.length === 0) {
    return (
      <section className="overflow-hidden rounded-2xl border border-zinc-200 bg-white">
        <DashboardState
          variant="empty"
          title="No hay incidentes para mostrar."
          description="No se encontraron incidentes con los filtros seleccionados."
        />
      </section>
    );
  }

  return (
    <section
      className="overflow-hidden rounded-2xl border border-zinc-200 bg-white"
      aria-label="Incidentes operacionales"
    >
      <div className="border-b border-zinc-100 px-5 py-4">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h4 className="text-sm font-semibold text-zinc-900">
              Incidentes
            </h4>

            <p className="mt-1 text-xs text-zinc-400">
              {incidents.length} resultado(s)
            </p>
          </div>
        </div>
      </div>

      <div className="divide-y divide-zinc-100 md:hidden">
        {incidents.map((incident) => (
          <button
            key={incident.id}
            type="button"
            onClick={() => onOpenIncident(incident.id)}
            className="block min-h-11 w-full p-5 text-left transition hover:bg-zinc-50 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-zinc-400"
            aria-label={`Abrir incidente ${incident.title}`}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-zinc-900">
                  {incident.title}
                </p>

                <p className="mt-1 text-xs text-zinc-400">
                  {categoryLabels[incident.category]}
                </p>
              </div>

              <SeverityBadge severity={incident.severity} />
            </div>

            <div className="mt-4 flex flex-wrap items-center gap-2 text-xs text-zinc-500">
              <StatusBadge status={incident.status} />

              <span>
                {incident.occurrence_count} ocurrencia(s)
              </span>

              <span>
                {formatDateTime(incident.last_seen_at)}
              </span>
            </div>
          </button>
        ))}
      </div>

      <div className="hidden overflow-x-auto md:block">
        <table className="w-full border-collapse text-left">
          <thead>
            <tr className="border-b border-zinc-100 text-xs font-medium text-zinc-400">
              <th scope="col" className="px-5 py-3">
                Incidente
              </th>

              <th scope="col" className="px-5 py-3">
                Categoria
              </th>

              <th scope="col" className="px-5 py-3">
                Severidad
              </th>

              <th scope="col" className="px-5 py-3">
                Estado
              </th>

              <th scope="col" className="px-5 py-3">
                Ocurrencias
              </th>

              <th scope="col" className="px-5 py-3">
                Ultima deteccion
              </th>
            </tr>
          </thead>

          <tbody className="divide-y divide-zinc-100">
            {incidents.map((incident) => (
              <tr
                key={incident.id}
                role="button"
                tabIndex={0}
                onClick={() =>
                  onOpenIncident(incident.id)
                }
                onKeyDown={(event) => {
                  if (
                    event.key === "Enter" ||
                    event.key === " "
                  ) {
                    event.preventDefault();
                    onOpenIncident(incident.id);
                  }
                }}
                className="cursor-pointer transition hover:bg-zinc-50 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-zinc-400"
                aria-label={`Abrir incidente ${incident.title}`}
              >
                <td className="max-w-xs px-5 py-4">
                  <p className="truncate text-sm font-medium text-zinc-900">
                    {incident.title}
                  </p>

                  {incident.provider && (
                    <p className="mt-1 truncate text-xs text-zinc-400">
                      {incident.provider}
                    </p>
                  )}
                </td>

                <td className="px-5 py-4 text-sm text-zinc-600">
                  {categoryLabels[incident.category]}
                </td>

                <td className="px-5 py-4">
                  <SeverityBadge
                    severity={incident.severity}
                  />
                </td>

                <td className="px-5 py-4">
                  <StatusBadge status={incident.status} />
                </td>

                <td className="px-5 py-4 text-sm text-zinc-600">
                  {incident.occurrence_count}
                </td>

                <td className="whitespace-nowrap px-5 py-4 text-sm text-zinc-500">
                  {formatDateTime(incident.last_seen_at)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function SeverityBadge({
  severity,
}: {
  severity: IncidentSeverity;
}) {
  const classes: Record<IncidentSeverity, string> = {
    info: "bg-blue-50 text-blue-700",
    warning: "bg-amber-50 text-amber-700",
    critical: "bg-red-50 text-red-700",
  };

  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${classes[severity]}`}
    >
      {severityLabels[severity]}
    </span>
  );
}

function StatusBadge({
  status,
}: {
  status: IncidentStatus;
}) {
  const classes: Record<IncidentStatus, string> = {
    open: "bg-red-50 text-red-700",
    resolved: "bg-emerald-50 text-emerald-700",
  };

  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${classes[status]}`}
    >
      {statusLabels[status]}
    </span>
  );
}

function formatDateTime(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("es-CO", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(date);
}

function formatOperationalError(error: string): string {
  if (error === "PERMISSION_DENIED") {
    return "Tu rol no tiene permiso para consultar esta informacion.";
  }

  if (error === "AUTH_REQUIRED") {
    return "La sesion expiro. Inicia sesion nuevamente.";
  }

  return error;
}