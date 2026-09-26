import type { CustomerDetail } from "@/lib/api";

interface CustomerDetailDrawerProps {
  customer: CustomerDetail | null;
  loading: boolean;
  error: string | null;
  onClose: () => void;
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

function formatContact(
  value: string | null,
): string {
  return value?.trim() || "No registrado";
}

function formatOrderTotal(
  value: number,
): string {
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

function formatChannel(channel: string): string {
  const normalized = channel
    .trim()
    .toLowerCase();

  if (normalized === "whatsapp") {
    return "WhatsApp";
  }

  if (normalized === "webchat") {
    return "Web chat";
  }

  return channel;
}

export function CustomerDetailDrawer({
  customer,
  loading,
  error,
  onClose,
}: CustomerDetailDrawerProps) {
  const open =
    customer !== null ||
    loading ||
    error !== null;

  if (!open) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 z-50"
      role="dialog"
      aria-modal="true"
      aria-labelledby="customer-detail-title"
    >
      <button
        type="button"
        className="absolute inset-0 bg-black/30"
        onClick={onClose}
        aria-label="Cerrar detalle del cliente"
      />

      <aside className="absolute inset-y-0 right-0 flex w-full max-w-xl flex-col bg-white shadow-xl">
        <div className="flex items-start justify-between gap-4 border-b border-zinc-200 px-5 py-5 md:px-6">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
              Cliente
            </p>

            <h4
              id="customer-detail-title"
              className="mt-1 text-xl font-bold tracking-tight text-zinc-950"
            >
              {customer
                ? customer.name
                : "Detalle del cliente"}
            </h4>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-zinc-300 px-3 py-2 text-sm font-medium text-zinc-700 transition hover:bg-zinc-100 focus:outline-none focus:ring-2 focus:ring-zinc-400 focus:ring-offset-2"
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
              <div className="mx-auto h-7 w-7 animate-spin rounded-full border-2 border-zinc-300 border-t-zinc-950" />

              <p className="mt-3 text-sm text-zinc-500">
                Cargando detalle del cliente...
              </p>
            </div>
          ) : error ? (
            <div
              className="rounded-xl border border-zinc-200 bg-zinc-50 p-5"
              role="alert"
            >
              <p className="text-sm font-semibold text-zinc-950">
                No fue posible cargar el cliente
              </p>

              <p className="mt-2 text-sm leading-6 text-zinc-500">
                {error}
              </p>
            </div>
          ) : customer ? (
            <div className="space-y-6">
              <section
                className="rounded-xl border border-zinc-200 p-5"
                aria-labelledby="customer-information-title"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h5
                      id="customer-information-title"
                      className="text-sm font-semibold text-zinc-950"
                    >
                      Informacion
                    </h5>

                    <p className="mt-1 text-xs text-zinc-500">
                      Datos registrados para este cliente.
                    </p>
                  </div>

                  <span
                    className={
                      customer.active
                        ? "rounded-full bg-zinc-900 px-2.5 py-1 text-xs font-medium text-white"
                        : "rounded-full bg-zinc-100 px-2.5 py-1 text-xs font-medium text-zinc-600"
                    }
                  >
                    {customer.active
                      ? "Activo"
                      : "Inactivo"}
                  </span>
                </div>

                <dl className="mt-5 grid gap-4 sm:grid-cols-2">
                  <div>
                    <dt className="text-xs font-medium text-zinc-500">
                      ID
                    </dt>

                    <dd className="mt-1 text-sm font-medium text-zinc-900">
                      #{customer.id}
                    </dd>
                  </div>

                  <div>
                    <dt className="text-xs font-medium text-zinc-500">
                      Telefono
                    </dt>

                    <dd className="mt-1 break-words text-sm text-zinc-900">
                      {formatContact(customer.phone)}
                    </dd>
                  </div>

                  <div>
                    <dt className="text-xs font-medium text-zinc-500">
                      Correo
                    </dt>

                    <dd className="mt-1 break-words text-sm text-zinc-900">
                      {formatContact(customer.email)}
                    </dd>
                  </div>

                  <div>
                    <dt className="text-xs font-medium text-zinc-500">
                      Creado
                    </dt>

                    <dd className="mt-1 text-sm text-zinc-900">
                      {formatDate(customer.created_at)}
                    </dd>
                  </div>

                  <div>
                    <dt className="text-xs font-medium text-zinc-500">
                      Ultima actualizacion
                    </dt>

                    <dd className="mt-1 text-sm text-zinc-900">
                      {formatDate(customer.updated_at)}
                    </dd>
                  </div>
                </dl>
              </section>

              <section
                className="rounded-xl border border-zinc-200 p-5"
                aria-labelledby="customer-activity-title"
              >
                <h5
                  id="customer-activity-title"
                  className="text-sm font-semibold text-zinc-950"
                >
                  Actividad de pedidos
                </h5>

                <p className="mt-1 text-xs text-zinc-500">
                  Resumen de pedidos vinculados al cliente.
                </p>

                <dl className="mt-5 grid grid-cols-2 gap-4">
                  <div className="rounded-lg bg-zinc-50 p-4">
                    <dt className="text-xs font-medium text-zinc-500">
                      Pedidos
                    </dt>

                    <dd className="mt-2 text-2xl font-bold tracking-tight text-zinc-950">
                      {customer.order_count.toLocaleString()}
                    </dd>
                  </div>

                  <div className="rounded-lg bg-zinc-50 p-4">
                    <dt className="text-xs font-medium text-zinc-500">
                      Total registrado
                    </dt>

                    <dd className="mt-2 text-2xl font-bold tracking-tight text-zinc-950">
                      {formatOrderTotal(
                        customer.order_total,
                      )}
                    </dd>
                  </div>
                </dl>

                <p className="mt-3 text-xs leading-5 text-zinc-500">
                  El total se muestra sin simbolo de moneda
                  porque el resumen actual de clientes no
                  expone una moneda asociada.
                </p>
              </section>

              <section
                className="rounded-xl border border-zinc-200 p-5"
                aria-labelledby="customer-identities-title"
              >
                <h5
                  id="customer-identities-title"
                  className="text-sm font-semibold text-zinc-950"
                >
                  Identidades y canales
                </h5>

                <p className="mt-1 text-xs text-zinc-500">
                  Identificadores externos asociados al cliente.
                </p>

                {customer.identities.length === 0 ? (
                  <div
                    className="mt-5 rounded-lg bg-zinc-50 p-4"
                    role="status"
                  >
                    <p className="text-sm text-zinc-500">
                      Este cliente no tiene identidades externas
                      registradas.
                    </p>
                  </div>
                ) : (
                  <ul className="mt-5 divide-y divide-zinc-200">
                    {customer.identities.map(
                      (identity) => (
                        <li
                          key={identity.id}
                          className="py-4 first:pt-0 last:pb-0"
                        >
                          <div className="flex flex-wrap items-start justify-between gap-3">
                            <div className="min-w-0">
                              <p className="text-sm font-semibold text-zinc-950">
                                {formatChannel(
                                  identity.channel,
                                )}
                              </p>

                              <p className="mt-1 break-all text-sm text-zinc-600">
                                {identity.external_id}
                              </p>
                            </div>

                            <span className="rounded-full bg-zinc-100 px-2.5 py-1 text-xs font-medium text-zinc-600">
                              #{identity.id}
                            </span>
                          </div>

                          <p className="mt-2 text-xs text-zinc-500">
                            Registrada{" "}
                            {formatDate(
                              identity.created_at,
                            )}
                          </p>
                        </li>
                      ),
                    )}
                  </ul>
                )}
              </section>
            </div>
          ) : null}
        </div>
      </aside>
    </div>
  );
}