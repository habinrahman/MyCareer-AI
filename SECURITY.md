# Security Policy

## Supported versions

| Version | Supported          |
| ------- | ------------------ |
| main    | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a vulnerability

**Please do not open public GitHub issues for security vulnerabilities.**

Instead, report them by emailing the maintainer via the contact listed on [https://github.com/habinrahman](https://github.com/habinrahman) or through GitHub's private vulnerability reporting (if enabled on the repository).

Include:

- Description of the vulnerability and impact
- Steps to reproduce
- Affected endpoints or components
- Suggested fix (if any)

We aim to acknowledge reports within **72 hours** and provide a remediation timeline when possible.

## Security practices in this project

- Supabase JWT verification on protected FastAPI routes
- Service role and OpenAI keys are server-side only
- Rate limiting on upload, chat, and lead capture endpoints
- Row Level Security (RLS) recommended on all user tables
- File upload validation (type/size) for resumes
- TLS enforced for Postgres in staging/production

## Scope

The following are generally **out of scope** for security reports:

- Missing security headers without a demonstrated exploit
- Social engineering
- Denial-of-service without a practical attack path at default rate limits
- Issues in third-party services (Supabase, OpenAI, Vercel) — report those to the respective vendors
