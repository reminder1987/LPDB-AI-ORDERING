"use client";

import {
  FormEvent,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  getOperationalActivity,
  type OperationalActivity,
  type OperationalActivitySource,
} from "@/lib/api";

type SourceFilter =
  | "all"
  | OperationalActivitySource;

const SOURCE_LABELS: Record<
  OperationalActivitySource,
  string
> = {
  payment: "Pagos",
  incident: "Incidentes",
  integration: "Integraciones",
  webhook: "Eventos externos",
};

function getErrorMessage(error: unknown): string {
  if (!(error instanceof Error)) {
    return "Ocurrio un error inesperado.";
  }

  if (error.message === "AUTH_REQUIRED") {
    return "La sesion expiro. Inicia sesion nuevamente.";
  }

  if (
    error.message.includes("API error 403") ||
    error.message.includes("API error 401")
  ) {
    return "No tienes permisos para consultar la actividad operativa.";
  }

  return error.message;
}

function formatDate(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("es-CO", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function formatSource(
  source: OperationalActivitySource,
): string {
  return SOURCE_LABELS[source];
}

function formatStatus(
  status: string | null,
): string {
  if (!status) {
    return "Sin estado";
  }

  return status.replaceAll("_", " ");
}

function ActivityMetric({
  label,
  value,
  description,
}: {
  label: string;
  value: number;
  description: string;
}) {
  return (
    <article className="rounded-xl border border-zinc-200 bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
        {label}
      </p>

      <p className="mt-2 text-2xl font-bold tracking-tight text-zinc-950">
        {value}
      </p>

      <p className="mt-1 text-xs leading-5 text-zinc-500">
        {description}
      </p>
    </article>
  );
}

function ActivityTable({
  activities,
  loading,
  error,
}: {
  activities: OperationalActivity[];
  loading: boolean;
  error: string | null;
}) {
  if (loading) {
    return (
      <section
        className="rounded-xl border border-zinc-200 bg-white p-6"
        aria-live="polite"
      >
        <p className="text-sm text-zinc-600">
          Cargando actividad operativa...
        </p>
      </section>
    );
  }

  if (error) {
    return (
      <section
        className="rounded-xl border border-red-200 bg-red-50 p-6"
        role="alert"
      >
        <h3 className="text-sm font-semibold text-red-900">
          No fue posible cargar la actividad
        </h3>

        <p className="mt-2 text-sm text-red-700">
          {error}
        </p>
      </section>
    );
  }

  if (activities.length === 0) {
    return (
      <section
        className="rounded-xl border border-zinc-200 bg-white p-6"
        aria-live="polite"
      >
        <h3 className="text-sm font-semibold text-zinc-950">
          Sin actividad
        </h3>

        <p className="mt-2 text-sm text-zinc-500">
          No hay registros que coincidan con los filtros
          seleccionados.
        </p>
      </section>
    );
  }

  return (
    <section
      className="overflow-hidden rounded-xl border border-zinc-200 bg-white"
      aria-labelledby="activity-table-title"
    >
      <div className="border-b border-zinc-200 px-4 py-4 md:px-5">
        <h3
          id="activity-table-title"
          className="text-sm font-semibold text-zinc-950"
        >
          Actividad reciente
        </h3>

        <p className="mt-1 text-xs text-zinc-500">
          Registros operativos ordenados del mas reciente al
          mas antiguo.
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-zinc-200">
          <thead className="bg-zinc-50">
            <tr>
              <th
                scope="col"
                className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500 md:px-5"
              >
                Fecha
              </th>

              <th
                scope="col"
                className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500"
              >
                Fuente
              </th>

              <th
                scope="col"
                className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500"
              >
                Actividad
              </th>

              <th
                scope="col"
                className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500"
              >
                Proveedor
              </th>

              <th
                scope="col"
                className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500"
              >
                Estado
              </th>
            </tr>
          </thead>

          <tbody className="divide-y divide-zinc-100">
            {activities.map((activity) => (
              <tr
                key={activity.id}
                className="align-top transition hover:bg-zinc-50"
              >
                <td className="whitespace-nowrap px-4 py-4 text-xs text-zinc-500 md:px-5">
                  {formatDate(activity.occurred_at)}
                </td>

                <td className="whitespace-nowrap px-4 py-4">
                  <span className="inline-flex rounded-full bg-zinc-100 px-2.5 py-1 text-xs font-medium text-zinc-700">
                    {formatSource(activity.source)}
                  </span>
                </td>

                <td className="min-w-72 px-4 py-4">
                  <p className="text-sm font-semibold text-zinc-950">
                    {activity.title}
                  </p>

                  <p className="mt-1 text-xs leading-5 text-zinc-500">
                    {activity.description}
                  </p>

                  <p className="mt-2 text-xs text-zinc-400">
                    {activity.event_type}
                    {" · "}
                    {activity.entity_type}
                    {" #"}
                    {activity.entity_id}
                  </p>
                </td>

                <td className="whitespace-nowrap px-4 py-4 text-sm text-zinc-700">
                  {activity.provider ?? "—"}
                </td>

                <td className="whitespace-nowrap px-4 py-4">
                  {activity.status ? (
                    <span className="inline-flex rounded-full border border-zinc-200 bg-white px-2.5 py-1 text-xs font-medium capitalize text-zinc-700">
                      {formatStatus(activity.status)}
                    </span>
                  ) : activity.severity ? (
                    <span className="inline-flex rounded-full border border-zinc-200 bg-white px-2.5 py-1 text-xs font-medium capitalize text-zinc-700">
                      {activity.severity}
                    </span>
                  ) : (
                    <span className="text-xs text-zinc-400">
                      —
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export function ActivityDashboard() {
  const [activities, setActivities] = useState<
    OperationalActivity[]
  >([]);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState<string | null>(
    null,
  );

  const [sourceFilter, setSourceFilter] =
    useState<SourceFilter>("all");

  const [providerInput, setProviderInput] =
    useState("");

  const [providerFilter, setProviderFilter] =
    useState("");

  const [limitFilter, setLimitFilter] =
    useState(100);

  useEffect(() => {
    let active = true;

    async function loadActivity() {
      setLoading(true);
      setError(null);

      try {
        const result = await getOperationalActivity({
          source:
            sourceFilter === "all"
              ? undefined
              : sourceFilter,
          provider:
            providerFilter || undefined,
          limit: limitFilter,
        });

        if (!active) {
          return;
        }

        setActivities(result);
      } catch (loadError) {
        if (!active) {
          return;
        }

        setActivities([]);
        setError(
          getErrorMessage(loadError),
        );
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadActivity();

    return () => {
      active = false;
    };
  }, [
    sourceFilter,
    providerFilter,
    limitFilter,
  ]);

  const metrics = useMemo(() => {
    const incidents = activities.filter(
      (activity) =>
        activity.source === "incident",
    ).length;

    const externalEvents = activities.filter(
      (activity) =>
        activity.source === "webhook",
    ).length;

    const providers = new Set(
      activities
        .map((activity) =>
          activity.provider
            ?.trim()
            .toLowerCase(),
        )
        .filter(
          (provider): provider is string =>
            Boolean(provider),
        ),
    ).size;

    return {
      total: activities.length,
      incidents,
      externalEvents,
      providers,
    };
  }, [activities]);

  function handleFiltersSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setProviderFilter(
      providerInput.trim(),
    );
  }

  function clearFilters() {
    setSourceFilter("all");
    setProviderInput("");
    setProviderFilter("");
    setLimitFilter(100);
  }

  const filtersApplied =
    sourceFilter !== "all" ||
    Boolean(providerFilter) ||
    limitFilter !== 100;

  return (
    <div className="space-y-6">
      <header>
        <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
          Operacion
        </p>

        <div className="mt-1 flex flex-wrap items-end justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-zinc-950">
              Actividad operativa
            </h2>

            <p className="mt-2 max-w-3xl text-sm leading-6 text-zinc-500">
              Consulta una vista consolidada de pagos,
              incidentes, integraciones y eventos externos
              del tenant actual.
            </p>
          </div>

          <div
            className="rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-2"
            role="note"
          >
            <p className="text-xs font-medium text-zinc-700">
              Vista de solo lectura
            </p>
          </div>
        </div>

        <div
          className="mt-4 rounded-lg border border-zinc-200 bg-zinc-50 px-4 py-3"
          role="note"
        >
          <p className="text-xs leading-5 text-zinc-600">
            Esta vista consolida el estado operativo
            disponible actualmente. No sustituye un registro
            historico de auditoria inmutable.
          </p>
        </div>
      </header>

      <section
        className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"
        aria-label="Resumen de actividad operativa"
      >
        <ActivityMetric
          label="Registros"
          value={metrics.total}
          description="Actividad visible con los filtros actuales."
        />

        <ActivityMetric
          label="Incidentes"
          value={metrics.incidents}
          description="Incidentes incluidos en la actividad cargada."
        />

        <ActivityMetric
          label="Eventos externos"
          value={metrics.externalEvents}
          description="Webhooks recibidos incluidos en la vista."
        />

        <ActivityMetric
          label="Proveedores"
          value={metrics.providers}
          description="Proveedores distintos presentes en los registros."
        />
      </section>

      <section
        className="rounded-xl border border-zinc-200 bg-white p-4 md:p-5"
        aria-labelledby="activity-filters-title"
      >
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h3
              id="activity-filters-title"
              className="text-sm font-semibold text-zinc-950"
            >
              Filtros
            </h3>

            <p className="mt-1 text-xs text-zinc-500">
              Filtra la actividad por fuente, proveedor y
              cantidad maxima de registros.
            </p>
          </div>

          {filtersApplied && (
            <button
              type="button"
              onClick={clearFilters}
              className="rounded-lg border border-zinc-300 px-3 py-2 text-xs font-medium text-zinc-700 transition hover:bg-zinc-100 focus:outline-none focus:ring-2 focus:ring-zinc-400 focus:ring-offset-2"
            >
              Limpiar filtros
            </button>
          )}
        </div>

        <form
          className="mt-4 grid gap-4 lg:grid-cols-[1fr_1fr_auto_auto]"
          onSubmit={handleFiltersSubmit}
        >
          <label className="block">
            <span className="text-xs font-medium text-zinc-600">
              Fuente
            </span>

            <select
              value={sourceFilter}
              onChange={(event) =>
                setSourceFilter(
                  event.target.value as SourceFilter,
                )
              }
              className="mt-1.5 w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm text-zinc-950 outline-none transition focus:border-zinc-500 focus:ring-2 focus:ring-zinc-200"
            >
              <option value="all">
                Todas
              </option>

              <option value="payment">
                Pagos
              </option>

              <option value="incident">
                Incidentes
              </option>

              <option value="integration">
                Integraciones
              </option>

              <option value="webhook">
                Eventos externos
              </option>
            </select>
          </label>

          <label className="block">
            <span className="text-xs font-medium text-zinc-600">
              Proveedor
            </span>

            <input
              type="text"
              value={providerInput}
              onChange={(event) =>
                setProviderInput(
                  event.target.value,
                )
              }
              placeholder="Ej. toast"
              className="mt-1.5 w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm text-zinc-950 outline-none transition placeholder:text-zinc-400 focus:border-zinc-500 focus:ring-2 focus:ring-zinc-200"
            />
          </label>

          <label className="block">
            <span className="text-xs font-medium text-zinc-600">
              Limite
            </span>

            <select
              value={limitFilter}
              onChange={(event) =>
                setLimitFilter(
                  Number(event.target.value),
                )
              }
              className="mt-1.5 w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm text-zinc-950 outline-none transition focus:border-zinc-500 focus:ring-2 focus:ring-zinc-200"
            >
              <option value={25}>
                25
              </option>

              <option value={50}>
                50
              </option>

              <option value={100}>
                100
              </option>

              <option value={250}>
                250
              </option>
            </select>
          </label>

          <div className="flex items-end">
            <button
              type="submit"
              className="w-full rounded-lg bg-zinc-950 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-zinc-800 focus:outline-none focus:ring-2 focus:ring-zinc-500 focus:ring-offset-2 lg:w-auto"
            >
              Aplicar
            </button>
          </div>
        </form>
      </section>

      <ActivityTable
        activities={activities}
        loading={loading}
        error={error}
      />
    </div>
  );
}