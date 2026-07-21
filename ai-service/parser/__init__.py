# TODO(saurabh): PDF/DOCX/PPTX parsing + OCR for images
# def parse_document(file_path: str) -> str: ...
"""Unified document parsing entrypoint. Owner: Saurabh

Every format returns the same shape: [{"page": int, "text": str}, ...]
so downstream chunking/embedding stays format-agnostic.
"""
from pathlib import Path

from .pdf import parse_pdf
from .docx import parse_docx
from .pptx import parse_pptx

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".pptx"}


def parse_document(path: str | Path) -> list[dict]:
    path = Path(path)
    ext = path.suffix.lower()

    if ext == ".pdf":
        return parse_pdf(path)
    elif ext == ".docx":
        return parse_docx(path)
    elif ext == ".pptx":
        return parse_pptx(path)
    else:
        raise ValueError(f"Unsupported file type: {ext}. Supported: {SUPPORTED_EXTENSIONS}")

# TODO(saurabh): image/scanned-page OCR via pytesseract — needs the Tesseract
# binary installed system-wide first (see Sprint 2 note on tesseract-5.5.2.zip)