"use client";

/**
 * Client session from Supabase (PKCE + cookies via @supabase/ssr).
 * Session fetch is disabled until the browser hydrates so SSR markup matches
 * the first client paint (avoids hydration mismatches).
 */
import { useSyncExternalStore } from "react";
import { useQuery } from "@tanstack/react-query";
import type { Session } from "@supabase/supabase-js";
import { queryKeys } from "@/lib/query-keys";
import { tryGetSupabaseBrowserClient } from "@/lib/supabase/client";

function subscribeNoop() {
  return () => {};
}

/** `false` during SSR and the first hydrated paint; then `true`. */
export function useHydrationReady(): boolean {
  return useSyncExternalStore(subscribeNoop, () => true, () => false);
}

/** Same on server and client — do not use `window` or a browser-only Supabase client. */
export function useSupabaseConfigured(): boolean {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const anon = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  return Boolean(url && anon);
}

export function useSession() {
  const isClient = useHydrationReady();
  return useQuery({
    queryKey: queryKeys.session,
    enabled: isClient,
    queryFn: async (): Promise<Session | null> => {
      const supabase = tryGetSupabaseBrowserClient();
      if (!supabase) return null;
      const { data, error } = await supabase.auth.getSession();
      if (error) throw error;
      return data.session ?? null;
    },
  });
}
