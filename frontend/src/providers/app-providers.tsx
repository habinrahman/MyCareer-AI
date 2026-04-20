"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { AuthSessionListener } from "@/components/providers/auth-session-listener";
import { featureFlags } from "@/lib/feature-flags";

export function AppProviders({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            refetchOnWindowFocus: false,
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={queryClient}>
      {featureFlags.auth ? <AuthSessionListener /> : null}
      {children}
    </QueryClientProvider>
  );
}
