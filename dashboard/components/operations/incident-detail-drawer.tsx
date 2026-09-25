"use client";

import { useEffect, useRef } from "react";

import { DashboardState } from "@/components/ui/dashboard-state";
import type { OperationalIncident } from "@/lib/operational/incidents";

type IncidentDetailDrawerProps = {
  incident: OperationalIncident | null;
  loading: boolean;
  error: string | null;
  onClose: () => void;
};

export function IncidentDetailDrawer({
  incident,
  loading,
  error,
  onClose,
}: IncidentDetailDrawerProps) {
  const closeButtonRef =
    useRef<HTMLButtonElement | null>(null);

  const visible = loading || Boolean(error) || Boolean(incident);

  useEffect(() => {
    if (!visible) {
      return;
    }

    const previousOverflow = document.body.style.overflow;

    document.body.style.overflow = "hidden";

    window.requestAnimationFrame(() => {
      closeButtonRef.current?.focus();
    });

    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [visible]);

  if (!visible) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50">
      <button
        type="button"
        className="absolute inset-0 bg-black/30"
        onClick={onClose}
        aria-label="Cerrar detalle del incidente"
      />

      <aside
        role="dialog"
        aria-modal="true"
        aria-labelledby="incident-detail-title"
        className="absolute inset-x-0 bottom-0 max-h-[90vh] overflow-y-auto rounded-t-3xl bg-white shadow-2xl md:inset-y-0 md:left-auto md:right-0 md:max-h-none md:w-full md:max-w-xl md:rounded-none"
      >
        <div className="sticky top-0 z-10 flex items-start justify-between gap-4 border-b border-zinc-100 bg-white px-5 py-5 md:px-6">
          <div className="min-w-0">
            <p className="text-xs font-medium uppercase tracking-wide text-zinc-400">
              Operaciones
            </p>

            <h3
              id="incident-detail-title"
              className="mt-1 truncate text-xl font-bold text-zinc-950"
            >
              {incident?.title ?? "Detalle del incidente"}
            </h3>
          </div>

          <button
            ref={closeButtonRef}
            type="button"
            onClick={onClose}
            className="min-h-11 min-w-11 rounded-xl border border-zinc-200 px-3 text-sm font-medium text-zinc-700 transition hover:bg-zinc-50 focus:outline-none focus:ring-2 focus:ring-zinc-400"
          >
            Cerrar
          </button>
        </div>

        {loading && (
          <DashboardState
            variant="loading"
            title="Cargando incidente..."
          />
        )}

        {!loading && error && (
          <DashboardState
            variant="error"
            title="No fue posible cargar el incidente."
            description={formatOperationalError(error)}
          />
        )}

        {!loading && !error && incident && (
          <div className="space-y-6 p-5 md:p-6">
            <DetailSection title="Estado">
              <DetailGrid>
                <DetailItem
                  label="Severidad"
                  value={incident.severity}
                />

                <DetailItem
                  label="Estado"
                  value={incident.status}
                />

                <DetailItem
                  label="Categoria"
                  value={incident.category}
                />

                <DetailItem
                  label="Ocurrencias"
                  value={String(
                    incident.occurrence_count,
                  )}
                />
              </DetailGrid>
            </DetailSection>

            <DetailSection title="Descripcion">
              <p className="whitespace-pre-wrap break-words text-sm leading-6 text-zinc-700">
                {incident.description}
              </p>
            </DetailSection>

            <DetailSection title="Origen">
              <DetailGrid>
                <DetailItem
                  label="Proveedor"
                  value={incident.provider ?? "-"}
                />

                <DetailItem
                  label="Operacion"
                  value={incident.operation ?? "-"}
                />

                <DetailItem
                  label="Primera deteccion"
                  value={formatDateTime(
                    incident.first_seen_at,
                  )}
                />

                <DetailItem
                  label="Ultima deteccion"
                  value={formatDateTime(
                    incident.last_seen_at,
                  )}
                />

                <DetailItem
                  label="Resuelto"
                  value={
                    incident.resolved_at
                      ? formatDateTime(
                          incident.resolved_at,
                        )
                      : "-"
                  }
                />
              </DetailGrid>
            </DetailSection>

            <DetailSection title="Contexto">
              {Object.keys(incident.context).length === 0 ? (
                <p className="text-sm text-zinc-400">
                  Sin contexto adicional.
                </p>
              ) : (
                <dl className="space-y-3">
                  {Object.entries(incident.context).map(
                    ([key, value]) => (
                      <div
                        key={key}
                        className="rounded-xl bg-zinc-50 p-4"
                      >
                        <dt className="break-words text-xs font-medium text-zinc-400">
                          {key}
                        </dt>

                        <dd className="mt-1 break-words text-sm text-zinc-700">
                          {value}
                        </dd>
                      </div>
                    ),
                  )}
                </dl>
              )}
            </DetailSection>

            <DetailSection title="Identificacion">
              <dl className="space-y-3 text-xs">
                <DetailCode
                  label="Incident ID"
                  value={incident.id}
                />

                <DetailCode
                  label="Fingerprint"
                  value={incident.fingerprint}
                />
              </dl>
            </DetailSection>
          </div>
        )}
      </aside>
    </div>
  );
}

function DetailSection({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section>
      <h4 className="mb-3 text-sm font-semibold text-zinc-900">
        {title}
      </h4>

      {children}
    </section>
  );
}

function DetailGrid({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <dl className="grid gap-4 sm:grid-cols-2">
      {children}
    </dl>
  );
}

function DetailItem({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div>
      <dt className="text-xs font-medium text-zinc-400">
        {label}
      </dt>

      <dd className="mt-1 break-words text-sm text-zinc-700">
        {value}
      </dd>
    </div>
  );
}

function DetailCode({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div>
      <dt className="font-medium text-zinc-400">
        {label}
      </dt>

      <dd className="mt-1 break-all rounded-lg bg-zinc-50 p-3 font-mono text-zinc-600">
        {value}
      </dd>
    </div>
  );
}

function formatDateTime(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("es-CO", {
    dateStyle: "medium",
    timeStyle: "medium",
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