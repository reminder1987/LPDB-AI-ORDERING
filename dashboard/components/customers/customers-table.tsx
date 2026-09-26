import type { Customer } from "@/lib/api";

interface CustomersTableProps {
  customers: Customer[];
  loading: boolean;
  error: string | null;
  onOpenCustomer: (customerId: number) => void;
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

export function CustomersTable({
  customers,
  loading,
  error,
  onOpenCustomer,
}: CustomersTableProps) {
  return (
    <section
      className="mt-6 overflow-hidden rounded-xl border border-zinc-200 bg-white"
      aria-labelledby="customers-table-title"
    >
      <div className="border-b border-zinc-200 px-4 py-4 md:px-5">
        <h4
          id="customers-table-title"
          className="text-sm font-semibold text-zinc-950"
        >
          Directorio de clientes
        </h4>

        <p className="mt-1 text-xs text-zinc-500">
          Clientes identificados dentro del tenant actual.
        </p>
      </div>

      {loading ? (
        <div
          className="p-8 text-center"
          role="status"
        >
          <div className="mx-auto h-6 w-6 animate-spin rounded-full border-2 border-zinc-300 border-t-zinc-950" />

          <p className="mt-3 text-sm text-zinc-500">
            Cargando clientes...
          </p>
        </div>
      ) : error ? (
        <div
          className="p-8 text-center"
          role="alert"
        >
          <p className="text-sm font-medium text-zinc-900">
            No fue posible mostrar los clientes
          </p>

          <p className="mt-2 text-sm text-zinc-500">
            {error}
          </p>
        </div>
      ) : customers.length === 0 ? (
        <div
          className="p-8 text-center"
          role="status"
        >
          <p className="text-sm font-medium text-zinc-900">
            No hay clientes para mostrar
          </p>

          <p className="mt-2 text-sm text-zinc-500">
            No encontramos clientes que coincidan con los
            filtros actuales.
          </p>
        </div>
      ) : (
        <>
          <div className="divide-y divide-zinc-200 md:hidden">
            {customers.map((customer) => (
              <button
                key={customer.id}
                type="button"
                onClick={() =>
                  onOpenCustomer(customer.id)
                }
                className="block w-full p-4 text-left transition hover:bg-zinc-50 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-zinc-500"
                aria-label={`Ver cliente ${customer.name}`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-zinc-950">
                      {customer.name}
                    </p>

                    <p className="mt-1 truncate text-xs text-zinc-500">
                      {formatContact(customer.phone)}
                    </p>

                    <p className="mt-1 truncate text-xs text-zinc-500">
                      {formatContact(customer.email)}
                    </p>
                  </div>

                  <span
                    className={
                      customer.active
                        ? "shrink-0 rounded-full bg-zinc-900 px-2.5 py-1 text-xs font-medium text-white"
                        : "shrink-0 rounded-full bg-zinc-100 px-2.5 py-1 text-xs font-medium text-zinc-600"
                    }
                  >
                    {customer.active
                      ? "Activo"
                      : "Inactivo"}
                  </span>
                </div>

                <div className="mt-4 grid grid-cols-2 gap-3">
                  <div>
                    <p className="text-xs text-zinc-500">
                      Pedidos
                    </p>

                    <p className="mt-1 text-sm font-semibold text-zinc-900">
                      {customer.order_count.toLocaleString()}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs text-zinc-500">
                      Total registrado
                    </p>

                    <p className="mt-1 text-sm font-semibold text-zinc-900">
                      {formatOrderTotal(
                        customer.order_total,
                      )}
                    </p>
                  </div>
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
                    Cliente
                  </th>

                  <th
                    scope="col"
                    className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500"
                  >
                    Contacto
                  </th>

                  <th
                    scope="col"
                    className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500"
                  >
                    Estado
                  </th>

                  <th
                    scope="col"
                    className="px-5 py-3 text-right text-xs font-semibold uppercase tracking-wide text-zinc-500"
                  >
                    Pedidos
                  </th>

                  <th
                    scope="col"
                    className="px-5 py-3 text-right text-xs font-semibold uppercase tracking-wide text-zinc-500"
                  >
                    Total registrado
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
                {customers.map((customer) => (
                  <tr
                    key={customer.id}
                    className="transition hover:bg-zinc-50"
                  >
                    <td className="whitespace-nowrap px-5 py-4">
                      <p className="text-sm font-semibold text-zinc-950">
                        {customer.name}
                      </p>

                      <p className="mt-1 text-xs text-zinc-500">
                        ID #{customer.id}
                      </p>
                    </td>

                    <td className="px-5 py-4">
                      <p className="text-sm text-zinc-700">
                        {formatContact(customer.phone)}
                      </p>

                      <p className="mt-1 text-xs text-zinc-500">
                        {formatContact(customer.email)}
                      </p>
                    </td>

                    <td className="whitespace-nowrap px-5 py-4">
                      <span
                        className={
                          customer.active
                            ? "inline-flex rounded-full bg-zinc-900 px-2.5 py-1 text-xs font-medium text-white"
                            : "inline-flex rounded-full bg-zinc-100 px-2.5 py-1 text-xs font-medium text-zinc-600"
                        }
                      >
                        {customer.active
                          ? "Activo"
                          : "Inactivo"}
                      </span>
                    </td>

                    <td className="whitespace-nowrap px-5 py-4 text-right text-sm font-medium text-zinc-700">
                      {customer.order_count.toLocaleString()}
                    </td>

                    <td className="whitespace-nowrap px-5 py-4 text-right text-sm font-medium text-zinc-700">
                      {formatOrderTotal(
                        customer.order_total,
                      )}
                    </td>

                    <td className="whitespace-nowrap px-5 py-4 text-right">
                      <button
                        type="button"
                        onClick={() =>
                          onOpenCustomer(customer.id)
                        }
                        className="rounded-lg border border-zinc-300 px-3 py-2 text-xs font-medium text-zinc-700 transition hover:bg-zinc-100 focus:outline-none focus:ring-2 focus:ring-zinc-400 focus:ring-offset-2"
                        aria-label={`Ver detalle de ${customer.name}`}
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