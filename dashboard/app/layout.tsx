import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";

import AuthGate from "@/components/auth/auth-gate";
import { DashboardShell } from "@/components/layout/dashboard-shell";

import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "LPDB AI Ordering",
  description:
    "Centro de operaciones de Los Perritos del Barrio AI Ordering.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <AuthGate>
          <DashboardShell>
            {children}
          </DashboardShell>
        </AuthGate>
      </body>
    </html>
  );
}
