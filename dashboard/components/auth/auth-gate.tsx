"use client";

import {
  type FormEvent,
  type ReactNode,
  useEffect,
  useState,
} from "react";

import {
  establishSession,
  getCurrentUser,
  getTenantAccess,
  logout,
} from "@/lib/auth/client";

import {
  getAccessToken,
  type AuthenticatedUser,
  type TenantAccess,
} from "@/lib/auth/session";

interface AuthGateProps {
  children: ReactNode;
}

type AuthState =
  | "checking"
  | "authenticated"
  | "anonymous";

export default function AuthGate({
  children,
}: AuthGateProps) {
  const [authState, setAuthState] =
    useState<AuthState>("checking");

  const [user, setUser] =
    useState<AuthenticatedUser | null>(null);

  const [tenant, setTenant] =
    useState<TenantAccess | null>(null);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [submitting, setSubmitting] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function restoreSession() {
      if (!getAccessToken()) {
        if (active) {
          setAuthState("anonymous");
        }

        return;
      }

      try {
        const [currentUser, tenantAccess] =
          await Promise.all([
            getCurrentUser(),
            getTenantAccess(),
          ]);

        if (!active) {
          return;
        }

        setUser(currentUser);
        setTenant(tenantAccess);
        setAuthState("authenticated");
      } catch {
        logout();

        if (active) {
          setUser(null);
          setTenant(null);
          setAuthState("anonymous");
        }
      }
    }

    restoreSession();

    return () => {
      active = false;
    };
  }, []);

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    try {
      setSubmitting(true);
      setError(null);

      const session = await establishSession({
        email,
        password,
      });

      setUser(session.user);
      setTenant(session.tenant);

      setPassword("");
      setAuthState("authenticated");
    } catch {
      logout();

      setUser(null);
      setTenant(null);

      setError(
        "No fue posible iniciar sesión. Verifica tus credenciales.",
      );

      setAuthState("anonymous");
    } finally {
      setSubmitting(false);
    }
  }

  function handleLogout() {
    logout();

    setUser(null);
    setTenant(null);
    setEmail("");
    setPassword("");
    setError(null);
    setAuthState("anonymous");
  }

  if (authState === "checking") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-100 px-6">
        <div className="text-center">
          <p className="text-sm font-semibold text-zinc-700">
            Verificando sesión
          </p>

          <p className="mt-1 text-xs text-zinc-400">
            Conectando con LPDB AI Ordering.
          </p>
        </div>
      </div>
    );
  }

  if (authState === "anonymous") {
    return (
      <main className="flex min-h-screen items-center justify-center bg-zinc-100 px-5 py-10">
        <section className="w-full max-w-md rounded-2xl border border-zinc-200 bg-white p-7 shadow-sm">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-zinc-400">
              LPDB
            </p>

            <h1 className="mt-2 text-2xl font-bold tracking-tight text-zinc-950">
              AI Ordering
            </h1>

            <p className="mt-2 text-sm leading-6 text-zinc-500">
              Ingresa a tu centro de operaciones.
            </p>
          </div>

          <form
            className="mt-7 space-y-5"
            onSubmit={handleSubmit}
          >
            <div>
              <label
                htmlFor="email"
                className="text-sm font-medium text-zinc-700"
              >
                Correo electrónico
              </label>

              <input
                id="email"
                name="email"
                type="email"
                autoComplete="username"
                required
                value={email}
                onChange={(event) =>
                  setEmail(event.target.value)
                }
                className="mt-2 w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm text-zinc-950 outline-none transition focus:border-zinc-500 focus:ring-2 focus:ring-zinc-200"
              />
            </div>

            <div>
              <label
                htmlFor="password"
                className="text-sm font-medium text-zinc-700"
              >
                Contraseña
              </label>

              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                minLength={8}
                value={password}
                onChange={(event) =>
                  setPassword(event.target.value)
                }
                className="mt-2 w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm text-zinc-950 outline-none transition focus:border-zinc-500 focus:ring-2 focus:ring-zinc-200"
              />
            </div>

            {error && (
              <div
                role="alert"
                className="rounded-lg border border-red-200 bg-red-50 px-4 py-3"
              >
                <p className="text-sm text-red-700">
                  {error}
                </p>
              </div>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="w-full rounded-lg bg-zinc-950 px-4 py-3 text-sm font-semibold text-white transition hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {submitting
                ? "Ingresando..."
                : "Iniciar sesión"}
            </button>
          </form>
        </section>
      </main>
    );
  }

  return (
    <>
      <div className="fixed bottom-4 right-4 z-40 hidden items-center gap-3 rounded-xl border border-zinc-200 bg-white px-4 py-2 shadow-sm lg:flex">
        <div className="min-w-0">
          <p className="max-w-48 truncate text-xs font-semibold text-zinc-700">
            {user?.email}
          </p>

          <p className="text-[11px] text-zinc-400">
            {tenant?.tenant_name} · {tenant?.role}
          </p>
        </div>

        <button
          type="button"
          onClick={handleLogout}
          className="rounded-md border border-zinc-200 px-2.5 py-1.5 text-xs font-medium text-zinc-600 transition hover:bg-zinc-100"
        >
          Salir
        </button>
      </div>

      {children}
    </>
  );
}
