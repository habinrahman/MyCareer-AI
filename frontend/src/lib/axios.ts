/**
 * Axios instance with Supabase JWT attached (same as `@/lib/api`).
 *
 * Prefer `@/lib/api` in new code. This file exists for imports expecting `lib/axios`.
 */
export { apiClient as axiosInstance, apiClient, default } from "./api";
