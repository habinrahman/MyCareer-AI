"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useMemo } from "react";
import { queryKeys } from "@/lib/query-keys";
import { tryGetSupabaseBrowserClient } from "@/lib/supabase/client";
import { useSession, useSupabaseConfigured } from "@/hooks/use-session";

export function useAuth() {
  const queryClient = useQueryClient();
  const configured = useSupabaseConfigured();
  const sessionQuery = useSession();

  const user = useMemo(
    () => sessionQuery.data?.user ?? null,
    [sessionQuery.data?.user],
  );

  const signOut = useCallback(async () => {
    const supabase = tryGetSupabaseBrowserClient();
    if (!supabase) return;
    await supabase.auth.signOut({ scope: "global" });
    queryClient.removeQueries({ queryKey: queryKeys.session });
    queryClient.removeQueries({ queryKey: ["profile"] });
    window.location.href = "/";
  }, [queryClient]);

  const refreshSession = useCallback(async () => {
    const supabase = tryGetSupabaseBrowserClient();
    if (!supabase) return;
    await supabase.auth.refreshSession();
    await queryClient.invalidateQueries({ queryKey: queryKeys.session });
  }, [queryClient]);

  return {
    configured,
    session: sessionQuery.data ?? null,
    user,
    isLoading: sessionQuery.isPending,
    isError: sessionQuery.isError,
    error: sessionQuery.error,
    signOut,
    refreshSession,
  };
}
