# MyCareer AI — Windows setup (PowerShell)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "==> MyCareer AI setup" -ForegroundColor Cyan

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example — edit with your values."
} else {
    Write-Host "Skipping root .env (already exists)."
}

if (-not (Test-Path "backend\.env")) {
    Copy-Item "backend\.env.example" "backend\.env"
    Write-Host "Created backend\.env from backend\.env.example"
} else {
    Write-Host "Skipping backend\.env (already exists)."
}

if (-not (Test-Path "frontend\.env.local")) {
    Copy-Item "frontend\.env.example" "frontend\.env.local"
    Write-Host "Created frontend\.env.local from frontend\.env.example"
} else {
    Write-Host "Skipping frontend\.env.local (already exists)."
}

if (-not (Test-Path "backend\.venv")) {
    python -m venv backend\.venv
    Write-Host "Created backend\.venv"
}

& "backend\.venv\Scripts\python.exe" -m pip install -r backend\requirements.txt

Set-Location frontend
npm install
Set-Location $Root

Write-Host ""
Write-Host "Done. Next:"
Write-Host "  1. Run supabase/migrations/0001_init.sql in your Supabase SQL editor."
Write-Host "  2. Fill backend\.env and frontend\.env.local."
Write-Host "  3. Terminal A: cd backend; .\.venv\Scripts\Activate.ps1; uvicorn app.main:app --reload"
Write-Host "  4. Terminal B: cd frontend; npm run dev"
