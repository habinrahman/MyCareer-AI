-- MyCareer AI — legacy minimal schema (profiles + simplified resumes/chat).
--
-- For production, use the full application schema instead:
--   supabase/schema.sql
-- That file defines public.users, analyses, reports, recommendations, storage buckets,
-- and RLS aligned with the FastAPI persistence layer.
--
-- Run in Supabase SQL Editor or: supabase db push

create extension if not exists vector;

-- Optional profile row per auth user (create via trigger or app on first login)
create table if not exists public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  display_name text,
  created_at timestamptz not null default now()
);

create table if not exists public.resumes (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles (id) on delete cascade,
  storage_path text,
  original_filename text not null,
  parsed_text text not null,
  summary text,
  embedding vector(1536),
  meta jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists resumes_user_id_idx on public.resumes (user_id);
create index if not exists resumes_embedding_idx on public.resumes using hnsw (embedding vector_cosine_ops);

create table if not exists public.chat_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles (id) on delete cascade,
  title text,
  created_at timestamptz not null default now()
);

create table if not exists public.chat_messages (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.chat_sessions (id) on delete cascade,
  role text not null check (role in ('user', 'assistant', 'system')),
  content text not null,
  created_at timestamptz not null default now()
);

create index if not exists chat_messages_session_idx on public.chat_messages (session_id);

-- Row Level Security
alter table public.profiles enable row level security;
alter table public.resumes enable row level security;
alter table public.chat_sessions enable row level security;
alter table public.chat_messages enable row level security;

-- Profiles: users manage their own row
create policy "profiles_select_own" on public.profiles for select using (auth.uid() = id);
create policy "profiles_insert_own" on public.profiles for insert with check (auth.uid() = id);
create policy "profiles_update_own" on public.profiles for update using (auth.uid() = id);

-- Resumes
create policy "resumes_select_own" on public.resumes for select using (auth.uid() = user_id);
create policy "resumes_insert_own" on public.resumes for insert with check (auth.uid() = user_id);
create policy "resumes_update_own" on public.resumes for update using (auth.uid() = user_id);
create policy "resumes_delete_own" on public.resumes for delete using (auth.uid() = user_id);

-- Chat
create policy "chat_sessions_select_own" on public.chat_sessions for select using (auth.uid() = user_id);
create policy "chat_sessions_insert_own" on public.chat_sessions for insert with check (auth.uid() = user_id);
create policy "chat_sessions_update_own" on public.chat_sessions for update using (auth.uid() = user_id);
create policy "chat_sessions_delete_own" on public.chat_sessions for delete using (auth.uid() = user_id);

create policy "chat_messages_select_own" on public.chat_messages for select
  using (
    exists (
      select 1 from public.chat_sessions s
      where s.id = chat_messages.session_id and s.user_id = auth.uid()
    )
  );
create policy "chat_messages_insert_own" on public.chat_messages for insert
  with check (
    exists (
      select 1 from public.chat_sessions s
      where s.id = chat_messages.session_id and s.user_id = auth.uid()
    )
  );

-- Service role (FastAPI with service key) bypasses RLS — use least privilege in production.
