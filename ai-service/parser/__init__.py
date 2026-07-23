"""Unified document parsing entrypoint. Owner: Saurabh

Every format returns the same shape: [{"page": int, "text": str}, ...]
so downstream chunking/embedding stays format-agnostic.
"""
from pathlib import Path

from .pdf import parse_pdf
from .docx import parse_docx
from .pptx import parse_pptx
from .image import parse_image_file

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".png", ".jpg", ".jpeg"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def parse_document(path: str | Path) -> list[dict]:
    path = Path(path)
    ext = path.suffix.lower()

    if ext == ".pdf":
        return parse_pdf(path)
    elif ext == ".docx":
        return parse_docx(path)
    elif ext == ".pptx":
        return parse_pptx(path)
    elif ext in IMAGE_EXTENSIONS:
        return parse_image_file(path)
    else:
        raise ValueError(f"Unsupported file type: {ext}. Supported: {SUPPORTED_EXTENSIONS}")