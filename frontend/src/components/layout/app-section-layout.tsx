"use client";

import { DashboardShell } from "@/components/layout/dashboard-shell";
import { RequireAuth } from "@/components/layout/require-auth";

export function AppSectionLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <RequireAuth>
      <DashboardShell>{children}</DashboardShell>
    </RequireAuth>
  );
}
