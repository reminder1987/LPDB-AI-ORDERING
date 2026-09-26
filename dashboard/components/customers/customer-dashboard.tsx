"use client";

import { useEffect, useMemo, useState } from "react";

import {
  getCustomer,
  getCustomers,
  type Customer,
  type CustomerDetail,
} from "@/lib/api";

import { CustomerDetailDrawer } from "./customer-detail-drawer";
import { CustomerMetrics } from "./customer-metrics";
import { CustomersTable } from "./customers-table";

type ActiveFilter = "all" | "active" | "inactive";

function getCustomerErrorMessage(
  error: unknown,
  fallback: string,
): string {
  if (!(error instanceof Error)) {
    return fallback;
  }

  if (error.message === "AUTH_REQUIRED") {
    return "La sesion expiro. Inicia sesion nuevamente.";
  }

  if (
    error.message === "PERMISSION_DENIED" ||
    error.message.includes("API error 403")
  ) {
    return "No tienes permisos para consultar los clientes.";
  }

  return error.message || fallback;
}

export function CustomerDashboard() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [searchInput, setSearchInput] = useState("");
  const [searchFilter, setSearchFilter] = useState("");
  const [activeFilter, setActiveFilter] =
    useState<ActiveFilter>("all");

  const [selectedCustomer, setSelectedCustomer] =
    useState<CustomerDetail | null>(null);
  const [detailLoading, setDetailLoading] =
    useState(false);
  const [detailError, setDetailError] =
    useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadCustomers() {
      try {
        setLoading(true);
        setError(null);

        const response = await getCustomers({
          search: searchFilter || undefined,
          active:
            activeFilter === "all"
              ? undefined
              : activeFilter === "active",
        });

        if (!active) {
          return;
        }

        setCustomers(response);
      } catch (err) {
        if (!active) {
          return;
        }

        setError(
          getCustomerErrorMessage(
            err,
            "No fue posible cargar los clientes.",
          ),
        );
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadCustomers();

    return () => {
      active = false;
    };
  }, [searchFilter, activeFilter]);

  useEffect(() => {
    if (!selectedCustomer && !detailLoading) {
      return;
    }

    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setSelectedCustomer(null);
        setDetailError(null);
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
  }, [selectedCustomer, detailLoading]);

  async function handleOpenCustomer(
    customerId: number,
  ) {
    try {
      setDetailLoading(true);
      setDetailError(null);
      setSelectedCustomer(null);

      const customer = await getCustomer(customerId);

      setSelectedCustomer(customer);
    } catch (err) {
      setSelectedCustomer(null);
      setDetailError(
        getCustomerErrorMessage(
          err,
          "No fue posible cargar el detalle del cliente.",
        ),
      );
    } finally {
      setDetailLoading(false);
    }
  }

  function handleCloseCustomer() {
    setSelectedCustomer(null);
    setDetailError(null);
  }

  function handleSearchSubmit(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();
    setSearchFilter(searchInput.trim());
  }

  function handleClearFilters() {
    setSearchInput("");
    setSearchFilter("");
    setActiveFilter("all");
  }

  const metrics = useMemo(() => {
    const activeCustomers = customers.filter(
      (customer) => customer.active,
    );

    const customersWithOrders = customers.filter(
      (customer) => customer.order_count > 0,
    );

    const orderCount = customers.reduce(
      (total, customer) =>
        total + customer.order_count,
      0,
    );

    return {
      total: customers.length,
      active: activeCustomers.length,
      withOrders: customersWithOrders.length,
      orderCount,
    };
  }, [customers]);

  const hasFilters =
    Boolean(searchFilter) ||
    activeFilter !== "all";

  return (
    <div className="min-h-full bg-zinc-100 p-5 text-zinc-950 md:p-8">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8">
          <p className="text-sm font-medium text-zinc-500">
            Operacion
          </p>

          <h3 className="mt-1 text-3xl font-bold tracking-tight">
            Clientes
          </h3>

          <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-500">
            Consulta los clientes identificados por el sistema,
            sus canales asociados y su actividad de pedidos.
          </p>

          <div
            className="mt-4 max-w-2xl rounded-lg border border-zinc-200 bg-white px-4 py-3"
            role="status"
          >
            <p className="text-sm font-medium text-zinc-700">
              Vista operacional de solo lectura
            </p>

            <p className="mt-1 text-xs leading-5 text-zinc-500">
              La informacion de clientes e identidades se
              consulta desde este modulo sin modificar los
              registros operativos.
            </p>
          </div>
        </div>

        <CustomerMetrics
          total={metrics.total}
          active={metrics.active}
          withOrders={metrics.withOrders}
          orderCount={metrics.orderCount}
          loading={loading}
        />

        <section
          className="mt-6 rounded-xl border border-zinc-200 bg-white p-4 md:p-5"
          aria-labelledby="customer-filters-title"
        >
          <form
            onSubmit={handleSearchSubmit}
            className="flex flex-col gap-4 lg:flex-row lg:items-end"
          >
            <div className="flex-1">
              <h4
                id="customer-filters-title"
                className="text-sm font-semibold text-zinc-950"
              >
                Filtros
              </h4>

              <p className="mt-1 text-xs text-zinc-500">
                Busca por nombre, telefono o correo y filtra
                por estado.
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-2 lg:w-[38rem]">
              <label className="block">
                <span className="text-xs font-medium text-zinc-600">
                  Buscar cliente
                </span>

                <input
                  type="search"
                  value={searchInput}
                  onChange={(event) =>
                    setSearchInput(event.target.value)
                  }
                  placeholder="Nombre, telefono o correo"
                  className="mt-1 w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm outline-none transition placeholder:text-zinc-400 focus:border-zinc-500 focus:ring-2 focus:ring-zinc-200"
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
                      event.target.value as ActiveFilter,
                    )
                  }
                  className="mt-1 w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm outline-none transition focus:border-zinc-500 focus:ring-2 focus:ring-zinc-200"
                >
                  <option value="all">
                    Todos los clientes
                  </option>
                  <option value="active">
                    Activos
                  </option>
                  <option value="inactive">
                    Inactivos
                  </option>
                </select>
              </label>
            </div>

            <button
              type="submit"
              className="rounded-lg bg-zinc-950 px-4 py-2 text-sm font-medium text-white transition hover:bg-zinc-800 focus:outline-none focus:ring-2 focus:ring-zinc-500 focus:ring-offset-2"
            >
              Buscar
            </button>

            {hasFilters && (
              <button
                type="button"
                onClick={handleClearFilters}
                className="rounded-lg border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 transition hover:bg-zinc-100 focus:outline-none focus:ring-2 focus:ring-zinc-400 focus:ring-offset-2"
              >
                Limpiar filtros
              </button>
            )}
          </form>
        </section>

        <CustomersTable
          customers={customers}
          loading={loading}
          error={error}
          onOpenCustomer={handleOpenCustomer}
        />
      </div>

      <CustomerDetailDrawer
        customer={selectedCustomer}
        loading={detailLoading}
        error={detailError}
        onClose={handleCloseCustomer}
      />
    </div>
  );
}