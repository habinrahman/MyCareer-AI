from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class CacheControlMiddleware(BaseHTTPMiddleware):
    """Adds short-lived private cache for safe read-only endpoints when enabled."""

    def __init__(self, app: Callable, *, max_age_seconds: int) -> None:
        super().__init__(app)
        self.max_age_seconds = max_age_seconds

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        if self.max_age_seconds <= 0:
            return response
        if request.method != "GET":
            return response
        path = request.url.path
        if path.startswith("/docs") or path in ("/openapi.json", "/redoc"):
            response.headers.setdefault(
                "Cache-Control",
                f"public, max-age={min(self.max_age_seconds, 300)}",
            )
        return response
