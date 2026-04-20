-- Public PDF flow often has no persisted analysis row; optional analysis_id should not require FK.
alter table public.resume_download_leads
  drop constraint if exists resume_download_leads_analysis_id_fkey;
