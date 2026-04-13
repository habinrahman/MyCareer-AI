# Careers module — student resume intelligence

This document describes the **industry benchmarking** and **AI job matching** (pgvector + OpenAI `text-embedding-3-small`) APIs for MyCareer AI. The platform is **student-centric**: it helps learners analyze resumes, compare scores to benchmarks, and explore example roles for skill development—not recruitment or placement.

## Prerequisites

1. **PostgreSQL + pgvector** (Supabase includes the `vector` extension).
2. **Schema**: run `supabase/migrations/0002_careers_benchmarks_jobs_recruiter.sql` (benchmarks + job postings) on an existing project, then `supabase/migrations/0003_remove_recruiter_student_platform.sql` if upgrading from a database that had recruiter-related columns. For a greenfield install, prefer the current `supabase/schema.sql`.
3. **Seed** (optional): `supabase/seed/careers_seed.sql` for reference benchmarks and sample job postings.
4. **Backend**: `OPENAI_API_KEY`, `DATABASE_URL` (async SQLAlchemy URL), and existing Supabase JWT settings. The API uses the same DB role as other routes; that role typically **bypasses Row Level Security (RLS)**, so job embedding writes are performed server-side only.
5. **RLS**: `industry_benchmarks` and `job_postings` allow **SELECT** for `authenticated` clients; **writes** to job postings are intended for **service role** / migrations / backend (no insert policy for authenticated on those catalog tables).

## Database objects

| Object | Purpose |
|--------|---------|
| `industry_benchmarks` | Reference percentiles (`p25`, `p50`, `p75`) per industry / role family. |
| `job_postings` | Job catalog with optional `embedding vector(1536)` and HNSW index for cosine distance (used for student learning insights). |

## HTTP API (FastAPI)

Base URL: same as the rest of the API (e.g. `http://localhost:8000`). All routes require `Authorization: Bearer <Supabase access token>`.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/careers/me` | Student workspace marker (`role: student`). |
| PATCH | `/careers/me` | No-op body reserved for future preferences; ensures the user row exists. |
| GET | `/careers/benchmarks` | Query: `industry`, `role_family`, `resume_id`, `metric_name` — compares latest analysis `scores.resume_score` to benchmarks. |
| POST | `/careers/jobs/match` | Body: `{ "resume_id": null, "limit": 12, "backfill_job_embeddings": true }` — embeds missing job rows via OpenAI, then vector search for learning-oriented matches. |

## Frontend

The Next.js app exposes **`/careers`** (authenticated shell): student dashboard copy, link to **Account** settings, **AI mentor** entry point, benchmarking panel, and job match action (described as learning insights, not hiring).

Configure **`NEXT_PUBLIC_API_URL`** to your FastAPI origin.

## Docker

No extra containers are required. Apply SQL migrations against the same Postgres instance referenced by `DATABASE_URL` in the API container.

## Operational notes

- **Embeddings**: Job rows may ship without vectors in seed SQL; the first `/careers/jobs/match` with `backfill_job_embeddings: true` fills `job_postings.embedding` using `text-embedding-3-small`.
- **Privacy**: Job matching returns posting metadata and similarity scores only; it does not expose other users’ resumes.
