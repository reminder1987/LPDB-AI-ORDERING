interface CustomerMetricsProps {
  total: number;
  active: number;
  withOrders: number;
  orderCount: number;
  loading: boolean;
}

interface MetricCardProps {
  label: string;
  value: number;
  description: string;
  loading: boolean;
}

function MetricCard({
  label,
  value,
  description,
  loading,
}: MetricCardProps) {
  return (
    <article className="rounded-xl border border-zinc-200 bg-white p-5">
      <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
        {label}
      </p>

      {loading ? (
        <div
          className="mt-3 h-9 w-20 animate-pulse rounded bg-zinc-200"
          aria-label={`Cargando ${label.toLowerCase()}`}
        />
      ) : (
        <p className="mt-2 text-3xl font-bold tracking-tight text-zinc-950">
          {value.toLocaleString()}
        </p>
      )}

      <p className="mt-2 text-xs leading-5 text-zinc-500">
        {description}
      </p>
    </article>
  );
}

export function CustomerMetrics({
  total,
  active,
  withOrders,
  orderCount,
  loading,
}: CustomerMetricsProps) {
  return (
    <section
      className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"
      aria-label="Resumen de clientes"
    >
      <MetricCard
        label="Clientes"
        value={total}
        description="Clientes visibles con los filtros actuales."
        loading={loading}
      />

      <MetricCard
        label="Activos"
        value={active}
        description="Clientes activos dentro del resultado actual."
        loading={loading}
      />

      <MetricCard
        label="Con pedidos"
        value={withOrders}
        description="Clientes que tienen al menos un pedido asociado."
        loading={loading}
      />

      <MetricCard
        label="Pedidos"
        value={orderCount}
        description="Pedidos asociados a los clientes mostrados."
        loading={loading}
      />
    </section>
  );
}