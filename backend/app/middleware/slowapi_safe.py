"""
SlowAPI's middleware can raise or mis-handle errors on FastAPI's built-in
documentation routes (e.g. /docs) when combined with newer Starlette/Python.
We skip rate limiting entirely for OpenAPI/Swagger/ReDoc paths.
"""

from __future__ import annotations

from starlette.requests import Request
from starlette.responses import Response

from slowapi.middleware import SlowAPIMiddleware


def _is_docs_or_schema_path(path: str) -> bool:
    if path in ("/docs", "/redoc", "/openapi.json"):
        return True
    return path.startswith("/docs/") or path.startswith("/redoc/")


class SafeSlowAPIMiddleware(SlowAPIMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[no-untyped-def]
        if _is_docs_or_schema_path(request.url.path):
            return await call_next(request)
        return await super().dispatch(request, call_next)
