"use client";

import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { tryGetSupabaseBrowserClient } from "@/lib/supabase/client";
import { queryKeys } from "@/lib/query-keys";

export function AuthSessionListener() {
  const queryClient = useQueryClient();

  useEffect(() => {
    const supabase = tryGetSupabaseBrowserClient();
    if (!supabase) return;
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(() => {
      queryClient.invalidateQueries({ queryKey: queryKeys.session });
    });
    return () => subscription.unsubscribe();
  }, [queryClient]);

  return null;
}
