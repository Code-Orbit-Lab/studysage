"""PDF parsing — PyMuPDF. Owner: Saurabh"""
from pathlib import Path
import fitz  # PyMuPDF


def parse_pdf(path: Path) -> list[dict]:
    """Returns [{"page": int, "text": str}, ...], one entry per page with text."""
    doc = fitz.open(path)
    pages = []
    for i, page in enumerate(doc, start=1):
        text = page.get_text()
        if text.strip():
            pages.append({"page": i, "text": text})
    doc.close()
    return pages