"use client";

import { useEffect, useState } from "react";

import {
  getOperationalIncident,
  getOperationalIncidents,
  type IncidentCategory,
  type IncidentSeverity,
  type IncidentStatus,
  type OperationalIncident,
  type OperationalIncidentFilters,
} from "@/lib/operational/incidents";

import { IncidentDetailDrawer } from "./incident-detail-drawer";
import { IncidentsTable } from "./incidents-table";

export function OperationsDashboard() {
  const [incidents, setIncidents] = useState<
    OperationalIncident[]
  >([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [status, setStatus] = useState<
    IncidentStatus | ""
  >("");
  const [severity, setSeverity] = useState<
    IncidentSeverity | ""
  >("");
  const [category, setCategory] = useState<
    IncidentCategory | ""
  >("");

  const [selectedIncident, setSelectedIncident] =
    useState<OperationalIncident | null>(null);
  const [detailLoading, setDetailLoading] =
    useState(false);
  const [detailError, setDetailError] =
    useState<string | null>(null);

  useEffect(() => {
    let active = true;

    const filters: OperationalIncidentFilters = {};

    if (status) {
      filters.status = status;
    }

    if (severity) {
      filters.severity = severity;
    }

    if (category) {
      filters.category = category;
    }

    getOperationalIncidents(filters)
      .then((response) => {
        if (!active) {
          return;
        }

        setIncidents(response);
        setError(null);
      })
      .catch((err: unknown) => {
        if (!active) {
          return;
        }

        setError(
          err instanceof Error
            ? err.message
            : "No fue posible cargar los incidentes.",
        );
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [status, severity, category]);

  useEffect(() => {
    if (!selectedIncident && !detailLoading) {
      return;
    }

    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setSelectedIncident(null);
        setDetailError(null);
      }
    }

    window.addEventListener("keydown", handleEscape);

    return () => {
      window.removeEventListener(
        "keydown",
        handleEscape,
      );
    };
  }, [selectedIncident, detailLoading]);

  async function handleOpenIncident(
    incidentId: string,
  ) {
    try {
      setDetailLoading(true);
      setDetailError(null);
      setSelectedIncident(null);

      const incident =
        await getOperationalIncident(incidentId);

      setSelectedIncident(incident);
    } catch (err) {
      setSelectedIncident(null);
      setDetailError(
        err instanceof Error
          ? err.message
          : "No fue posible cargar el incidente.",
      );
    } finally {
      setDetailLoading(false);
    }
  }

  function handleCloseIncident() {
    setSelectedIncident(null);
    setDetailError(null);
  }

  function handleStatusChange(value: string) {
    setLoading(true);
    setStatus(value as IncidentStatus | "");
  }

  function handleSeverityChange(value: string) {
    setLoading(true);
    setSeverity(value as IncidentSeverity | "");
  }

  function handleCategoryChange(value: string) {
    setLoading(true);
    setCategory(value as IncidentCategory | "");
  }

  function handleClearFilters() {
    setLoading(true);
    setStatus("");
    setSeverity("");
    setCategory("");
  }

  const openIncidents = incidents.filter(
    (incident) => incident.status === "open",
  ).length;

  const criticalIncidents = incidents.filter(
    (incident) =>
      incident.severity === "critical" &&
      incident.status === "open",
  ).length;

  const warningIncidents = incidents.filter(
    (incident) =>
      incident.severity === "warning" &&
      incident.status === "open",
  ).length;

  return (
    <div className="min-h-full bg-zinc-100 p-5 text-zinc-950 md:p-8">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8">
          <p className="text-sm font-medium text-zinc-500">
            Operacion
          </p>

          <h3 className="mt-1 text-3xl font-bold tracking-tight">
            Operaciones
          </h3>

          <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-500">
            Supervisa incidentes, errores y salud operacional
            del AI Order Agent.
          </p>
        </div>

        <section
          className="mb-6 grid gap-3 sm:grid-cols-3"
          aria-label="Resumen de incidentes"
        >
          <MetricCard
            label="Abiertos"
            value={openIncidents}
            loading={loading}
          />

          <MetricCard
            label="Criticos"
            value={criticalIncidents}
            loading={loading}
          />

          <MetricCard
            label="Advertencias"
            value={warningIncidents}
            loading={loading}
          />
        </section>

        <section
          className="mb-6 rounded-2xl border border-zinc-200 bg-white p-4"
          aria-label="Filtros de incidentes"
        >
          <div className="grid gap-4 md:grid-cols-4">
            <FilterSelect
              label="Estado"
              value={status}
              onChange={handleStatusChange}
              options={[
                ["open", "Abierto"],
                ["resolved", "Resuelto"],
              ]}
            />

            <FilterSelect
              label="Severidad"
              value={severity}
              onChange={handleSeverityChange}
              options={[
                ["info", "Informacion"],
                ["warning", "Advertencia"],
                ["critical", "Critico"],
              ]}
            />

            <FilterSelect
              label="Categoria"
              value={category}
              onChange={handleCategoryChange}
              options={[
                ["provider", "Proveedor"],
                ["payment", "Pago"],
                ["order", "Pedido"],
                ["webhook", "Webhook"],
                [
                  "reconciliation",
                  "Reconciliacion",
                ],
                ["system", "Sistema"],
              ]}
            />

            <div className="flex items-end">
              <button
                type="button"
                onClick={handleClearFilters}
                className="min-h-11 w-full rounded-xl border border-zinc-200 px-4 text-sm font-medium text-zinc-700 transition hover:bg-zinc-50 focus:outline-none focus:ring-2 focus:ring-zinc-400"
              >
                Limpiar filtros
              </button>
            </div>
          </div>
        </section>

        <IncidentsTable
          incidents={incidents}
          loading={loading}
          error={error}
          onOpenIncident={handleOpenIncident}
        />
      </div>

      <IncidentDetailDrawer
        incident={selectedIncident}
        loading={detailLoading}
        error={detailError}
        onClose={handleCloseIncident}
      />
    </div>
  );
}

type MetricCardProps = {
  label: string;
  value: number;
  loading: boolean;
};

function MetricCard({
  label,
  value,
  loading,
}: MetricCardProps) {
  return (
    <div className="rounded-2xl border border-zinc-200 bg-white p-5">
      <p className="text-xs font-medium uppercase tracking-wide text-zinc-400">
        {label}
      </p>

      <p className="mt-2 text-3xl font-bold tracking-tight">
        {loading ? "-" : value}
      </p>
    </div>
  );
}

type FilterSelectProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: Array<[string, string]>;
};

function FilterSelect({
  label,
  value,
  onChange,
  options,
}: FilterSelectProps) {
  return (
    <label className="block">
      <span className="mb-2 block text-xs font-medium text-zinc-500">
        {label}
      </span>

      <select
        value={value}
        onChange={(event) =>
          onChange(event.target.value)
        }
        className="min-h-11 w-full rounded-xl border border-zinc-200 bg-white px-3 text-sm text-zinc-800 focus:outline-none focus:ring-2 focus:ring-zinc-400"
      >
        <option value="">Todos</option>

        {options.map(([optionValue, optionLabel]) => (
          <option
            key={optionValue}
            value={optionValue}
          >
            {optionLabel}
          </option>
        ))}
      </select>
    </label>
  );
}