-- Public resume PDF download lead capture (MicroDegree / MyCareer AI)
-- Run after prior migrations. Backend also inserts via service role (bypasses RLS).

create table if not exists public.resume_download_leads (
  id uuid primary key default gen_random_uuid(),
  full_name text not null,
  email text not null,
  phone text not null,
  analysis_id uuid,
  created_at timestamptz not null default now(),
  constraint resume_download_leads_full_name_len check (char_length(trim(full_name)) >= 2),
  constraint resume_download_leads_email_len check (char_length(email) <= 320),
  constraint resume_download_leads_phone_len check (char_length(phone) between 8 and 32)
);

create index if not exists resume_download_leads_created_at_idx
  on public.resume_download_leads (created_at desc);

create index if not exists resume_download_leads_email_idx
  on public.resume_download_leads (email);

alter table public.resume_download_leads enable row level security;

drop policy if exists resume_download_leads_public_insert on public.resume_download_leads;
create policy resume_download_leads_public_insert on public.resume_download_leads
  for insert to anon, authenticated
  with check (true);

-- No SELECT for anon/authenticated (reads via service role / SQL editor only).
grant insert on public.resume_download_leads to anon, authenticated;
