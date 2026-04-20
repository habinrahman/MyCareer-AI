import axios, { type AxiosInstance, type InternalAxiosRequestConfig } from "axios";

import { featureFlags } from "@/lib/feature-flags";
import { tryGetSupabaseBrowserClient } from "@/lib/supabaseClient";

/**
 * Empty / whitespace NEXT_PUBLIC_API_URL must not become "" — Axios would then
 * hit the Next.js origin (e.g. POST /public/... → 404) and the browser reports a CORS error.
 */
function resolveApiBaseUrl(): string {
  const raw = (process.env.NEXT_PUBLIC_API_URL ?? "").trim().replace(/\/$/, "");
  return raw.length > 0 ? raw : "http://localhost:8000";
}

const baseURL = resolveApiBaseUrl();

/** Resolved API origin for fetch/axios (same as axios `baseURL`). */
export const API_BASE_URL = baseURL;

/** Optional override (e.g. tests). If unset, the interceptor reads the browser session. */
let getAccessTokenOverride: (() => Promise<string | null>) | null = null;

export function setApiAuthTokenGetter(fn: () => Promise<string | null>) {
  getAccessTokenOverride = fn;
}

export function getApiBaseUrl(): string {
  return baseURL;
}

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public body?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

const api: AxiosInstance = axios.create({
  baseURL,
  timeout: 120_000,
});

api.interceptors.request.use(async (config: InternalAxiosRequestConfig) => {
  // multipart/form-data: do not set Content-Type so the runtime can add the boundary.
  if (config.data instanceof FormData) {
    config.headers.delete("Content-Type");
  } else {
    config.headers.set("Content-Type", "application/json");
  }
  let token: string | null = null;
  if (!featureFlags.auth) {
    return config;
  }
  if (getAccessTokenOverride) {
    token = await getAccessTokenOverride();
  } else if (typeof window !== "undefined") {
    const client = tryGetSupabaseBrowserClient();
    if (client) {
      // Validates / refreshes session with Supabase Auth (cookie-backed SSR client).
      await client.auth.getUser();
      let {
        data: { session },
      } = await client.auth.getSession();
      if (!session?.access_token) {
        const { data } = await client.auth.refreshSession();
        session = data.session;
      }
      token = session?.access_token ?? null;
    }
  }
  if (token) {
    config.headers.set("Authorization", `Bearer ${token}`);
  }
  return config;
});

export const apiClient = api;

/**
 * Public resume analysis only — never attaches Supabase JWT.
 * Use from MicroDegree Resume Intelligence and other unauthenticated flows.
 */
export const publicResumeApi: AxiosInstance = axios.create({
  baseURL,
  timeout: 120_000,
});

publicResumeApi.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (config.data instanceof FormData) {
    config.headers.delete("Content-Type");
  } else {
    config.headers.set("Content-Type", "application/json");
  }
  return config;
});

export default api;

export async function apiFetch(
  path: string,
  init: RequestInit & { accessToken?: string } = {},
): Promise<Response> {
  const { accessToken, headers, ...rest } = init;
  const hdrs = new Headers(headers);
  if (accessToken) {
    hdrs.set("Authorization", `Bearer ${accessToken}`);
  } else if (!featureFlags.auth) {
    // Public-only mode: no Supabase session
  } else if (typeof window !== "undefined") {
    const client = tryGetSupabaseBrowserClient();
    if (client) {
      await client.auth.getUser();
      let {
        data: { session },
      } = await client.auth.getSession();
      if (!session?.access_token) {
        const { data } = await client.auth.refreshSession();
        session = data.session;
      }
      const t = session?.access_token;
      if (t) hdrs.set("Authorization", `Bearer ${t}`);
    }
  }
  return fetch(`${baseURL}${path}`, { ...rest, headers: hdrs });
}
