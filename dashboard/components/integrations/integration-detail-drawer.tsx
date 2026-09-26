import type { Integration } from "@/lib/api";

interface IntegrationDetailDrawerProps {
  integration: Integration | null;
  loading: boolean;
  error: string | null;
  onClose: () => void;
}

function formatProvider(
  provider: string,
): string {
  const normalized = provider.trim().toLowerCase();

  if (normalized === "meta") {
    return "Meta";
  }

  if (normalized === "toast") {
    return "Toast";
  }

  return provider.trim() || "Desconocido";
}

function formatIntegrationType(
  integrationType: string,
): string {
  const normalized = integrationType
    .trim()
    .toLowerCase();

  if (normalized === "whatsapp") {
    return "WhatsApp";
  }

  if (normalized === "pos") {
    return "POS";
  }

  return integrationType.trim() || "Sin tipo";
}

function formatDate(
  value: string,
): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("es-CO", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function formatConfigurationValue(
  value: unknown,
): string {
  if (value === null || value === undefined) {
    return "No configurado";
  }

  if (typeof value === "boolean") {
    return value ? "Si" : "No";
  }

  if (
    typeof value === "string" ||
    typeof value === "number"
  ) {
    return String(value);
  }

  try {
    return JSON.stringify(value);
  } catch {
    return "Valor no disponible";
  }
}

export function IntegrationDetailDrawer({
  integration,
  loading,
  error,
  onClose,
}: IntegrationDetailDrawerProps) {
  const isOpen =
    loading ||
    Boolean(error) ||
    Boolean(integration);

  if (!isOpen) {
    return null;
  }

  const configurationEntries = integration
    ? Object.entries(integration.configuration)
    : [];

  return (
    <div
      className="fixed inset-0 z-50"
      role="presentation"
    >
      <button
        type="button"
        className="absolute inset-0 bg-black/30"
        onClick={onClose}
        aria-label="Cerrar detalle de integracion"
      />

      <aside
        className="absolute inset-y-0 right-0 flex w-full max-w-xl flex-col bg-white shadow-xl"
        role="dialog"
        aria-modal="true"
        aria-labelledby="integration-detail-title"
      >
        <div className="flex items-start justify-between gap-4 border-b border-zinc-200 px-5 py-5 md:px-6">
          <div className="min-w-0">
            <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
              Integracion
            </p>

            <h4
              id="integration-detail-title"
              className="mt-1 truncate text-xl font-bold text-zinc-950"
            >
              {integration
                ? formatProvider(
                    integration.provider,
                  )
                : "Detalle de integracion"}
            </h4>

            {integration && (
              <p className="mt-1 text-sm text-zinc-500">
                {formatIntegrationType(
                  integration.integration_type,
                )}
              </p>
            )}
          </div>

          <button
            type="button"
            onClick={onClose}
            className="shrink-0 rounded-lg border border-zinc-300 px-3 py-2 text-sm font-medium text-zinc-700 transition hover:bg-zinc-100 focus:outline-none focus:ring-2 focus:ring-zinc-400 focus:ring-offset-2"
          >
            Cerrar
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-5 md:p-6">
          {loading ? (
            <div
              className="py-12 text-center"
              role="status"
            >
              <div className="mx-auto h-6 w-6 animate-spin rounded-full border-2 border-zinc-300 border-t-zinc-950" />

              <p className="mt-3 text-sm text-zinc-500">
                Cargando detalle...
              </p>
            </div>
          ) : error ? (
            <div
              className="rounded-xl border border-zinc-200 bg-zinc-50 p-5"
              role="alert"
            >
              <p className="text-sm font-semibold text-zinc-950">
                No fue posible cargar la integracion
              </p>

              <p className="mt-2 text-sm leading-6 text-zinc-500">
                {error}
              </p>
            </div>
          ) : integration ? (
            <div className="space-y-6">
              <section
                className="rounded-xl border border-zinc-200 p-4"
                aria-labelledby="integration-general-title"
              >
                <h5
                  id="integration-general-title"
                  className="text-sm font-semibold text-zinc-950"
                >
                  Informacion general
                </h5>

                <dl className="mt-4 grid gap-4 sm:grid-cols-2">
                  <div>
                    <dt className="text-xs font-medium text-zinc-500">
                      ID interno
                    </dt>

                    <dd className="mt-1 text-sm font-medium text-zinc-900">
                      #{integration.id}
                    </dd>
                  </div>

                  <div>
                    <dt className="text-xs font-medium text-zinc-500">
                      Estado
                    </dt>

                    <dd className="mt-1">
                      <span
                        className={
                          integration.active
                            ? "inline-flex rounded-full bg-zinc-900 px-2.5 py-1 text-xs font-medium text-white"
                            : "inline-flex rounded-full bg-zinc-100 px-2.5 py-1 text-xs font-medium text-zinc-600"
                        }
                      >
                        {integration.active
                          ? "Activa"
                          : "Inactiva"}
                      </span>
                    </dd>
                  </div>

                  <div>
                    <dt className="text-xs font-medium text-zinc-500">
                      Proveedor
                    </dt>

                    <dd className="mt-1 text-sm font-medium text-zinc-900">
                      {formatProvider(
                        integration.provider,
                      )}
                    </dd>
                  </div>

                  <div>
                    <dt className="text-xs font-medium text-zinc-500">
                      Tipo
                    </dt>

                    <dd className="mt-1 text-sm font-medium text-zinc-900">
                      {formatIntegrationType(
                        integration.integration_type,
                      )}
                    </dd>
                  </div>

                  <div className="sm:col-span-2">
                    <dt className="text-xs font-medium text-zinc-500">
                      Identificador externo
                    </dt>

                    <dd className="mt-1 break-all text-sm font-medium text-zinc-900">
                      {integration.external_id?.trim() ||
                        "No registrado"}
                    </dd>
                  </div>
                </dl>
              </section>

              <section
                className="rounded-xl border border-zinc-200 p-4"
                aria-labelledby="integration-credentials-title"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h5
                      id="integration-credentials-title"
                      className="text-sm font-semibold text-zinc-950"
                    >
                      Credenciales
                    </h5>

                    <p className="mt-1 text-xs leading-5 text-zinc-500">
                      Solo se muestran los nombres de las
                      credenciales configuradas.
                    </p>
                  </div>

                  <span
                    className={
                      integration.credentials_configured
                        ? "rounded-full bg-zinc-100 px-2.5 py-1 text-xs font-medium text-zinc-700"
                        : "rounded-full border border-zinc-300 px-2.5 py-1 text-xs font-medium text-zinc-600"
                    }
                  >
                    {integration.credentials_configured
                      ? "Configuradas"
                      : "No configuradas"}
                  </span>
                </div>

                {integration.credential_names.length > 0 ? (
                  <ul className="mt-4 space-y-2">
                    {integration.credential_names.map(
                      (credentialName) => (
                        <li
                          key={credentialName}
                          className="rounded-lg bg-zinc-50 px-3 py-2 font-mono text-xs text-zinc-700"
                        >
                          {credentialName}
                        </li>
                      ),
                    )}
                  </ul>
                ) : (
                  <p className="mt-4 text-sm text-zinc-500">
                    Esta integracion no registra credenciales.
                  </p>
                )}
              </section>

              <section
                className="rounded-xl border border-zinc-200 p-4"
                aria-labelledby="integration-configuration-title"
              >
                <h5
                  id="integration-configuration-title"
                  className="text-sm font-semibold text-zinc-950"
                >
                  Configuracion operacional
                </h5>

                <p className="mt-1 text-xs leading-5 text-zinc-500">
                  Parametros no secretos asociados a la
                  integracion.
                </p>

                {configurationEntries.length > 0 ? (
                  <dl className="mt-4 divide-y divide-zinc-200">
                    {configurationEntries.map(
                      ([key, value]) => (
                        <div
                          key={key}
                          className="py-3 first:pt-0 last:pb-0"
                        >
                          <dt className="break-all font-mono text-xs font-medium text-zinc-500">
                            {key}
                          </dt>

                          <dd className="mt-1 break-all text-sm text-zinc-900">
                            {formatConfigurationValue(
                              value,
                            )}
                          </dd>
                        </div>
                      ),
                    )}
                  </dl>
                ) : (
                  <p className="mt-4 text-sm text-zinc-500">
                    No hay parametros adicionales registrados.
                  </p>
                )}
              </section>

              <section
                className="rounded-xl border border-zinc-200 p-4"
                aria-labelledby="integration-audit-title"
              >
                <h5
                  id="integration-audit-title"
                  className="text-sm font-semibold text-zinc-950"
                >
                  Registro
                </h5>

                <dl className="mt-4 grid gap-4 sm:grid-cols-2">
                  <div>
                    <dt className="text-xs font-medium text-zinc-500">
                      Creada
                    </dt>

                    <dd className="mt-1 text-sm text-zinc-900">
                      {formatDate(
                        integration.created_at,
                      )}
                    </dd>
                  </div>

                  <div>
                    <dt className="text-xs font-medium text-zinc-500">
                      Ultima actualizacion
                    </dt>

                    <dd className="mt-1 text-sm text-zinc-900">
                      {formatDate(
                        integration.updated_at,
                      )}
                    </dd>
                  </div>
                </dl>
              </section>

              <div
                className="rounded-xl border border-zinc-200 bg-zinc-50 p-4"
                role="note"
              >
                <p className="text-sm font-medium text-zinc-800">
                  Vista de solo lectura
                </p>

                <p className="mt-1 text-xs leading-5 text-zinc-500">
                  Este modulo no permite modificar
                  configuraciones, credenciales ni el estado
                  de la integracion.
                </p>
              </div>
            </div>
          ) : null}
        </div>
      </aside>
    </div>
  );
}