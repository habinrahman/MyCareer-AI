"use client";

import { Skeleton } from "@/components/ui/skeleton";

/**
 * Stable loading UI for auth-gated routes (matches server + first client paint).
 */
export function AuthSkeleton() {
  return (
    <div
      className="mx-auto flex min-h-[50vh] max-w-2xl flex-col justify-center space-y-4 p-8"
      aria-busy="true"
      aria-label="Loading workspace"
    >
      <Skeleton className="h-10 w-48" />
      <Skeleton className="h-32 w-full" />
      <Skeleton className="h-32 w-full" />
    </div>
  );
}
