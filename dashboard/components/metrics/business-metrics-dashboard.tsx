"use client";

import { useEffect, useState } from "react";

import {
  getBusinessMetricsConversions,
  getBusinessMetricsEvolution,
  getBusinessMetricsLocations,
  getBusinessMetricsSummary,
  type BusinessMetricsConversions,
  type BusinessMetricsFilters,
  type BusinessMetricsLocation,
  type BusinessMetricsSummary,
  type BusinessMetricsTimePoint,
} from "@/lib/api";

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
  }).format(Number(value));
}

function formatRate(value: number): string {
  return new Intl.NumberFormat("es-CO", {
    style: "percent",
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(Number(value));
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("es-CO", {
    year: "numeric",
    month: "short",
    day: "numeric",
    timeZone: "UTC",
  }).format(new Date(`${value}T00:00:00Z`));
}

function getExclusiveEndDate(value: string): string {
  const [year, month, day] = value.split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));

  date.setUTCDate(date.getUTCDate() + 1);

  return date.toISOString().slice(0, 10);
}

function getMetricsErrorMessage(error: unknown): string {
  if (!(error instanceof Error)) {
    return "No fue posible cargar las metricas.";
  }

  if (error.message === "AUTH_REQUIRED") {
    return "La sesion expiro. Inicia sesion nuevamente.";
  }

  if (
    error.message === "PERMISSION_DENIED" ||
    error.message.includes("API error 403")
  ) {
    return "No tienes permisos para consultar las metricas.";
  }

  return error.message || "No fue posible cargar las metricas.";
}

type MetricCardProps = {
  label: string;
  value: string | number;
  loading: boolean;
  description?: string;
};

function MetricCard({
  label,
  value,
  loading,
  description,
}: MetricCardProps) {
  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-5">
      <p className="text-sm text-zinc-500">{label}</p>

      <p className="mt-2 text-3xl font-bold">
        {loading ? "-" : value}
      </p>

      {description && (
        <p className="mt-2 text-xs leading-5 text-zinc-400">
          {description}
        </p>
      )}
    </div>
  );
}

type StatusCardProps = {
  label: string;
  value: number;
  loading: boolean;
};

function StatusCard({
  label,
  value,
  loading,
}: StatusCardProps) {
  return (
    <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
        {label}
      </p>

      <p className="mt-2 text-2xl font-semibold text-zinc-950">
        {loading ? "-" : value}
      </p>
    </div>
  );
}

export function BusinessMetricsDashboard() {
  const [summary, setSummary] =
    useState<BusinessMetricsSummary | null>(null);

  const [evolution, setEvolution] =
    useState<BusinessMetricsTimePoint[]>([]);

  const [locations, setLocations] =
    useState<BusinessMetricsLocation[]>([]);

  const [conversions, setConversions] =
    useState<BusinessMetricsConversions | null>(null);

  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const [appliedStartDate, setAppliedStartDate] = useState("");
  const [appliedEndDate, setAppliedEndDate] = useState("");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadMetrics() {
      try {
        setLoading(true);
        setError(null);

        const filters: BusinessMetricsFilters = {
          start_at: appliedStartDate
            ? `${appliedStartDate}T00:00:00`
            : undefined,
          end_at: appliedEndDate
            ? `${getExclusiveEndDate(appliedEndDate)}T00:00:00`
            : undefined,
        };

        const [
          summaryResponse,
          evolutionResponse,
          locationsResponse,
          conversionsResponse,
        ] = await Promise.all([
          getBusinessMetricsSummary(filters),
          getBusinessMetricsEvolution(filters),
          getBusinessMetricsLocations(filters),
          getBusinessMetricsConversions(filters),
        ]);

        if (!active) {
          return;
        }

        setSummary(summaryResponse);
        setEvolution(evolutionResponse);
        setLocations(locationsResponse);
        setConversions(conversionsResponse);
      } catch (err) {
        if (!active) {
          return;
        }

        setError(getMetricsErrorMessage(err));
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadMetrics();

    return () => {
      active = false;
    };
  }, [appliedStartDate, appliedEndDate]);

  function handleApplyFilters() {
    setAppliedStartDate(startDate);
    setAppliedEndDate(endDate);
  }

  function handleClearFilters() {
    setStartDate("");
    setEndDate("");
    setAppliedStartDate("");
    setAppliedEndDate("");
  }

  const hasFilters =
    appliedStartDate.length > 0 ||
    appliedEndDate.length > 0;

  return (
    <div className="min-h-full bg-zinc-100 p-5 text-zinc-950 md:p-8">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8">
          <p className="text-sm font-medium text-zinc-500">
            Inteligencia de negocio
          </p>

          <h3 className="mt-1 text-3xl font-bold tracking-tight">
            Metricas
          </h3>

          <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-500">
            Analiza pedidos, ventas, ticket promedio, rendimiento por
            sede y estado actual de las ordenes.
          </p>
        </div>

        <section
          className="mb-6 rounded-xl border border-zinc-200 bg-white p-4 md:p-5"
          aria-labelledby="metrics-filters-title"
        >
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end">
            <div className="flex-1">
              <h4
                id="metrics-filters-title"
                className="text-sm font-semibold text-zinc-950"
              >
                Periodo
              </h4>

              <p className="mt-1 text-xs text-zinc-500">
                Filtra las metricas por fecha de creacion del pedido.
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-2 lg:w-[30rem]">
              <label className="block">
                <span className="text-xs font-medium text-zinc-600">
                  Desde
                </span>

                <input
                  type="date"
                  value={startDate}
                  onChange={(event) =>
                    setStartDate(event.target.value)
                  }
                  className="mt-1 w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm outline-none transition focus:border-zinc-500 focus:ring-2 focus:ring-zinc-200"
                />
              </label>

              <label className="block">
                <span className="text-xs font-medium text-zinc-600">
                  Hasta
                </span>

                <input
                  type="date"
                  value={endDate}
                  onChange={(event) =>
                    setEndDate(event.target.value)
                  }
                  className="mt-1 w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm outline-none transition focus:border-zinc-500 focus:ring-2 focus:ring-zinc-200"
                />
              </label>
            </div>

            <div className="flex gap-2">
              <button
                type="button"
                onClick={handleApplyFilters}
                disabled={loading}
                className="rounded-lg bg-zinc-950 px-4 py-2 text-sm font-medium text-white transition hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Aplicar
              </button>

              {(startDate || endDate || hasFilters) && (
                <button
                  type="button"
                  onClick={handleClearFilters}
                  disabled={loading}
                  className="rounded-lg border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 transition hover:bg-zinc-100 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Limpiar
                </button>
              )}
            </div>
          </div>
        </section>

        {error && (
          <div
            className="mb-6 rounded-xl border border-zinc-300 bg-white p-5"
            role="alert"
          >
            <p className="text-sm font-medium text-zinc-950">
              No fue posible cargar las metricas
            </p>

            <p className="mt-1 text-sm text-zinc-500">
              {error}
            </p>
          </div>
        )}

        <section
          className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
          aria-label="Resumen comercial"
        >
          <MetricCard
            label="Pedidos"
            value={summary?.order_count ?? 0}
            loading={loading}
          />

          <MetricCard
            label="Valor total"
            value={formatCurrency(
              summary?.total_order_value ?? 0,
            )}
            loading={loading}
          />

          <MetricCard
            label="Ticket promedio"
            value={formatCurrency(
              summary?.average_ticket ?? 0,
            )}
            loading={loading}
          />
        </section>

        <section className="mt-6 rounded-xl border border-zinc-200 bg-white p-5">
          <div>
            <p className="text-sm font-semibold text-zinc-950">
              Estado actual de pedidos
            </p>

            <p className="mt-1 text-xs leading-5 text-zinc-500">
              Distribucion actual de las ordenes del periodo. No
              representa un historial de transiciones entre estados.
            </p>
          </div>

          <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
            <StatusCard
              label="Nuevos"
              value={conversions?.created_count ?? 0}
              loading={loading}
            />

            <StatusCard
              label="Confirmados"
              value={conversions?.confirmed_count ?? 0}
              loading={loading}
            />

            <StatusCard
              label="En envio"
              value={conversions?.submitting_count ?? 0}
              loading={loading}
            />

            <StatusCard
              label="Enviados"
              value={conversions?.submitted_count ?? 0}
              loading={loading}
            />

            <StatusCard
              label="Fallidos"
              value={conversions?.failed_count ?? 0}
              loading={loading}
            />

            <StatusCard
              label="Cancelados"
              value={conversions?.cancelled_count ?? 0}
              loading={loading}
            />
          </div>

          <div className="mt-5 grid gap-4 sm:grid-cols-3">
            <MetricCard
              label="Tasa de envio"
              value={formatRate(
                conversions?.submitted_rate ?? 0,
              )}
              loading={loading}
            />

            <MetricCard
              label="Tasa de fallo"
              value={formatRate(
                conversions?.failed_rate ?? 0,
              )}
              loading={loading}
            />

            <MetricCard
              label="Tasa de cancelacion"
              value={formatRate(
                conversions?.cancelled_rate ?? 0,
              )}
              loading={loading}
            />
          </div>
        </section>

        <section className="mt-6 rounded-xl border border-zinc-200 bg-white">
          <div className="border-b border-zinc-200 p-5">
            <h4 className="text-sm font-semibold text-zinc-950">
              Evolucion diaria
            </h4>

            <p className="mt-1 text-xs text-zinc-500">
              Pedidos, valor total y ticket promedio por dia.
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-zinc-50 text-xs uppercase text-zinc-500">
                <tr>
                  <th className="px-5 py-3 font-medium">
                    Fecha
                  </th>
                  <th className="px-5 py-3 font-medium">
                    Pedidos
                  </th>
                  <th className="px-5 py-3 font-medium">
                    Valor total
                  </th>
                  <th className="px-5 py-3 font-medium">
                    Ticket promedio
                  </th>
                </tr>
              </thead>

              <tbody className="divide-y divide-zinc-100">
                {!loading &&
                  evolution.map((point) => (
                    <tr key={point.date}>
                      <td className="px-5 py-4 font-medium">
                        {formatDate(point.date)}
                      </td>
                      <td className="px-5 py-4">
                        {point.order_count}
                      </td>
                      <td className="px-5 py-4">
                        {formatCurrency(
                          point.total_order_value,
                        )}
                      </td>
                      <td className="px-5 py-4">
                        {formatCurrency(
                          point.average_ticket,
                        )}
                      </td>
                    </tr>
                  ))}

                {!loading &&
                  !error &&
                  evolution.length === 0 && (
                    <tr>
                      <td
                        colSpan={4}
                        className="px-5 py-8 text-center text-zinc-500"
                      >
                        No hay datos para el periodo seleccionado.
                      </td>
                    </tr>
                  )}
              </tbody>
            </table>
          </div>
        </section>

        <section className="mt-6 rounded-xl border border-zinc-200 bg-white">
          <div className="border-b border-zinc-200 p-5">
            <h4 className="text-sm font-semibold text-zinc-950">
              Rendimiento por sede
            </h4>

            <p className="mt-1 text-xs text-zinc-500">
              Comparativo de pedidos y valor generado por cada sede
              con actividad en el periodo.
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-zinc-50 text-xs uppercase text-zinc-500">
                <tr>
                  <th className="px-5 py-3 font-medium">
                    Sede
                  </th>
                  <th className="px-5 py-3 font-medium">
                    Ciudad
                  </th>
                  <th className="px-5 py-3 font-medium">
                    Pedidos
                  </th>
                  <th className="px-5 py-3 font-medium">
                    Valor total
                  </th>
                  <th className="px-5 py-3 font-medium">
                    Ticket promedio
                  </th>
                </tr>
              </thead>

              <tbody className="divide-y divide-zinc-100">
                {!loading &&
                  locations.map((location) => (
                    <tr key={location.location_id}>
                      <td className="px-5 py-4 font-medium">
                        {location.location_name}
                      </td>
                      <td className="px-5 py-4 text-zinc-500">
                        {location.city || "-"}
                      </td>
                      <td className="px-5 py-4">
                        {location.order_count}
                      </td>
                      <td className="px-5 py-4">
                        {formatCurrency(
                          location.total_order_value,
                        )}
                      </td>
                      <td className="px-5 py-4">
                        {formatCurrency(
                          location.average_ticket,
                        )}
                      </td>
                    </tr>
                  ))}

                {!loading &&
                  !error &&
                  locations.length === 0 && (
                    <tr>
                      <td
                        colSpan={5}
                        className="px-5 py-8 text-center text-zinc-500"
                      >
                        No hay sedes con actividad en el periodo.
                      </td>
                    </tr>
                  )}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  );
}