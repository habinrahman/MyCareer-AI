import logging
import time
import uuid
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.utils.logging_config import request_id_var

logger = logging.getLogger("app.request")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Assign X-Request-ID, bind logging context, log access line with latency."""

    def __init__(self, app: Callable, *, header_name: str = "X-Request-ID") -> None:
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        incoming = request.headers.get(self.header_name)
        rid = incoming or str(uuid.uuid4())
        token = request_id_var.set(rid)
        t0 = time.perf_counter()
        try:
            response = await call_next(request)
        except BaseException:
            request_id_var.reset(token)
            raise
        request_id_var.reset(token)
        request.state.request_id = rid
        duration_ms = (time.perf_counter() - t0) * 1000
        response.headers.setdefault(self.header_name, rid)
        logger.info(
            "%s %s %s %.2fms",
            request.method,
            request.url.path,
            getattr(response, "status_code", "?"),
            duration_ms,
        )
        return response
