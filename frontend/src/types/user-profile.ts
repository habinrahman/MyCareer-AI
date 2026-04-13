export type AppUserRow = {
  id: string;
  email: string | null;
  display_name: string | null;
  avatar_url: string | null;
  timezone: string | null;
  preferences: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};
