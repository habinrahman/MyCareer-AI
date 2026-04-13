"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "@/lib/query-keys";
import { tryGetSupabaseBrowserClient } from "@/lib/supabase/client";
import type { AppUserRow } from "@/types/user-profile";
import { useSession } from "@/hooks/use-session";

export type ProfileUpdate = {
  display_name?: string | null;
  avatar_url?: string | null;
  timezone?: string | null;
};

export function useProfile() {
  const queryClient = useQueryClient();
  const { data: session } = useSession();
  const userId = session?.user.id;

  const query = useQuery({
    queryKey: userId ? queryKeys.profile(userId) : ["profile", "none"],
    queryFn: async (): Promise<AppUserRow> => {
      const supabase = tryGetSupabaseBrowserClient();
      if (!supabase || !userId) {
        throw new Error("Not authenticated");
      }
      const { data, error } = await supabase
        .from("users")
        .select(
          "id, email, display_name, avatar_url, timezone, preferences, created_at, updated_at",
        )
        .eq("id", userId)
        .single();
      if (error) throw error;
      return data as AppUserRow;
    },
    enabled: !!userId,
  });

  const updateMutation = useMutation({
    mutationFn: async (patch: ProfileUpdate) => {
      const supabase = tryGetSupabaseBrowserClient();
      if (!supabase || !userId) throw new Error("Not authenticated");
      const { data, error } = await supabase
        .from("users")
        .update(patch)
        .eq("id", userId)
        .select(
          "id, email, display_name, avatar_url, timezone, preferences, created_at, updated_at",
        )
        .single();
      if (error) throw error;
      return data as AppUserRow;
    },
    onSuccess: (row) => {
      queryClient.setQueryData(queryKeys.profile(row.id), row);
    },
  });

  return { ...query, updateProfile: updateMutation.mutateAsync, updateState: updateMutation };
}
