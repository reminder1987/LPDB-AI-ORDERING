"use client";

import {
  createContext,
  type ReactNode,
  useContext,
} from "react";

import type {
  AuthenticatedUser,
  TenantAccess,
} from "@/lib/auth/session";

export type DashboardSession = {
  user: AuthenticatedUser;
  tenant: TenantAccess;
};

type DashboardSessionProviderProps = {
  session: DashboardSession;
  children: ReactNode;
};

const DashboardSessionContext =
  createContext<DashboardSession | null>(null);

export function DashboardSessionProvider({
  session,
  children,
}: DashboardSessionProviderProps) {
  return (
    <DashboardSessionContext.Provider value={session}>
      {children}
    </DashboardSessionContext.Provider>
  );
}

export function useDashboardSession(): DashboardSession {
  const session = useContext(DashboardSessionContext);

  if (!session) {
    throw new Error(
      "useDashboardSession must be used within DashboardSessionProvider",
    );
  }

  return session;
}

export function useDashboardUser(): AuthenticatedUser {
  return useDashboardSession().user;
}

export function useDashboardTenant(): TenantAccess {
  return useDashboardSession().tenant;
}

export function useDashboardRole(): string {
  return useDashboardSession().tenant.role;
}