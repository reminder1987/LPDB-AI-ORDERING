interface IntegrationMetricsProps {
  total: number;
  active: number;
  credentialsConfigured: number;
  providers: number;
}

interface MetricCardProps {
  label: string;
  value: number;
  description: string;
}

function MetricCard({
  label,
  value,
  description,
}: MetricCardProps) {
  return (
    <article className="rounded-xl border border-zinc-200 bg-white p-4 md:p-5">
      <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
        {label}
      </p>

      <p className="mt-2 text-2xl font-bold tracking-tight text-zinc-950">
        {value}
      </p>

      <p className="mt-1 text-xs leading-5 text-zinc-500">
        {description}
      </p>
    </article>
  );
}

export function IntegrationMetrics({
  total,
  active,
  credentialsConfigured,
  providers,
}: IntegrationMetricsProps) {
  return (
    <section
      className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4"
      aria-label="Metricas de integraciones"
    >
      <MetricCard
        label="Integraciones"
        value={total}
        description="Conexiones registradas para el tenant actual."
      />

      <MetricCard
        label="Activas"
        value={active}
        description="Integraciones actualmente marcadas como activas."
      />

      <MetricCard
        label="Con credenciales"
        value={credentialsConfigured}
        description="Integraciones con referencias de credenciales configuradas."
      />

      <MetricCard
        label="Proveedores"
        value={providers}
        description="Proveedores distintos presentes en las integraciones."
      />
    </section>
  );
}