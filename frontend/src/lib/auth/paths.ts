/** App routes that require a Supabase session (middleware + client guard). */
const PROTECTED_PREFIXES = [
  "/dashboard",
  "/resume",
  "/chat",
  "/reports",
  "/analysis",
  "/settings",
] as const;

const AUTH_PREFIX = "/auth";

export function isProtectedPath(pathname: string): boolean {
  return PROTECTED_PREFIXES.some(
    (p) => pathname === p || pathname.startsWith(`${p}/`),
  );
}

export function isAuthPath(pathname: string): boolean {
  return (
    pathname === AUTH_PREFIX ||
    pathname.startsWith(`${AUTH_PREFIX}/`)
  );
}

/** Internal redirect target only (middleware / auth callback). */
export function safeNextPath(next: string | null): string {
  if (!next || !next.startsWith("/") || next.startsWith("//")) {
    return "/dashboard";
  }
  if (next.includes("://")) {
    return "/dashboard";
  }
  return next;
}
