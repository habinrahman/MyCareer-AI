-- MyCareer AI — dedupe historical rows + integrity indexes (no-login V1 safe).
-- Run in Supabase SQL Editor after backups, or via migration runner.
-- ``analyses`` already has ``analyses_resume_version_uniq`` on (resume_id, analysis_version).

-- -----------------------------------------------------------------------------
-- 1) Remove duplicate resumes (same user + storage_path), keep oldest ctid
-- -----------------------------------------------------------------------------
DELETE FROM public.resumes r
WHERE r.storage_path IS NOT NULL
  AND r.ctid NOT IN (
    SELECT MIN(r2.ctid)
    FROM public.resumes r2
    WHERE r2.storage_path IS NOT NULL
    GROUP BY r2.user_id, r2.storage_path
  );

-- -----------------------------------------------------------------------------
-- 2) Remove duplicate analyses (same resume + version), keep oldest ctid
-- -----------------------------------------------------------------------------
DELETE FROM public.analyses a
WHERE a.ctid NOT IN (
  SELECT MIN(a2.ctid)
  FROM public.analyses a2
  GROUP BY a2.resume_id, a2.analysis_version
);

-- -----------------------------------------------------------------------------
-- 3) At most one report row per analysis_id (when analysis_id is set)
-- -----------------------------------------------------------------------------
DELETE FROM public.reports r
WHERE r.analysis_id IS NOT NULL
  AND r.ctid NOT IN (
    SELECT MIN(r2.ctid)
    FROM public.reports r2
    WHERE r2.analysis_id IS NOT NULL
    GROUP BY r2.analysis_id
  );

-- -----------------------------------------------------------------------------
-- 4) Unique: one resume row per (user_id, storage_path) when path is not null
-- -----------------------------------------------------------------------------
CREATE UNIQUE INDEX IF NOT EXISTS resumes_user_storage_path_unique
  ON public.resumes (user_id, storage_path)
  WHERE storage_path IS NOT NULL;

-- -----------------------------------------------------------------------------
-- 5) Unique: one report per analysis (nullable analysis_id still allowed multiple NULLs)
-- -----------------------------------------------------------------------------
CREATE UNIQUE INDEX IF NOT EXISTS reports_one_row_per_analysis_id
  ON public.reports (analysis_id)
  WHERE analysis_id IS NOT NULL;
