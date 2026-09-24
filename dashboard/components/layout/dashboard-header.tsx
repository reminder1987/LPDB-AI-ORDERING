export function DashboardHeader() {
  return (
    <header className="border-b border-zinc-200 bg-white">
      <div className="flex min-h-16 items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
            Los Perritos del Barrio
          </p>

          <p className="text-sm font-semibold text-zinc-950">
            Centro de operaciones
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span
            aria-label="Sistema activo"
            className="inline-block h-2.5 w-2.5 rounded-full bg-emerald-500"
          />

          <span className="text-xs font-medium text-zinc-600">
            Operativo
          </span>
        </div>
      </div>
    </header>
  );
}
