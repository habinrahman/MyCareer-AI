/**
 * Browser Supabase access for MyCareer AI.
 *
 * Required env (Next.js inlines `NEXT_PUBLIC_*` at build time):
 * - NEXT_PUBLIC_SUPABASE_URL
 * - NEXT_PUBLIC_SUPABASE_ANON_KEY
 *
 * We use `@supabase/ssr` `createBrowserClient` so the session matches
 * middleware/cookies (PKCE). A standalone `createClient` from `@supabase/supabase-js`
 * only can desync from the cookie session and cause missing JWTs on API calls (401).
 *
 * `supabase` exposes `.auth.getSession()` / `.auth.refreshSession()` for Axios.
 */
import { createBrowserClient } from "@supabase/ssr";
import type { SupabaseClient } from "@supabase/supabase-js";

let browserClient: SupabaseClient | null = null;

export function tryGetSupabaseBrowserClient(): SupabaseClient | null {
  if (typeof window === "undefined") return null;
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL?.trim();
  const anon = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY?.trim();
  if (!url || !anon) return null;
  if (!browserClient) {
    browserClient = createBrowserClient(url, anon);
  }
  return browserClient;
}

export function getSupabaseBrowserClient(): SupabaseClient {
  const client = tryGetSupabaseBrowserClient();
  if (!client) {
    throw new Error(
      "Missing NEXT_PUBLIC_SUPABASE_URL or NEXT_PUBLIC_SUPABASE_ANON_KEY",
    );
  }
  return client;
}

/** Browser-safe auth helpers for Axios (same cookie-backed client as the rest of the app). */
export const supabase = {
  auth: {
    getSession: () => {
      const c = tryGetSupabaseBrowserClient();
      if (!c) {
        return Promise.resolve({ data: { session: null }, error: null });
      }
      return c.auth.getSession();
    },
    refreshSession: () => {
      const c = tryGetSupabaseBrowserClient();
      if (!c) {
        return Promise.resolve({
          data: { session: null, user: null },
          error: null,
        });
      }
      return c.auth.refreshSession();
    },
  },
};
