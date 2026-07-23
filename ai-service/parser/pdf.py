"""PDF parsing — PyMuPDF, with OCR fallback for scanned/image-only pages.
Owner: Saurabh
"""
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image

from .image import ocr_image, check_tesseract_available


def parse_pdf(path: Path, use_ocr_fallback: bool = True) -> list[dict]:
    """Returns [{"page": int, "text": str}, ...], one entry per page with text.

    Pages with no extractable text (typically scanned/image-only pages) fall
    back to OCR on a rendered image of the page, if use_ocr_fallback is True
    and Tesseract is available. If OCR isn't available, those pages are
    skipped (same behavior as before OCR support existed) rather than
    failing the whole document.
    """
    doc = fitz.open(path)
    pages = []
    ocr_available = use_ocr_fallback and check_tesseract_available()

    for i, page in enumerate(doc, start=1):
        text = page.get_text()

        if not text.strip() and ocr_available:
            pix = page.get_pixmap(dpi=200)
            image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text = ocr_image(image)

        if text.strip():
            pages.append({"page": i, "text": text})

    doc.close()
    return pages