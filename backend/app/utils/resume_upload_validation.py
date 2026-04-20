"""Shared guards for resume uploads (extension, size cap while reading, magic bytes)."""

from __future__ import annotations

from fastapi import HTTPException, UploadFile, status

_ALLOWED_SUFFIXES: tuple[str, ...] = (".pdf", ".docx")
_READ_CHUNK = 256 * 1024


def resume_filename_allowed(filename: str | None) -> bool:
    if not filename or not filename.strip():
        return False
    base = filename.lower().rsplit("/", maxsplit=1)[-1]
    return base.endswith(_ALLOWED_SUFFIXES)


def resume_magic_matches_filename(raw: bytes, filename: str) -> bool:
    """
    Require file content to match declared type (reduces extension spoofing).
    PDF: leading ``%PDF``. DOCX: ZIP local file header (OOXML container).
    """
    if len(raw) < 5:
        return False
    base = filename.lower().rsplit("/", maxsplit=1)[-1]
    if base.endswith(".pdf"):
        return raw.startswith(b"%PDF")
    if base.endswith(".docx"):
        return raw.startswith(b"PK\x03\x04")
    return False


async def read_upload_bytes_capped(upload: UploadFile, max_bytes: int) -> bytes:
    """
    Read upload body without buffering more than ``max_bytes``.
    Raises HTTP 413 if the stream exceeds the limit.
    """
    if max_bytes < 1:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid upload size configuration",
        )
    parts: list[bytes] = []
    total = 0
    while True:
        chunk = await upload.read(_READ_CHUNK)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large (maximum {max_bytes} bytes).",
            )
        parts.append(chunk)
    return b"".join(parts)
