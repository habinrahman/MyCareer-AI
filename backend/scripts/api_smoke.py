#!/usr/bin/env python3
"""
Lightweight API smoke checks (no auth by default).

Usage:
  python scripts/api_smoke.py --base-url http://127.0.0.1:8000
  python scripts/api_smoke.py --base-url https://api.example.com --token "$ACCESS_TOKEN"
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

import httpx


def main() -> int:
    p = argparse.ArgumentParser(description="MyCareer AI API smoke tests")
    p.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="API origin without trailing slash",
    )
    p.add_argument("--token", default=None, help="Bearer access token (optional)")
    args = p.parse_args()
    base = args.base_url.rstrip("/")
    headers: dict[str, str] = {}
    if args.token:
        headers["Authorization"] = f"Bearer {args.token}"

    checks: list[tuple[str, str, dict[str, Any]]] = [
        ("GET", "/health", {}),
        ("GET", "/docs", {}),
    ]

    failures = 0
    with httpx.Client(timeout=30.0, headers=headers) as client:
        for method, path, extra in checks:
            url = f"{base}{path}"
            try:
                r = client.request(method, url, **extra)
                ok = r.is_success or (path == "/docs" and r.status_code in (200, 307))
                if not ok:
                    print(f"FAIL {method} {url} -> {r.status_code}", file=sys.stderr)
                    failures += 1
                else:
                    print(f"OK   {method} {url} -> {r.status_code}")
            except httpx.HTTPError as e:
                print(f"FAIL {method} {url} -> {e}", file=sys.stderr)
                failures += 1

        if args.token:
            r = client.get(f"{base}/report/00000000-0000-0000-0000-000000000000")
            if r.status_code not in (401, 404):
                print(
                    f"WARN authenticated probe unexpected status {r.status_code}",
                    file=sys.stderr,
                )

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
