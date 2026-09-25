"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  useEffect,
  useRef,
  useState,
} from "react";

import { dashboardNavigation } from "@/lib/dashboard/navigation";

function isNavigationItemActive(
  pathname: string,
  href: string,
) {
  if (href === "/") {
    return pathname === "/";
  }

  return pathname === href || pathname.startsWith(`${href}/`);
}

export function DashboardHeader() {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!menuOpen) {
      return;
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setMenuOpen(false);
        menuButtonRef.current?.focus();
      }
    }

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [menuOpen]);

  function closeMenu() {
    setMenuOpen(false);
  }

  return (
    <header className="relative z-40 border-b border-zinc-200 bg-white">
      <div className="flex min-h-16 items-center justify-between gap-3 px-4 sm:px-6 lg:px-8">
        <div className="min-w-0">
          <p className="truncate text-xs font-medium uppercase tracking-wide text-zinc-500">
            Los Perritos del Barrio
          </p>

          <p className="truncate text-sm font-semibold text-zinc-950">
            Centro de operaciones
          </p>
        </div>

        <div className="flex shrink-0 items-center gap-3">
          <div
            className="hidden items-center gap-2 sm:flex"
            role="status"
            aria-label="Sistema operativo"
          >
            <span
              className="inline-block h-2.5 w-2.5 rounded-full bg-emerald-500"
              aria-hidden="true"
            />

            <span className="text-xs font-medium text-zinc-600">
              Operativo
            </span>
          </div>

          <button
            ref={menuButtonRef}
            type="button"
            className="inline-flex min-h-11 min-w-11 items-center justify-center rounded-lg border border-zinc-200 bg-white px-3 text-sm font-medium text-zinc-700 transition hover:bg-zinc-100 focus:outline-none focus:ring-2 focus:ring-zinc-400 focus:ring-offset-2 lg:hidden"
            aria-expanded={menuOpen}
            aria-controls="dashboard-mobile-navigation"
            aria-label={
              menuOpen
                ? "Cerrar navegacion"
                : "Abrir navegacion"
            }
            onClick={() =>
              setMenuOpen((current) => !current)
            }
          >
            <span aria-hidden="true">
              {menuOpen ? "Cerrar" : "Menu"}
            </span>
          </button>
        </div>
      </div>

      {menuOpen && (
        <div
          id="dashboard-mobile-navigation"
          className="border-t border-zinc-200 bg-white px-4 py-4 shadow-lg sm:px-6 lg:hidden"
        >
          <nav
            aria-label="Navegacion principal movil"
            className="flex flex-col gap-1"
          >
            {dashboardNavigation.map((item) => {
              if (!item.enabled) {
                return (
                  <div
                    key={item.label}
                    className="rounded-lg px-3 py-3 text-sm text-zinc-400"
                    aria-disabled="true"
                  >
                    <div className="font-medium">
                      {item.label}
                    </div>

                    <div className="mt-0.5 text-xs">
                      Proximamente
                    </div>
                  </div>
                );
              }

              const isActive =
                isNavigationItemActive(
                  pathname,
                  item.href,
                );

              return (
                <Link
                  key={item.label}
                  href={item.href}
                  onClick={closeMenu}
                  aria-current={
                    isActive ? "page" : undefined
                  }
                  className={
                    isActive
                      ? "rounded-lg bg-zinc-950 px-3 py-3 text-sm font-medium text-white focus:outline-none focus:ring-2 focus:ring-zinc-400 focus:ring-offset-2"
                      : "rounded-lg px-3 py-3 text-sm font-medium text-zinc-700 transition hover:bg-zinc-100 focus:outline-none focus:ring-2 focus:ring-zinc-400 focus:ring-offset-2"
                  }
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>

          <div className="mt-4 border-t border-zinc-200 pt-4 sm:hidden">
            <div
              className="flex items-center gap-2"
              role="status"
              aria-label="Sistema operativo"
            >
              <span
                className="inline-block h-2.5 w-2.5 rounded-full bg-emerald-500"
                aria-hidden="true"
              />

              <span className="text-xs font-medium text-zinc-600">
                Operativo
              </span>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}