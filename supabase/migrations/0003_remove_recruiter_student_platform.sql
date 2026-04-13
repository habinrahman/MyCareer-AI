-- MyCareer AI — remove recruitment/placement columns and legacy recruiter tables.
-- Safe to run on existing databases that applied 0002 (or schema.sql versions that included these objects).
-- Preserves: resumes, analyses, job_postings, industry_benchmarks, reports, chat_*.

-- Drop policies that might reference recruiter-only tables (names are illustrative; IF EXISTS is safe).
DROP POLICY IF EXISTS recruiter_reports_select_own ON public.recruiter_reports;
DROP POLICY IF EXISTS recruiter_reports_insert_service ON public.recruiter_reports;
DROP POLICY IF EXISTS recruiter_rankings_select_own ON public.recruiter_rankings;
DROP POLICY IF EXISTS recruiter_insights_select_own ON public.recruiter_insights;

DROP TABLE IF EXISTS public.recruiter_reports CASCADE;
DROP TABLE IF EXISTS public.recruiter_rankings CASCADE;
DROP TABLE IF EXISTS public.recruiter_insights CASCADE;

ALTER TABLE public.users
  DROP COLUMN IF EXISTS account_type;

ALTER TABLE public.users
  DROP COLUMN IF EXISTS opt_in_recruiter_matching;
