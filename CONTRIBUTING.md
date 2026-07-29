# Contributing to MyCareer AI

Thank you for your interest in contributing. This project welcomes bug reports, documentation improvements, and focused feature PRs that align with the roadmap.

## Getting started

1. Fork the repository and clone your fork.
2. Follow the setup steps in [README.md](./README.md) (Supabase, env files, local dev).
3. Create a branch from `main`: `git checkout -b fix/short-description` or `feat/short-description`.

## Development workflow

### Backend (FastAPI)

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
```

### Frontend (Next.js)

```bash
cd frontend
npm install
npm run lint
npm test
npm run build
```

## Pull request guidelines

- Keep PRs focused — one logical change per PR.
- Include tests for bug fixes and non-trivial features.
- Update README or `docs/` when behavior or setup changes.
- Fill out the [pull request template](.github/pull_request_template.md).
- Ensure CI passes before requesting review.

## Code style

- **Python**: Follow existing patterns in `backend/app/`; type hints encouraged.
- **TypeScript/React**: ESLint + Next.js conventions; use existing UI components in `frontend/src/components/ui/`.
- **Commits**: Use clear, imperative messages (e.g. `fix: handle empty resume upload`).

## Reporting issues

Use the [bug report](.github/ISSUE_TEMPLATE/bug_report.yml) or [feature request](.github/ISSUE_TEMPLATE/feature_request.yml) templates. Do not include API keys, JWTs, or real resume content in issues.

## Security

Report vulnerabilities privately — see [SECURITY.md](./SECURITY.md).

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](./LICENSE).
