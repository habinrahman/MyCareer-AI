-- =============================================================================
-- MyCareer AI â€” production schema for Supabase (PostgreSQL + pgvector)
-- =============================================================================
-- Run this file in the Supabase SQL Editor on a project (Dashboard â†’ SQL).
--
-- Prerequisites: none (extensions are created below).
-- Greenfield: applies cleanly to an empty public schema.
-- If you previously ran migrations using public.profiles, migrate data before
-- adopting this schema or drop legacy objects in a maintenance window.
--
-- Storage (Dashboard + policies below):
--   This script inserts into storage.buckets and defines RLS on storage.objects.
--   Client uploads should use object keys: "<auth.uid()>/<rest-of-path>".
--
-- Embeddings: dimension 1536 (OpenAI text-embedding-3-small default).
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Extensions
-- -----------------------------------------------------------------------------
create extension if not exists vector;

-- -----------------------------------------------------------------------------
-- Timestamps
-- -----------------------------------------------------------------------------
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

-- -----------------------------------------------------------------------------
-- 1. users â€” application profile bound 1:1 to auth.users
-- -----------------------------------------------------------------------------
create table if not exists public.users (
  id uuid primary key references auth.users (id) on delete cascade,
  email text,
  display_name text,
  avatar_url text,
  timezone text,
  preferences jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint users_email_check check (email is null or char_length(email) <= 320)
);

create index if not exists users_created_at_idx on public.users (created_at desc);

drop trigger if exists trg_users_updated_at on public.users;
create trigger trg_users_updated_at
  before update on public.users
  for each row execute function public.set_updated_at();

-- Auto-provision public.users when a Supabase Auth user is created
create or replace function public.handle_new_auth_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.users (id, email, display_name)
  values (
    new.id,
    new.email,
    coalesce(
      new.raw_user_meta_data->>'display_name',
      new.raw_user_meta_data->>'full_name',
      split_part(coalesce(new.email, ''), '@', 1)
    )
  )
  on conflict (id) do update
    set email = excluded.email,
        display_name = coalesce(public.users.display_name, excluded.display_name),
        updated_at = now();
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_auth_user();

-- -----------------------------------------------------------------------------
-- 2. resumes â€” file metadata + parsed text + optional embedding
-- -----------------------------------------------------------------------------
create table if not exists public.resumes (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users (id) on delete cascade,
  original_filename text not null,
  mime_type text,
  file_size_bytes bigint,
  storage_path text,
  parsing_status text not null default 'pending'
    check (parsing_status in ('pending', 'processing', 'ready', 'failed')),
  parsed_text text,
  language text,
  meta jsonb not null default '{}'::jsonb,
  embedding vector(1536),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists resumes_user_created_idx
  on public.resumes (user_id, created_at desc);

create index if not exists resumes_parsing_status_idx
  on public.resumes (user_id, parsing_status)
  where parsing_status is not null;

create index if not exists resumes_embedding_hnsw_idx
  on public.resumes
  using hnsw (embedding vector_cosine_ops)
  where embedding is not null;

create index if not exists resumes_meta_gin_idx
  on public.resumes using gin (meta jsonb_path_ops);

drop trigger if exists trg_resumes_updated_at on public.resumes;
create trigger trg_resumes_updated_at
  before update on public.resumes
  for each row execute function public.set_updated_at();

-- -----------------------------------------------------------------------------
-- 3. analyses â€” structured AI output per resume (versioned)
-- -----------------------------------------------------------------------------
create table if not exists public.analyses (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users (id) on delete cascade,
  resume_id uuid not null references public.resumes (id) on delete cascade,
  analysis_version int not null default 1,
  model text not null,
  prompt_version text,
  summary text,
  findings jsonb not null default '{}'::jsonb,
  scores jsonb not null default '{}'::jsonb,
  embedding vector(1536),
  meta jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint analyses_resume_version_uniq unique (resume_id, analysis_version)
);

create index if not exists analyses_user_created_idx
  on public.analyses (user_id, created_at desc);

create index if not exists analyses_resume_idx
  on public.analyses (resume_id);

create index if not exists analyses_embedding_hnsw_idx
  on public.analyses
  using hnsw (embedding vector_cosine_ops)
  where embedding is not null;

create index if not exists analyses_findings_gin_idx
  on public.analyses using gin (findings jsonb_path_ops);

drop trigger if exists trg_analyses_updated_at on public.analyses;
create trigger trg_analyses_updated_at
  before update on public.analyses
  for each row execute function public.set_updated_at();

-- -----------------------------------------------------------------------------
-- 4. chat_sessions
-- -----------------------------------------------------------------------------
create table if not exists public.chat_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users (id) on delete cascade,
  resume_id uuid references public.resumes (id) on delete set null,
  title text,
  meta jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists chat_sessions_user_created_idx
  on public.chat_sessions (user_id, created_at desc);

create index if not exists chat_sessions_resume_idx
  on public.chat_sessions (resume_id)
  where resume_id is not null;

drop trigger if exists trg_chat_sessions_updated_at on public.chat_sessions;
create trigger trg_chat_sessions_updated_at
  before update on public.chat_sessions
  for each row execute function public.set_updated_at();

-- -----------------------------------------------------------------------------
-- 5. chat_messages
-- -----------------------------------------------------------------------------
create table if not exists public.chat_messages (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.chat_sessions (id) on delete cascade,
  role text not null check (role in ('user', 'assistant', 'system', 'tool')),
  content text not null,
  token_prompt int,
  token_completion int,
  model text,
  embedding vector(1536),
  meta jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists chat_messages_session_created_idx
  on public.chat_messages (session_id, created_at);

create index if not exists chat_messages_embedding_hnsw_idx
  on public.chat_messages
  using hnsw (embedding vector_cosine_ops)
  where embedding is not null;

drop trigger if exists trg_chat_messages_updated_at on public.chat_messages;
create trigger trg_chat_messages_updated_at
  before update on public.chat_messages
  for each row execute function public.set_updated_at();

-- -----------------------------------------------------------------------------
-- 6. recommendations â€” actionable items (from analysis or heuristics)
-- -----------------------------------------------------------------------------
create table if not exists public.recommendations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users (id) on delete cascade,
  analysis_id uuid references public.analyses (id) on delete set null,
  resume_id uuid references public.resumes (id) on delete set null,
  category text not null,
  title text not null,
  description text,
  priority smallint not null default 2 check (priority between 1 and 5),
  status text not null default 'pending'
    check (status in ('pending', 'accepted', 'dismissed', 'completed')),
  meta jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists recommendations_user_status_idx
  on public.recommendations (user_id, status, priority, created_at desc);

create index if not exists recommendations_analysis_idx
  on public.recommendations (analysis_id)
  where analysis_id is not null;

drop trigger if exists trg_recommendations_updated_at on public.recommendations;
create trigger trg_recommendations_updated_at
  before update on public.recommendations
  for each row execute function public.set_updated_at();

-- -----------------------------------------------------------------------------
-- 7. reports â€” generated artifacts (PDF, etc.) in Storage
-- -----------------------------------------------------------------------------
create table if not exists public.reports (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users (id) on delete cascade,
  analysis_id uuid references public.analyses (id) on delete set null,
  title text not null,
  report_type text not null default 'career_summary'
    check (report_type in ('career_summary', 'resume_review', 'interview_prep', 'custom')),
  storage_path text,
  status text not null default 'draft'
    check (status in ('draft', 'ready', 'failed')),
  meta jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists reports_user_created_idx
  on public.reports (user_id, created_at desc);

create index if not exists reports_status_idx
  on public.reports (user_id, status);

drop trigger if exists trg_reports_updated_at on public.reports;
create trigger trg_reports_updated_at
  before update on public.reports
  for each row execute function public.set_updated_at();

-- -----------------------------------------------------------------------------
-- 8. industry_benchmarks (reference percentiles; no vectors)
-- -----------------------------------------------------------------------------
create table if not exists public.industry_benchmarks (
  id uuid primary key default gen_random_uuid(),
  industry text not null,
  role_family text not null,
  metric_name text not null default 'resume_score',
  p25 smallint,
  p50 smallint not null,
  p75 smallint,
  sample_size int,
  source text,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint industry_benchmarks_percentiles check (
    p25 is null or (p25 between 0 and 100)
    and p50 between 0 and 100
    and (p75 is null or p75 between 0 and 100))
);

create index if not exists industry_benchmarks_lookup_idx
  on public.industry_benchmarks (industry, role_family, metric_name);

create unique index if not exists industry_benchmarks_industry_role_metric_uniq
  on public.industry_benchmarks (industry, role_family, metric_name);

drop trigger if exists trg_industry_benchmarks_updated_at on public.industry_benchmarks;
create trigger trg_industry_benchmarks_updated_at
  before update on public.industry_benchmarks
  for each row execute function public.set_updated_at();

-- -----------------------------------------------------------------------------
-- 9. job_postings (catalog; embeddings via backend / scripts)
-- -----------------------------------------------------------------------------
create table if not exists public.job_postings (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  description text not null,
  company_name text,
  location text,
  employment_type text,
  industry text,
  external_url text,
  is_active boolean not null default true,
  embedding vector(1536),
  meta jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists job_postings_industry_idx on public.job_postings (industry) where is_active;
create index if not exists job_postings_active_idx on public.job_postings (is_active, created_at desc);

create index if not exists job_postings_embedding_hnsw_idx
  on public.job_postings
  using hnsw (embedding vector_cosine_ops)
  where embedding is not null;

drop trigger if exists trg_job_postings_updated_at on public.job_postings;
create trigger trg_job_postings_updated_at
  before update on public.job_postings
  for each row execute function public.set_updated_at();

-- -----------------------------------------------------------------------------
-- Row Level Security â€” public tables
-- -----------------------------------------------------------------------------
alter table public.users enable row level security;
alter table public.resumes enable row level security;
alter table public.analyses enable row level security;
alter table public.chat_sessions enable row level security;
alter table public.chat_messages enable row level security;
alter table public.recommendations enable row level security;
alter table public.reports enable row level security;
alter table public.industry_benchmarks enable row level security;
alter table public.job_postings enable row level security;

-- users
drop policy if exists users_select_own on public.users;
create policy users_select_own on public.users
  for select to authenticated
  using (id = auth.uid());

drop policy if exists users_update_own on public.users;
create policy users_update_own on public.users
  for update to authenticated
  using (id = auth.uid())
  with check (id = auth.uid());

-- Inserts are performed by trigger on auth.users; optional manual backfill uses service role.

-- resumes
drop policy if exists resumes_select_own on public.resumes;
create policy resumes_select_own on public.resumes
  for select to authenticated
  using (user_id = auth.uid());

drop policy if exists resumes_insert_own on public.resumes;
create policy resumes_insert_own on public.resumes
  for insert to authenticated
  with check (user_id = auth.uid());

drop policy if exists resumes_update_own on public.resumes;
create policy resumes_update_own on public.resumes
  for update to authenticated
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

drop policy if exists resumes_delete_own on public.resumes;
create policy resumes_delete_own on public.resumes
  for delete to authenticated
  using (user_id = auth.uid());

-- analyses
drop policy if exists analyses_select_own on public.analyses;
create policy analyses_select_own on public.analyses
  for select to authenticated
  using (user_id = auth.uid());

drop policy if exists analyses_insert_own on public.analyses;
create policy analyses_insert_own on public.analyses
  for insert to authenticated
  with check (
    user_id = auth.uid()
    and exists (
      select 1 from public.resumes r
      where r.id = resume_id and r.user_id = auth.uid()
    )
  );

drop policy if exists analyses_update_own on public.analyses;
create policy analyses_update_own on public.analyses
  for update to authenticated
  using (user_id = auth.uid())
  with check (
    user_id = auth.uid()
    and exists (
      select 1 from public.resumes r
      where r.id = resume_id and r.user_id = auth.uid()
    )
  );

drop policy if exists analyses_delete_own on public.analyses;
create policy analyses_delete_own on public.analyses
  for delete to authenticated
  using (user_id = auth.uid());

-- chat_sessions
drop policy if exists chat_sessions_select_own on public.chat_sessions;
create policy chat_sessions_select_own on public.chat_sessions
  for select to authenticated
  using (user_id = auth.uid());

drop policy if exists chat_sessions_insert_own on public.chat_sessions;
create policy chat_sessions_insert_own on public.chat_sessions
  for insert to authenticated
  with check (
    user_id = auth.uid()
    and (
      resume_id is null
      or exists (
        select 1 from public.resumes r
        where r.id = resume_id and r.user_id = auth.uid()
      )
    )
  );

drop policy if exists chat_sessions_update_own on public.chat_sessions;
create policy chat_sessions_update_own on public.chat_sessions
  for update to authenticated
  using (user_id = auth.uid())
  with check (
    user_id = auth.uid()
    and (
      resume_id is null
      or exists (
        select 1 from public.resumes r
        where r.id = resume_id and r.user_id = auth.uid()
      )
    )
  );

drop policy if exists chat_sessions_delete_own on public.chat_sessions;
create policy chat_sessions_delete_own on public.chat_sessions
  for delete to authenticated
  using (user_id = auth.uid());

-- chat_messages
drop policy if exists chat_messages_select_own on public.chat_messages;
create policy chat_messages_select_own on public.chat_messages
  for select to authenticated
  using (
    exists (
      select 1 from public.chat_sessions s
      where s.id = session_id and s.user_id = auth.uid()
    )
  );

drop policy if exists chat_messages_insert_own on public.chat_messages;
create policy chat_messages_insert_own on public.chat_messages
  for insert to authenticated
  with check (
    exists (
      select 1 from public.chat_sessions s
      where s.id = session_id and s.user_id = auth.uid()
    )
  );

drop policy if exists chat_messages_update_own on public.chat_messages;
create policy chat_messages_update_own on public.chat_messages
  for update to authenticated
  using (
    exists (
      select 1 from public.chat_sessions s
      where s.id = session_id and s.user_id = auth.uid()
    )
  )
  with check (
    exists (
      select 1 from public.chat_sessions s
      where s.id = session_id and s.user_id = auth.uid()
    )
  );

drop policy if exists chat_messages_delete_own on public.chat_messages;
create policy chat_messages_delete_own on public.chat_messages
  for delete to authenticated
  using (
    exists (
      select 1 from public.chat_sessions s
      where s.id = session_id and s.user_id = auth.uid()
    )
  );

-- recommendations
drop policy if exists recommendations_select_own on public.recommendations;
create policy recommendations_select_own on public.recommendations
  for select to authenticated
  using (user_id = auth.uid());

drop policy if exists recommendations_insert_own on public.recommendations;
create policy recommendations_insert_own on public.recommendations
  for insert to authenticated
  with check (
    user_id = auth.uid()
    and (
      analysis_id is null
      or exists (
        select 1 from public.analyses a
        where a.id = analysis_id and a.user_id = auth.uid()
      )
    )
    and (
      resume_id is null
      or exists (
        select 1 from public.resumes r
        where r.id = resume_id and r.user_id = auth.uid()
      )
    )
  );

drop policy if exists recommendations_update_own on public.recommendations;
create policy recommendations_update_own on public.recommendations
  for update to authenticated
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

drop policy if exists recommendations_delete_own on public.recommendations;
create policy recommendations_delete_own on public.recommendations
  for delete to authenticated
  using (user_id = auth.uid());

-- reports
drop policy if exists reports_select_own on public.reports;
create policy reports_select_own on public.reports
  for select to authenticated
  using (user_id = auth.uid());

drop policy if exists reports_insert_own on public.reports;
create policy reports_insert_own on public.reports
  for insert to authenticated
  with check (
    user_id = auth.uid()
    and (
      analysis_id is null
      or exists (
        select 1 from public.analyses a
        where a.id = analysis_id and a.user_id = auth.uid()
      )
    )
  );

drop policy if exists reports_update_own on public.reports;
create policy reports_update_own on public.reports
  for update to authenticated
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

drop policy if exists reports_delete_own on public.reports;
create policy reports_delete_own on public.reports
  for delete to authenticated
  using (user_id = auth.uid());

-- industry_benchmarks (read-only catalog for authenticated clients)
drop policy if exists industry_benchmarks_select_auth on public.industry_benchmarks;
create policy industry_benchmarks_select_auth on public.industry_benchmarks
  for select to authenticated
  using (true);

-- job_postings (active rows readable; writes via service role / migrations only)
drop policy if exists job_postings_select_active on public.job_postings;
create policy job_postings_select_active on public.job_postings
  for select to authenticated
  using (is_active = true);

-- -----------------------------------------------------------------------------
-- Grants (Supabase roles)
-- -----------------------------------------------------------------------------
grant usage on schema public to postgres, anon, authenticated, service_role;

grant select, insert, update, delete on all tables in schema public to authenticated;
grant all on all tables in schema public to service_role;

alter default privileges in schema public
  grant select, insert, update, delete on tables to authenticated;
alter default privileges in schema public
  grant all on tables to service_role;

-- -----------------------------------------------------------------------------
-- Storage buckets: resumes, reports (private)
-- -----------------------------------------------------------------------------
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'resumes',
  'resumes',
  false,
  10485760, -- 10 MiB
  array[
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
  ]::text[]
)
on conflict (id) do update
  set public = excluded.public,
      file_size_limit = excluded.file_size_limit,
      allowed_mime_types = excluded.allowed_mime_types;

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'reports',
  'reports',
  false,
  26214400, -- 25 MiB
  array['application/pdf']::text[]
)
on conflict (id) do update
  set public = excluded.public,
      file_size_limit = excluded.file_size_limit,
      allowed_mime_types = excluded.allowed_mime_types;

-- Storage RLS: object key must start with "<uid>/"
-- Example paths: "<uid>/resumes/2026/cv.pdf", "<uid>/reports/summary.pdf"

drop policy if exists storage_resumes_select_own on storage.objects;
create policy storage_resumes_select_own on storage.objects
  for select to authenticated
  using (
    bucket_id = 'resumes'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

drop policy if exists storage_resumes_insert_own on storage.objects;
create policy storage_resumes_insert_own on storage.objects
  for insert to authenticated
  with check (
    bucket_id = 'resumes'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

drop policy if exists storage_resumes_update_own on storage.objects;
create policy storage_resumes_update_own on storage.objects
  for update to authenticated
  using (
    bucket_id = 'resumes'
    and (storage.foldername(name))[1] = auth.uid()::text
  )
  with check (
    bucket_id = 'resumes'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

drop policy if exists storage_resumes_delete_own on storage.objects;
create policy storage_resumes_delete_own on storage.objects
  for delete to authenticated
  using (
    bucket_id = 'resumes'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

drop policy if exists storage_reports_select_own on storage.objects;
create policy storage_reports_select_own on storage.objects
  for select to authenticated
  using (
    bucket_id = 'reports'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

drop policy if exists storage_reports_insert_own on storage.objects;
create policy storage_reports_insert_own on storage.objects
  for insert to authenticated
  with check (
    bucket_id = 'reports'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

drop policy if exists storage_reports_update_own on storage.objects;
create policy storage_reports_update_own on storage.objects
  for update to authenticated
  using (
    bucket_id = 'reports'
    and (storage.foldername(name))[1] = auth.uid()::text
  )
  with check (
    bucket_id = 'reports'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

drop policy if exists storage_reports_delete_own on storage.objects;
create policy storage_reports_delete_own on storage.objects
  for delete to authenticated
  using (
    bucket_id = 'reports'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

-- -----------------------------------------------------------------------------
-- Sample seed data (runs only when at least one auth user exists)
-- -----------------------------------------------------------------------------
do $$
declare
  demo_user_id uuid;
  demo_resume_id uuid;
  demo_analysis_id uuid;
  demo_session_id uuid;
begin
  select id into demo_user_id from auth.users order by created_at asc limit 1;
  if demo_user_id is null then
    raise notice 'MyCareer AI seed: skipped (no rows in auth.users). Create a user first.';
    return;
  end if;

  if exists (
    select 1 from public.resumes r
    where r.user_id = demo_user_id and r.meta->>'source' = 'seed'
  ) then
    raise notice 'MyCareer AI seed: skipped (already present for this user).';
    return;
  end if;

  insert into public.users (id, email, display_name)
  select id, email, coalesce(raw_user_meta_data->>'display_name', split_part(email, '@', 1))
  from auth.users
  where id = demo_user_id
  on conflict (id) do nothing;

  insert into public.resumes (
    user_id,
    original_filename,
    mime_type,
    file_size_bytes,
    storage_path,
    parsing_status,
    parsed_text,
    meta
  )
  values (
    demo_user_id,
    'demo-resume.pdf',
    'application/pdf',
    102400,
    demo_user_id::text || '/resumes/seed/demo-resume.pdf',
    'ready',
    'Demo Candidate' || chr(10) || 'Skills: Python, PostgreSQL, FastAPI' || chr(10)
      || 'Experience: Built AI career guidance APIs and RLS-aware schemas.',
    '{"source":"seed"}'::jsonb
  )
  returning id into demo_resume_id;

  insert into public.analyses (
    user_id,
    resume_id,
    analysis_version,
    model,
    prompt_version,
    summary,
    findings,
    scores
  )
  values (
    demo_user_id,
    demo_resume_id,
    1,
    'gpt-4o-mini',
    'v1',
    'Strong backend focus; add quantified impact on recent roles.',
    '{"strengths":["API design","data modeling"],"gaps":["metrics","leadership examples"]}'::jsonb,
    '{"ats_fit":0.72,"clarity":0.81}'::jsonb
  )
  returning id into demo_analysis_id;

  insert into public.recommendations (
    user_id,
    analysis_id,
    resume_id,
    category,
    title,
    description,
    priority,
    status
  )
  values (
    demo_user_id,
    demo_analysis_id,
    demo_resume_id,
    'structure',
    'Add metrics to your impact bullets',
    'Recruiters scan for numbers. Add at least one quantified outcome per role.',
    2,
    'pending'
  );

  insert into public.chat_sessions (user_id, resume_id, title, meta)
  values (
    demo_user_id,
    demo_resume_id,
    'Seed: career coaching',
    '{"source":"seed"}'::jsonb
  )
  returning id into demo_session_id;

  insert into public.chat_messages (session_id, role, content, meta)
  values
    (demo_session_id, 'user', 'How should I improve my resume for backend roles?', '{"source":"seed"}'::jsonb),
    (demo_session_id, 'assistant', 'Lead with impact: add metrics, name key systems, and align keywords with target job descriptions.', '{"source":"seed"}'::jsonb);

  insert into public.reports (
    user_id,
    analysis_id,
    title,
    report_type,
    storage_path,
    status,
    meta
  )
  values (
    demo_user_id,
    demo_analysis_id,
    'Sample career summary (placeholder PDF path)',
    'career_summary',
    demo_user_id::text || '/reports/seed/career-summary.pdf',
    'draft',
    '{"source":"seed"}'::jsonb
  );

  raise notice 'MyCareer AI seed: inserted demo rows for user %', demo_user_id;
end $$;

-- =============================================================================
-- STORAGE SETUP (manual checklist - buckets and policies are created above)
-- =============================================================================
-- 1. Buckets `resumes` and `reports` are private, with file size and MIME limits.
-- 2. Object keys MUST start with the owning user id (first path segment):
--      resumes:  "<uuid>/..." e.g. "<uuid>/uploads/2026/cv.pdf"
--      reports:  "<uuid>/..." e.g. "<uuid>/exports/summary.pdf"
-- 3. Client upload (browser, anon key + user session):
--      const path = `${user.id}/uploads/${file.name}`;
--      await supabase.storage.from('resumes').upload(path, file, { upsert: false });
-- 4. For downloads, prefer signed URLs from an Edge Function or FastAPI using
--    the service role; never ship the service role key to the client.
-- 5. Keep `public.resumes.storage_path` and `public.reports.storage_path` equal
--    to the Storage object key you stored.
-- 6. Policies use storage.foldername(name)[1] = auth.uid()::text; if uploads
--    fail, verify the JWT is present and the path prefix matches auth.uid().
-- =============================================================================

