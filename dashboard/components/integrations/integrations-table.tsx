import type { Integration } from "@/lib/api";

interface IntegrationsTableProps {
  integrations: Integration[];
  loading: boolean;
  error: string | null;
  onOpenIntegration: (integrationId: number) => void;
}

function formatValue(
  value: string | null,
): string {
  return value?.trim() || "No registrado";
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

export function IntegrationsTable({
  integrations,
  loading,
  error,
  onOpenIntegration,
}: IntegrationsTableProps) {
  return (
    <section
      className="mt-6 overflow-hidden rounded-xl border border-zinc-200 bg-white"
      aria-labelledby="integrations-table-title"
    >
      <div className="border-b border-zinc-200 px-4 py-4 md:px-5">
        <h4
          id="integrations-table-title"
          className="text-sm font-semibold text-zinc-950"
        >
          Integraciones configuradas
        </h4>

        <p className="mt-1 text-xs text-zinc-500">
          Proveedores y conexiones asociadas al tenant actual.
        </p>
      </div>

      {loading ? (
        <div
          className="p-8 text-center"
          role="status"
        >
          <div className="mx-auto h-6 w-6 animate-spin rounded-full border-2 border-zinc-300 border-t-zinc-950" />

          <p className="mt-3 text-sm text-zinc-500">
            Cargando integraciones...
          </p>
        </div>
      ) : error ? (
        <div
          className="p-8 text-center"
          role="alert"
        >
          <p className="text-sm font-medium text-zinc-900">
            No fue posible mostrar las integraciones
          </p>

          <p className="mt-2 text-sm text-zinc-500">
            {error}
          </p>
        </div>
      ) : integrations.length === 0 ? (
        <div
          className="p-8 text-center"
          role="status"
        >
          <p className="text-sm font-medium text-zinc-900">
            No hay integraciones para mostrar
          </p>

          <p className="mt-2 text-sm text-zinc-500">
            No encontramos integraciones que coincidan con
            los filtros actuales.
          </p>
        </div>
      ) : (
        <>
          <div className="divide-y divide-zinc-200 md:hidden">
            {integrations.map((integration) => (
              <button
                key={integration.id}
                type="button"
                onClick={() =>
                  onOpenIntegration(integration.id)
                }
                className="block w-full p-4 text-left transition hover:bg-zinc-50 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-zinc-500"
                aria-label={`Ver integracion ${formatProvider(
                  integration.provider,
                )}`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-zinc-950">
                      {formatProvider(
                        integration.provider,
                      )}
                    </p>

                    <p className="mt-1 truncate text-xs text-zinc-500">
                      {formatIntegrationType(
                        integration.integration_type,
                      )}
                    </p>

                    <p className="mt-1 truncate text-xs text-zinc-500">
                      {formatValue(
                        integration.external_id,
                      )}
                    </p>
                  </div>

                  <span
                    className={
                      integration.active
                        ? "shrink-0 rounded-full bg-zinc-900 px-2.5 py-1 text-xs font-medium text-white"
                        : "shrink-0 rounded-full bg-zinc-100 px-2.5 py-1 text-xs font-medium text-zinc-600"
                    }
                  >
                    {integration.active
                      ? "Activa"
                      : "Inactiva"}
                  </span>
                </div>

                <div className="mt-4">
                  <p className="text-xs text-zinc-500">
                    Credenciales
                  </p>

                  <p className="mt-1 text-sm font-semibold text-zinc-900">
                    {integration.credentials_configured
                      ? "Configuradas"
                      : "No configuradas"}
                  </p>
                </div>
              </button>
            ))}
          </div>

          <div className="hidden overflow-x-auto md:block">
            <table className="min-w-full divide-y divide-zinc-200">
              <thead className="bg-zinc-50">
                <tr>
                  <th
                    scope="col"
                    className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500"
                  >
                    Proveedor
                  </th>

                  <th
                    scope="col"
                    className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500"
                  >
                    Tipo
                  </th>

                  <th
                    scope="col"
                    className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500"
                  >
                    Identificador externo
                  </th>

                  <th
                    scope="col"
                    className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500"
                  >
                    Estado
                  </th>

                  <th
                    scope="col"
                    className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500"
                  >
                    Credenciales
                  </th>

                  <th
                    scope="col"
                    className="px-5 py-3 text-right text-xs font-semibold uppercase tracking-wide text-zinc-500"
                  >
                    Detalle
                  </th>
                </tr>
              </thead>

              <tbody className="divide-y divide-zinc-200 bg-white">
                {integrations.map((integration) => (
                  <tr
                    key={integration.id}
                    className="transition hover:bg-zinc-50"
                  >
                    <td className="whitespace-nowrap px-5 py-4">
                      <p className="text-sm font-semibold text-zinc-950">
                        {formatProvider(
                          integration.provider,
                        )}
                      </p>

                      <p className="mt-1 text-xs text-zinc-500">
                        ID #{integration.id}
                      </p>
                    </td>

                    <td className="whitespace-nowrap px-5 py-4 text-sm text-zinc-700">
                      {formatIntegrationType(
                        integration.integration_type,
                      )}
                    </td>

                    <td className="max-w-xs px-5 py-4">
                      <p className="truncate text-sm text-zinc-700">
                        {formatValue(
                          integration.external_id,
                        )}
                      </p>
                    </td>

                    <td className="whitespace-nowrap px-5 py-4">
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
                    </td>

                    <td className="whitespace-nowrap px-5 py-4">
                      <span
                        className={
                          integration.credentials_configured
                            ? "inline-flex rounded-full bg-zinc-100 px-2.5 py-1 text-xs font-medium text-zinc-700"
                            : "inline-flex rounded-full border border-zinc-300 px-2.5 py-1 text-xs font-medium text-zinc-600"
                        }
                      >
                        {integration.credentials_configured
                          ? "Configuradas"
                          : "No configuradas"}
                      </span>
                    </td>

                    <td className="whitespace-nowrap px-5 py-4 text-right">
                      <button
                        type="button"
                        onClick={() =>
                          onOpenIntegration(
                            integration.id,
                          )
                        }
                        className="rounded-lg border border-zinc-300 px-3 py-2 text-xs font-medium text-zinc-700 transition hover:bg-zinc-100 focus:outline-none focus:ring-2 focus:ring-zinc-400 focus:ring-offset-2"
                        aria-label={`Ver detalle de integracion ${formatProvider(
                          integration.provider,
                        )}`}
                      >
                        Ver detalle
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </section>
  );
}