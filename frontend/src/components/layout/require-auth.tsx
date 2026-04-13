"use client";

/**
 * Client guard after middleware: avoids UI flash and stale client state.
 * Session is only read after hydration so SSR HTML matches the first client paint.
 */
import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AuthSkeleton } from "@/components/ui/auth-skeleton";
import {
  useHydrationReady,
  useSession,
  useSupabaseConfigured,
} from "@/hooks/use-session";

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const hydrated = useHydrationReady();
  const configured = useSupabaseConfigured();
  const { data: session, isPending, isError, error } = useSession();

  useEffect(() => {
    if (!configured || !hydrated || isPending) return;
    if (!session) {
      const next = encodeURIComponent(pathname || "/dashboard");
      router.replace(`/auth/login?next=${next}`);
    }
  }, [configured, hydrated, isPending, session, router, pathname]);

  if (!configured) {
    return (
      <div className="mx-auto max-w-lg p-6">
        <Alert>
          <AlertTitle>Supabase not configured</AlertTitle>
          <AlertDescription>
            Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY in
            .env.local, then restart the dev server.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="mx-auto max-w-lg p-6">
        <Alert variant="destructive">
          <AlertTitle>Could not load session</AlertTitle>
          <AlertDescription>
            {error instanceof Error ? error.message : "Unknown error"}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  if (!hydrated || isPending || !session) {
    return <AuthSkeleton />;
  }

  return <>{children}</>;
}
