"""Short-lived in-process cache for read-heavy authenticated GETs (single worker)."""

from __future__ import annotations

from typing import Any

from cachetools import TTLCache

# Per-process; short TTL keeps signed URLs and status reasonably fresh.
_report_meta_cache: TTLCache[tuple[str, str], Any] = TTLCache(maxsize=512, ttl=25)


def get_cached_report_detail(user_id: str, report_id: str) -> Any | None:
    return _report_meta_cache.get((user_id, report_id))


def set_cached_report_detail(user_id: str, report_id: str, value: Any) -> None:
    _report_meta_cache[(user_id, report_id)] = value
