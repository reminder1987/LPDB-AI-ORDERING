"use client";

import {
  FormEvent,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  getIntegration,
  getIntegrations,
  type Integration,
} from "@/lib/api";

import { IntegrationDetailDrawer } from "./integration-detail-drawer";
import { IntegrationMetrics } from "./integration-metrics";
import { IntegrationsTable } from "./integrations-table";

type ActiveFilter =
  | "all"
  | "active"
  | "inactive";

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
    return "No tienes permisos para consultar estas integraciones.";
  }

  return error.message;
}

export function IntegrationDashboard() {
  const [integrations, setIntegrations] = useState<
    Integration[]
  >([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(
    null,
  );

  const [providerInput, setProviderInput] =
    useState("");
  const [providerFilter, setProviderFilter] =
    useState("");
  const [
    integrationTypeInput,
    setIntegrationTypeInput,
  ] = useState("");
  const [
    integrationTypeFilter,
    setIntegrationTypeFilter,
  ] = useState("");
  const [activeFilter, setActiveFilter] =
    useState<ActiveFilter>("all");

  const [
    selectedIntegration,
    setSelectedIntegration,
  ] = useState<Integration | null>(null);
  const [
    detailLoading,
    setDetailLoading,
  ] = useState(false);
  const [detailError, setDetailError] = useState<
    string | null
  >(null);

  useEffect(() => {
    let active = true;

    async function loadIntegrations() {
      setLoading(true);
      setError(null);

      try {
        const result = await getIntegrations({
          provider:
            providerFilter || undefined,
          integration_type:
            integrationTypeFilter || undefined,
          active:
            activeFilter === "all"
              ? undefined
              : activeFilter === "active",
        });

        if (!active) {
          return;
        }

        setIntegrations(result);
      } catch (loadError) {
        if (!active) {
          return;
        }

        setIntegrations([]);
        setError(
          getErrorMessage(loadError),
        );
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadIntegrations();

    return () => {
      active = false;
    };
  }, [
    providerFilter,
    integrationTypeFilter,
    activeFilter,
  ]);

  useEffect(() => {
    function handleEscape(
      event: KeyboardEvent,
    ) {
      if (event.key === "Escape") {
        setSelectedIntegration(null);
        setDetailError(null);
        setDetailLoading(false);
      }
    }

    window.addEventListener(
      "keydown",
      handleEscape,
    );

    return () => {
      window.removeEventListener(
        "keydown",
        handleEscape,
      );
    };
  }, []);

  const metrics = useMemo(() => {
    const active = integrations.filter(
      (integration) => integration.active,
    ).length;

    const credentialsConfigured =
      integrations.filter(
        (integration) =>
          integration.credentials_configured,
      ).length;

    const providers = new Set(
      integrations
        .map((integration) =>
          integration.provider
            .trim()
            .toLowerCase(),
        )
        .filter(Boolean),
    ).size;

    return {
      total: integrations.length,
      active,
      credentialsConfigured,
      providers,
    };
  }, [integrations]);

  async function openIntegration(
    integrationId: number,
  ) {
    setSelectedIntegration(null);
    setDetailError(null);
    setDetailLoading(true);

    try {
      const integration =
        await getIntegration(integrationId);

      setSelectedIntegration(integration);
    } catch (loadError) {
      setDetailError(
        getErrorMessage(loadError),
      );
    } finally {
      setDetailLoading(false);
    }
  }

  function closeDetail() {
    setSelectedIntegration(null);
    setDetailError(null);
    setDetailLoading(false);
  }

  function handleFiltersSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setProviderFilter(
      providerInput.trim(),
    );
    setIntegrationTypeFilter(
      integrationTypeInput.trim(),
    );
  }

  function clearFilters() {
    setProviderInput("");
    setProviderFilter("");
    setIntegrationTypeInput("");
    setIntegrationTypeFilter("");
    setActiveFilter("all");
  }

  const filtersApplied =
    Boolean(providerFilter) ||
    Boolean(integrationTypeFilter) ||
    activeFilter !== "all";

  return (
    <div className="space-y-6">
      <header>
        <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
          Operacion
        </p>

        <div className="mt-1 flex flex-wrap items-end justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-zinc-950">
              Integraciones
            </h2>

            <p className="mt-2 max-w-3xl text-sm leading-6 text-zinc-500">
              Supervisa las conexiones externas
              configuradas para el tenant actual
              sin exponer credenciales ni secretos.
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
      </header>

      <IntegrationMetrics
        total={metrics.total}
        active={metrics.active}
        credentialsConfigured={
          metrics.credentialsConfigured
        }
        providers={metrics.providers}
      />

      <section
        className="rounded-xl border border-zinc-200 bg-white p-4 md:p-5"
        aria-labelledby="integration-filters-title"
      >
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h3
              id="integration-filters-title"
              className="text-sm font-semibold text-zinc-950"
            >
              Filtros
            </h3>

            <p className="mt-1 text-xs text-zinc-500">
              Busca por proveedor, tipo de
              integracion o estado.
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
              Tipo de integracion
            </span>

            <input
              type="text"
              value={integrationTypeInput}
              onChange={(event) =>
                setIntegrationTypeInput(
                  event.target.value,
                )
              }
              placeholder="Ej. whatsapp"
              className="mt-1.5 w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm text-zinc-950 outline-none transition placeholder:text-zinc-400 focus:border-zinc-500 focus:ring-2 focus:ring-zinc-200"
            />
          </label>

          <label className="block">
            <span className="text-xs font-medium text-zinc-600">
              Estado
            </span>

            <select
              value={activeFilter}
              onChange={(event) =>
                setActiveFilter(
                  event.target
                    .value as ActiveFilter,
                )
              }
              className="mt-1.5 w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm text-zinc-950 outline-none transition focus:border-zinc-500 focus:ring-2 focus:ring-zinc-200"
            >
              <option value="all">
                Todas
              </option>
              <option value="active">
                Activas
              </option>
              <option value="inactive">
                Inactivas
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

      <IntegrationsTable
        integrations={integrations}
        loading={loading}
        error={error}
        onOpenIntegration={
          openIntegration
        }
      />

      <IntegrationDetailDrawer
        integration={selectedIntegration}
        loading={detailLoading}
        error={detailError}
        onClose={closeDetail}
      />
    </div>
  );
}