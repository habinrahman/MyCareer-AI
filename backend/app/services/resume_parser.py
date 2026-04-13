import io
from typing import Final

import fitz
import pdfplumber
from docx import Document

_SUPPORTED: Final[frozenset[str]] = frozenset({".pdf", ".docx"})


def normalize_resume_text(text: str) -> str:
    """Collapse excessive blank lines; trim lines for cleaner NLP input."""
    lines = [ln.strip() for ln in text.splitlines()]
    out: list[str] = []
    prev_blank = False
    for ln in lines:
        blank = len(ln) == 0
        if blank and prev_blank:
            continue
        out.append(ln)
        prev_blank = blank
    return "\n".join(out).strip()


class UnsupportedResumeFormatError(ValueError):
    pass


def parse_resume_file(content: bytes, filename: str) -> str:
    name = filename.lower().rsplit("/", maxsplit=1)[-1]
    suffix = ""
    if "." in name:
        suffix = "." + name.rsplit(".", maxsplit=1)[-1]

    if suffix not in _SUPPORTED:
        raise UnsupportedResumeFormatError(
            f"Unsupported file type {suffix!r}. Use PDF or DOCX."
        )

    if suffix == ".pdf":
        return _parse_pdf(content)
    if suffix == ".docx":
        return _parse_docx(content)
    raise UnsupportedResumeFormatError("Unsupported resume format")


def _parse_pdf(content: bytes) -> str:
    text_parts: list[str] = []
    try:
        with fitz.open(stream=content, filetype="pdf") as doc:
            for page in doc:
                text_parts.append(page.get_text() or "")
    except Exception:
        text_parts = []

    joined = "\n".join(t.strip() for t in text_parts if t.strip())
    if len(joined.strip()) >= 40:
        return joined

    try:
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            plumber_parts = []
            for page in pdf.pages:
                t = page.extract_text() or ""
                if t.strip():
                    plumber_parts.append(t)
        fallback = "\n".join(plumber_parts)
        if fallback.strip():
            return fallback
    except Exception:
        pass

    if joined.strip():
        return joined
    raise ValueError("Could not extract text from PDF (empty or scanned image-only).")


def _parse_docx(content: bytes) -> str:
    doc = Document(io.BytesIO(content))
    paragraphs = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
    body = "\n".join(paragraphs).strip()
    if not body:
        raise ValueError("Could not extract text from DOCX.")
    return body
