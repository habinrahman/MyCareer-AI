import contextvars
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id",
    default="-",
)


class RequestIdFilter(logging.Filter):
    """Injects request_id from context (set by RequestContextMiddleware)."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


class JsonFormatter(logging.Formatter):
    """One JSON object per line for Loki / CloudWatch / ELK."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        rid = getattr(record, "request_id", None)
        if rid and rid != "-":
            payload["request_id"] = rid
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


class TextFormatter(logging.Formatter):
    def __init__(self) -> None:
        super().__init__(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(request_id)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )

    def format(self, record: logging.LogRecord) -> str:
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        return super().format(record)


def setup_logging(level: str = "INFO", *, log_json: bool = False) -> None:
    root = logging.getLogger()
    root.handlers.clear()
    numeric = getattr(logging, level.upper(), logging.INFO)
    root.setLevel(numeric)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(numeric)
    if log_json:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(TextFormatter())
    handler.addFilter(RequestIdFilter())
    root.addHandler(handler)

    # Reduce noise from overly chatty libraries in production
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("hpack").setLevel(logging.WARNING)
