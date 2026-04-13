-- Seed industry benchmarks and sample job postings (embeddings null until backend script).
-- Run in Supabase SQL Editor after migrations, or: psql ... -f careers_seed.sql

insert into public.industry_benchmarks (industry, role_family, metric_name, p25, p50, p75, sample_size, source, notes)
values
  ('Software', 'Backend Engineer', 'resume_score', 62, 74, 86, 1200, 'MyCareer AI composite', 'Typical applicant pool — illustrative'),
  ('Software', 'Full Stack', 'resume_score', 60, 72, 84, 980, 'MyCareer AI composite', null),
  ('Software', 'Data Engineer', 'resume_score', 64, 76, 88, 640, 'MyCareer AI composite', null),
  ('Software', 'DevOps / SRE', 'resume_score', 63, 75, 87, 520, 'MyCareer AI composite', null),
  ('all', 'General IC', 'resume_score', 58, 70, 82, 5000, 'MyCareer AI composite', 'Cross-industry baseline')
on conflict (industry, role_family, metric_name) do update set
  p25 = excluded.p25,
  p50 = excluded.p50,
  p75 = excluded.p75,
  sample_size = excluded.sample_size,
  source = excluded.source,
  notes = excluded.notes,
  updated_at = now();

insert into public.job_postings (title, description, company_name, location, employment_type, industry, external_url, is_active)
select v.title, v.description, v.company_name, v.location, v.employment_type, v.industry, v.external_url, v.is_active
from (
  values
    (
      'Senior Backend Engineer (Python)',
      'Design and ship APIs with FastAPI, PostgreSQL, and async workers. Experience with pgvector and OpenAI integrations preferred.',
      'Example Corp',
      'Remote (US)',
      'full_time',
      'Software',
      'https://example.com/jobs/backend-senior',
      true
    ),
    (
      'ML Engineer — Retrieval & Ranking',
      'Build embedding pipelines, vector indexes, and ranking models. Strong Python and SQL required.',
      'Example Labs',
      'Hybrid — NYC',
      'full_time',
      'Software',
      'https://example.com/jobs/ml-ranking',
      true
    ),
    (
      'Platform Engineer',
      'Kubernetes, Terraform, CI/CD, observability. Mentor junior engineers and drive reliability.',
      'Example Cloud',
      'Remote (EU)',
      'full_time',
      'Software',
      'https://example.com/jobs/platform',
      true
    )
) as v(title, description, company_name, location, employment_type, industry, external_url, is_active)
where not exists (
  select 1 from public.job_postings j where j.title = v.title and j.company_name = v.company_name
);
