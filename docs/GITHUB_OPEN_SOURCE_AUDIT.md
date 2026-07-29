# GitHub Open Source Audit — habinrahman

**Profile:** [github.com/habinrahman](https://github.com/habinrahman)  
**Audit date:** 2026-07-29  
**Public repositories:** 21  
**Followers:** 2 | **Following:** 10

---

## Executive summary

Your profile has **strong project depth** (especially `AI-CSV-IMPORTER`, `rls-inspector`, `Foundry`) but **low discoverability signals**: 0 stars across all repos, minimal CI, almost no releases, and missing issue/PR templates on most projects.

A recent bulk commit added LICENSE / CONTRIBUTING / SECURITY / CODE_OF_CONDUCT / CHANGELOG / dependabot to nearly every repo — good foundation, but many READMEs, workflows, and templates still need **substance** (not just file presence).

**Priority order for maximum impact:**

1. **MyCareer-AI** + **AI-CSV-IMPORTER** + **rls-inspector** — flagship, star-worthy, unique value
2. **competition-tracker**, **FinGuard**, **microdegree-outreach-platform** — production narratives
3. Archive or merge duplicates: `certificate-verification` vs `CertificationVerification-V2`, stale `SWEETGALORE`
4. Profile README (`habinrahman/habinrahman`) — already good; add featured pinned repos + metrics
5. External contributions (Pull Shark) — target FastAPI, Supabase, Next.js ecosystems

---

## Phase 1 — Per-repository audit

Legend: ✅ present & adequate | ⚠️ present but weak | ❌ missing | 🔸 partial

| Repository | README | CI | Releases | Topics | Issue tmpl | PR tmpl | Tests | Demo/GIF | Priority |
|------------|--------|-----|----------|--------|------------|---------|-------|----------|----------|
| **AI-CSV-IMPORTER** | ✅ 78KB | ✅ 3 workflows | ✅ v0.1 | ✅ 17 | ✅ 3 | ❌ | ✅ vitest+e2e | ⚠️ | P0 flagship |
| **rls-inspector** | ✅ 27KB | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️ | ❌ | P0 — unique Supabase tool |
| **MyCareer-AI** | ⚠️ 10KB | ❌→✅ local | ❌ | ✅ 12 | ❌→✅ local | ❌→✅ local | ✅ pytest+jest | ❌ | P0 — upgraded locally |
| **competition-tracker** | ✅ 17KB | ❌ | ❌ | ✅ 10 | ❌ | ❌ | ❌ | ❌ | P1 |
| **Foundry** | ✅ 45KB | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️ | ❌ | P1 |
| **microdegree-outreach** | ✅ 34KB | ✅ 2 | ✅ 1 | ✅ 11 | ❌ | ❌ | ✅ | ❌ | P1 |
| **FinGuard** | ✅ 16KB | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️ | ❌ | P2 |
| **AI-Job-Application-Tracker** | ✅ 16KB | ❌ | ❌ | ✅ 10 | ❌ | ❌ | ⚠️ | ❌ | P2 |
| **Ollive-Inference-Platform** | ✅ 24KB | ❌ | ❌ | ✅ 11 | ❌ | ❌ | ⚠️ | ❌ | P2 |
| **hybrid-llm-survival** | ✅ 10KB | ❌ | ❌ | ✅ 8 | ❌ | ❌ | ⚠️ | ❌ | P2 |
| **AI-Intruder-Detection** | ✅ 12KB | ❌ | ❌ | ✅ 9 | ❌ | ❌ | ❌ | ❌ | P3 |
| **certificate-verification** | ⚠️ 2KB | ❌ | ✅ 3 | ✅ 11 | ❌ | ❌ | ❌ | ❌ | P2 merge w/ V2 |
| **CertificationVerification-V2** | ✅ 44KB | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️ | ❌ | P2 — canonical? |
| **habinrahman** (profile) | ✅ 11KB | ✅ snake | ❌ | ✅ 11 | ❌ | ❌ | n/a | n/a | P0 profile |
| **habin-portfolio** | ⚠️ 1.4KB | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | P2 |
| **online-bookstore** | ⚠️ 3KB | ❌ | ❌ | ✅ 14 | ❌ | ❌ | ❌ | ❌ | P3 |
| **FLUTTER-QUIZ-APP** | ⚠️ 4KB | ❌ | ❌ | ✅ 10 | ❌ | ❌ | ❌ | ❌ | P3 |
| **ORYX** | ⚠️ 4.6KB | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | P3 |
| **dynamo-log-report-fixed** | ❌ no README | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️ | ❌ | P4 niche |
| **openclaw-appplatform-clean** | ✅ 16KB | ✅ 2 | ❌ | ❌ | ❌ | ❌ | ⚠️ | ❌ | P3 |
| **SWEETGALORE** | ❌ no README | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | P4 archive? |

### Cross-cutting gaps (18/21 repos)

| Item | Status |
|------|--------|
| LICENSE | ⚠️ Bulk-added; verify SPDX (some show "Other") |
| CONTRIBUTING.md | ⚠️ Present; needs repo-specific content |
| CODE_OF_CONDUCT.md | ⚠️ Present (likely template) |
| SECURITY.md | ⚠️ Present; enable private reporting in repo settings |
| CHANGELOG.md | ⚠️ Present; mostly empty |
| GitHub Actions CI | ❌ Only 4/21 repos have workflows |
| Issue templates | ❌ Only AI-CSV-IMPORTER (3 templates) |
| PR templates | ❌ None detected |
| Semantic releases | ❌ Only 3 repos have releases |
| Social preview images | ❌ Not configured (Settings → Social preview) |
| Dependabot | ⚠️ yml present; verify alerts enabled in Security tab |
| Code scanning | ❌ Not enabled |
| Secret scanning | ⚠️ Enable on all public repos |
| Discussions | ❌ Not enabled on flagship repos |
| Hero images / GIF demos | ❌ Missing on most |
| Architecture diagrams | ⚠️ MyCareer-AI, AI-CSV-IMPORTER have mermaid |

---

## Phase 2–4 — Implementation status (MyCareer-AI local)

**Why:** MyCareer-AI is your most marketable full-stack AI SaaS. Production-quality OSS here drives **Starstruck**, **Open Sourcerer**, and recruiter discoverability.

**Expected impact:** Green CI badge, MIT license clarity, contributor onboarding, Dependabot PRs (activity signal), release tags for changelog discipline.

**Implemented locally** (push to `habinrahman/MyCareer-AI`):

- `LICENSE` (MIT)
- `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `CHANGELOG.md`
- `.github/workflows/ci.yml` — backend pytest, frontend lint/test/build, Docker build on main
- `.github/workflows/release.yml` — tag-triggered releases
- `.github/dependabot.yml` — pip, npm, github-actions
- Issue templates (bug, feature) + PR template
- README: badges, features table, FAQ, roadmap, screenshots placeholder

**Next for MyCareer-AI:**

1. Fix git remote: local points to deleted `mycareer-ai-intelligence` → set to `MyCareer-AI`
2. Record demo GIF → `docs/assets/resume-analysis-demo.gif`
3. Enable GitHub Discussions
4. Tag `v0.1.0` release with notes from CHANGELOG
5. Add repo social preview image (1280×640)
6. Pin on profile alongside AI-CSV-IMPORTER and rls-inspector

---

## Phase 5 — Star-worthy content plan

### MyCareer-AI launch narrative

**Blog post (Dev.to / Hashnode):**  
_"Building a production resume intelligence stack with FastAPI, pgvector, and OpenAI structured outputs"_

**Hacker News (Show HN):**  
Lead with the **public resume analyzer** — instant value without signup. Link to live demo when hosted.

**Reddit:**  
r/SideProject, r/FastAPI, r/nextjs — focus on architecture decisions (SSE chat, Supabase RLS, TLS pooler quirks documented in README).

**LinkedIn:**  
Short video/GIF of upload → analysis → chat flow. Tag #FastAPI #NextJS #OpenAI #CareerTech.

### rls-inspector (high star potential)

Unique niche — **Supabase RLS debugging** has active community demand. Add:
- 60-second demo GIF
- "5 RLS mistakes this catches" blog post
- Submit to Supabase community Discord / awesome-supabase lists

### AI-CSV-IMPORTER (already excellent)

- Submit to Product Hunt / awesome-llm-apps
- Write "semantic CSV mapping vs hardcoded columns" comparison post
- Already has release + CI — **pin this repo first**

---

## Phase 6 — Pull Shark opportunities

Verified `good first issue` / beginner-friendly targets aligned with your stack:

| Repo | Issue | Why it fits |
|------|-------|-------------|
| [fastapi/fastapi](https://github.com/fastapi/fastapi/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) | Docs / typing fixes | Your core backend stack |
| [tiangolo/full-stack-fastapi-template](https://github.com/tiangolo/full-stack-fastapi-template) | Maintenance PRs | Same architecture pattern |
| [supabase/supabase](https://github.com/supabase/supabase/issues?q=good+first+issue) | Docs, CLI, examples | You use Supabase heavily |
| [vercel/next.js](https://github.com/vercel/next.js/issues?q=good+first+issue+label%3A%22good+first+issue%22) | Docs typos, small fixes | Frontend stack |
| [bundlab/job-application-tracker#1](https://github.com/bundlab/job-application-tracker/issues/1) | Return HTTP 201 on create | Tiny, clean FastAPI fix — **Quickdraw candidate** |
| [alencheung/hkgov-rethink#6](https://github.com/alencheung/hkgov-rethink/issues/6) | Async Python client | Matches your async FastAPI experience |

**Process for each PR:**

1. Read CONTRIBUTING + existing code style
2. Reproduce issue locally
3. Fix with test
4. One focused commit, conventional title
5. Link issue in PR body

---

## Phase 7 — Pair Extraordinaire

Use `Co-authored-by:` only when pairing live (mob session, hackathon, mentor review). Example:

```
fix: normalize resume MIME validation

Co-authored-by: Jane Doe <jane@example.com>
```

---

## Phase 8 — Quickdraw

Appropriate micro-PRs (documentation typos, HTTP status codes, missing type hints) on active repos. **Avoid** drive-by one-character changes on inactive projects.

Good candidates:
- bundlab/job-application-tracker#1 (HTTP 201)
- FastAPI docstring/typo fixes with linked issue

---

## Phase 9 — Galaxy Brain

Discussions where your experience adds real value:

- **Supabase**: RLS policy patterns, pooler + asyncpg TLS
- **FastAPI**: JWT + Supabase auth, SSE streaming, SlowAPI rate limits
- **OpenAI**: Structured outputs for resume parsing
- **Next.js**: App Router + Supabase SSR middleware

Search: `org:supabase RLS`, `fastapi supabase jwt`, `pgvector job matching`

Only answer when you can cite working code from your repos.

---

## Phase 10 — Profile README improvements

Current profile README is **strong** (typing SVG, badges, project cards). Enhancements:

- [ ] Pin top 3: AI-CSV-IMPORTER, rls-inspector, MyCareer-AI
- [ ] Add GitHub stats cards (github-readme-stats — already may exist, verify)
- [ ] Featured projects section with star badges (updates automatically)
- [ ] Add `location` and `twitter`/X on GitHub profile settings
- [ ] Link LinkedIn prominently (already in README)
- [ ] Add "Currently building: …" dynamic line
- [ ] Visitor counter (optional — some find it dated)

---

## Phase 11 — Releases roadmap

| Repo | Suggested tag | Notes |
|------|---------------|-------|
| MyCareer-AI | v0.1.0 | After CI push + GIF |
| rls-inspector | v0.1.0 | First public stable |
| competition-tracker | v0.1.0 | After CI added |
| Foundry | v0.1.0 | After license normalized |
| AI-CSV-IMPORTER | v0.2.0 | Already has v0.1 |

Use conventional commits + CHANGELOG.md + git tag → GitHub Release workflow.

---

## Phase 12 — Security checklist (all repos)

In each repo **Settings → Security**:

- [ ] Dependabot alerts: **Enable**
- [ ] Dependabot security updates: **Enable**
- [ ] Secret scanning: **Enable** (public repos)
- [ ] Code scanning (CodeQL): Add workflow
- [ ] Private vulnerability reporting: **Enable**

Add CodeQL workflow template to flagship repos.

---

## Phase 13 — CI/CD template rollout

Copy MyCareer-AI CI pattern to repos by stack:

| Stack | Workflow jobs |
|-------|----------------|
| Python/FastAPI | pytest, ruff/black optional |
| Node/Next.js | lint, test, build |
| Monorepo | matrix per workspace |
| Docker | build-push on tags only |

Repos needing CI first: **rls-inspector**, **Foundry**, **competition-tracker**, **FinGuard**.

---

## Phase 14 — Community presence

**Follow / learn from:**
- @tiangolo (FastAPI), @supabase, @vercel
- Maintainers of awesome-supabase, awesome-fastapi lists

**Organizations / programs:**
- GitHub Open Source Friday
- Supabase Launch Week community events
- Local DevRel meetups (Bangalore/India tech community)

**Hackathons:**
- GitHub Universe challenges
- Supabase hackathons
- AI Engineer World's Fair community tracks

---

## Duplicate / cleanup recommendations

1. **certificate-verification** + **CertificationVerification-V2** → pick V2 as canonical, archive the other with README redirect
2. **SWEETGALORE** → archive or add minimal README + purpose statement
3. **dynamo-log-report-fixed** → add README explaining Terminal-Bench context or archive
4. **Local mycareer_ai remote** → update to `https://github.com/habinrahman/MyCareer-AI.git`

---

## Achievement mapping

| Achievement | How to earn (authentically) |
|-------------|----------------------------|
| **Starstruck** | Ship rls-inspector + AI-CSV-IMPORTER quality; launch posts; get 16+ stars on one repo |
| **Pull Shark** | 2 merged PRs on external repos (start with bundlab, fastapi docs) |
| **Quickdraw** | Merge a valid micro-PR within 5 min of opening (maintainer must merge fast) |
| **Pair Extraordinaire** | Co-authored commits on hackathon/pairing sessions |
| **Galaxy Brain** | Accepted answers in Discussions (2+) |
| **Open Sourcerer** | Consistent public OSS with CI, releases, docs — you're building toward this |

---

## Immediate action items

1. **Push MyCareer-AI upgrades** from local workspace
2. **Pin 3 repos** on GitHub profile
3. **Add CI to rls-inspector** (highest star potential after CSV importer)
4. **Record one demo GIF** for MyCareer-AI
5. **Submit first external PR** (job-application-tracker #1 or FastAPI docs)
6. **Enable security features** on all public repos
7. **Tag v0.1.0** on MyCareer-AI after CI green
