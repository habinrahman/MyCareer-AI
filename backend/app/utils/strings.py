import re
import uuid


def safe_storage_filename(original: str) -> str:
    base = original.rsplit("/", maxsplit=1)[-1].rsplit("\\", maxsplit=1)[-1]
    cleaned = re.sub(r"[^a-zA-Z0-9._-]", "_", base).strip("._") or "resume"
    return cleaned[-180:] if len(cleaned) > 180 else cleaned


def storage_object_key(user_id: str, filename: str) -> str:
    return f"{user_id}/uploads/{uuid.uuid4().hex}_{filename}"
