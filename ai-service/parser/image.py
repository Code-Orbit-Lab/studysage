"""Image/scanned-page OCR — pytesseract. Owner: Saurabh

Requires the Tesseract binary installed system-wide (not just the pip
package, which is a thin wrapper). See README.md for install instructions.
"""
import shutil

import pytesseract
from PIL import Image


def check_tesseract_available() -> bool:
    """Returns False if the Tesseract binary isn't on PATH, so callers can
    fail with a clear message instead of a confusing pytesseract traceback."""
    return shutil.which("tesseract") is not None


def ocr_image(image: Image.Image) -> str:
    """Runs OCR on a single PIL Image, returns extracted text (empty string
    if nothing readable)."""
    if not check_tesseract_available():
        raise RuntimeError(
            "Tesseract binary not found on PATH. Install it separately from "
            "pip (see README.md) - pytesseract is just a wrapper around the "
            "system binary, it doesn't bundle it."
        )
    return pytesseract.image_to_string(image).strip()


def parse_image_file(path) -> list[dict]:
    """Standalone image upload (e.g. a photographed page).
    Returns [{"page": 1, "text": str}] - single "page" since there's no
    multi-page concept for a plain image file."""
    image = Image.open(path)
    text = ocr_image(image)
    if not text:
        return []
    return [{"page": 1, "text": text}]