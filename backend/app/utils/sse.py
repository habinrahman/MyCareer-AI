import json


def sse_encode(payload: dict) -> bytes:
    """Format one Server-Sent Events frame (UTF-8)."""
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n".encode("utf-8")
