-- MyCareer AI — read-only checks for Supabase SQL Editor
-- Run after applying schema.sql. Expects one row per table name listed.

select table_name
from information_schema.tables
where table_schema = 'public'
  and table_name in (
    'users',
    'resumes',
    'analyses',
    'chat_sessions',
    'chat_messages',
    'recommendations',
    'reports'
  )
order by table_name;

-- pgvector extension
select extname, extversion from pg_extension where extname = 'vector';
