"""
Environment and dependency diagnostic (no secrets printed).

Run from repo root or backend; always switches CWD to this file's directory so
``backend/.env`` is picked up by Pydantic settings.

  Windows: .\\venv\\Scripts\\python.exe test_env.py
  Unix:    ./venv/bin/python test_env.py
"""

from __future__ import annotations

import os
import socket
import ssl
import sys
from pathlib import Path
from urllib.parse import urlparse

_BACKEND = Path(__file__).resolve().parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


def _backend_dir() -> Path:
    return _BACKEND


def _redact_database_url(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.hostname or "?"
    port = parsed.port or ("5432" if "postgres" in (parsed.scheme or "") else "")
    db = (parsed.path or "").lstrip("/") or "?"
    scheme = parsed.scheme or "?"
    return f"{scheme}://**:*@{host}:{port}/{db}"


def main() -> int:
    os.chdir(_backend_dir())

    print("Python:", sys.version.replace("\n", " "))
    print("Executable:", sys.executable)
    print("OpenSSL:", ssl.OPENSSL_VERSION)
    try:
        import certifi

        print("certifi:", certifi.where())
    except ImportError:
        print("certifi: not installed")

    try:
        import asyncpg

        print("asyncpg:", getattr(asyncpg, "__version__", "?"))
    except ModuleNotFoundError:
        print("asyncpg: not installed (use venv; required for test_db.py)")

    try:
        from app.core.config import Settings

        s = Settings()
    except Exception as exc:  # noqa: BLE001 — diagnostic script
        print("\nSettings() failed:", type(exc).__name__, exc, file=sys.stderr)
        print(
            "\nEnsure backend/.env exists and required variables are set "
            "(see backend/.env.example).",
            file=sys.stderr,
        )
        return 1

    print("\n--- Configuration (values redacted) ---")
    print("APP_ENV:", s.app_env)
    print("DEBUG:", s.debug)
    print("DATABASE_URL (shape):", _redact_database_url(s.database_url))
    print("database_ssl_required:", s.database_ssl_required)
    print("database_ssl_verify_hostname (effective dev flag):", s.database_ssl_verify_hostname)
    print("database_ssl_cafile set:", bool((s.database_ssl_cafile or "").strip()))
    print("database_ssl_use_certifi:", s.database_ssl_use_certifi)
    print("database_ssl_insecure_dev:", s.database_ssl_insecure_dev)
    print("SUPABASE_URL host:", urlparse(str(s.supabase_url)).hostname)
    print("OPENAI_API_KEY set:", bool(s.openai_api_key))
    print("SUPABASE_SERVICE_ROLE_KEY set:", bool(s.supabase_service_role_key))
    print("SUPABASE_JWT_SECRET set:", bool(s.supabase_jwt_secret))
    print("SUPABASE_ANON_KEY set:", bool(s.supabase_anon_key))

    host = urlparse(s.database_url).hostname
    if host:
        print("\n--- DNS ---")
        try:
            infos = socket.getaddrinfo(host, 5432, type=socket.SOCK_STREAM)
            families = sorted({i[0] for i in infos})
            print(f"getaddrinfo({host!r}, 5432): ok, address families:", families)
        except OSError as exc:
            print(f"getaddrinfo failed: {exc}", file=sys.stderr)
            return 1

    print("\nOK: Settings loaded. Run test_db.py for a live DB handshake.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
