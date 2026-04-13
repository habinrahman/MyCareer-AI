-- MyCareer AI — industry benchmarks and job catalog (pgvector)
-- Run after 0001_init / schema.sql. Service role bypasses RLS for backend writes.
-- (Recruiter-specific user columns were removed; use 0003_remove_recruiter_student_platform.sql on legacy DBs.)

-- -----------------------------------------------------------------------------
-- Industry benchmarks (reference rows; no vectors)
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
-- Job postings (catalog for vector match; embeddings filled by backend script)
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
-- Row Level Security
-- -----------------------------------------------------------------------------
alter table public.industry_benchmarks enable row level security;
alter table public.job_postings enable row level security;

drop policy if exists industry_benchmarks_select_auth on public.industry_benchmarks;
create policy industry_benchmarks_select_auth on public.industry_benchmarks
  for select to authenticated
  using (true);

drop policy if exists job_postings_select_active on public.job_postings;
create policy job_postings_select_active on public.job_postings
  for select to authenticated
  using (is_active = true);

-- No insert/update/delete for authenticated on catalog tables (service role only).
