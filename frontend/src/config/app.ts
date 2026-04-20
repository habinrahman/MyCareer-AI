/**
 * App-wide public config (browser-safe `NEXT_PUBLIC_*` only).
 * Set values in `.env.local` / deployment env — no hardcoded production URLs in UI components.
 */

function envString(key: string): string | undefined {
  const v = process.env[key];
  return typeof v === "string" && v.trim().length > 0 ? v.trim() : undefined;
}

export const APP_CONFIG = {
  /** Public path or absolute URL for the marketing logo (see `next.config` if using remote). */
  logo: envString("NEXT_PUBLIC_APP_LOGO_SRC") ?? "/microdegree-logo.png",

  /** Full origin for the main marketing site (logo link target). */
  mainWebsiteUrl:
    envString("NEXT_PUBLIC_MAIN_SITE_URL") ?? "https://www.microdegree.work",
} as const;
