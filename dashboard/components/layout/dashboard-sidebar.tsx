import Link from "next/link";

import { dashboardNavigation } from "@/lib/dashboard/navigation";

export function DashboardSidebar() {
  return (
    <aside
      aria-label="Navegación principal"
      className="hidden w-64 shrink-0 border-r border-zinc-200 bg-white lg:flex lg:flex-col"
    >
      <div className="border-b border-zinc-200 px-6 py-6">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-500">
          LPDB
        </p>

        <p className="mt-1 text-lg font-semibold text-zinc-950">
          AI Ordering
        </p>
      </div>

      <nav className="flex flex-1 flex-col gap-1 p-4">
        {dashboardNavigation.map((item) => {
          if (!item.enabled) {
            return (
              <div
                key={item.label}
                className="rounded-lg px-3 py-3 text-sm text-zinc-400"
                title="Disponible próximamente"
              >
                <div className="font-medium">{item.label}</div>

                <div className="mt-0.5 text-xs text-zinc-400">
                  Próximamente
                </div>
              </div>
            );
          }

          return (
            <Link
              key={item.label}
              href={item.href}
              className="rounded-lg bg-zinc-950 px-3 py-3 text-sm font-medium text-white"
            >
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-zinc-200 p-4">
        <p className="text-xs text-zinc-500">
          Operational Dashboard
        </p>
      </div>
    </aside>
  );
}
