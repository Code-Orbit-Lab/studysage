from pathlib import Path
from parser import parse_document

from parser.image import ocr_image, check_tesseract_available, parse_image_file
from PIL import Image, ImageDraw

SAMPLE_PDF = Path(__file__).parent.parent / "spike" / "sample.pdf"


def test_parse_pdf_returns_pages_with_text():
    result = parse_document(SAMPLE_PDF)
    assert len(result) > 0
    assert all("page" in r and "text" in r for r in result)
    assert all(isinstance(r["page"], int) for r in result)


def _make_test_image_with_text(text: str, tmp_path):
    """Creates a simple PNG with rendered text for OCR to read - avoids
    needing a real photographed document as a test fixture."""
    img = Image.new("RGB", (400, 100), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((10, 40), text, fill="black")
    path = tmp_path / "test_image.png"
    img.save(path)
    return path


def test_tesseract_is_available():
    """Sanity check that the environment running tests actually has
    Tesseract installed - if this fails, every other OCR test's failure
    is misleading (it'll look like a code bug, not a missing binary)."""
    assert check_tesseract_available(), (
        "Tesseract binary not found on PATH - install it separately from pip, "
        "see README.md. This is an environment issue, not a code bug."
    )


def test_ocr_image_extracts_text(tmp_path):
    image_path = _make_test_image_with_text("HELLO WORLD", tmp_path)
    image = Image.open(image_path)
    result = ocr_image(image)
    assert "HELLO" in result.upper()


def test_parse_image_file_returns_single_page(tmp_path):
    image_path = _make_test_image_with_text("STUDY NOTES", tmp_path)
    result = parse_image_file(image_path)
    assert len(result) == 1
    assert result[0]["page"] == 1
    assert "STUDY" in result[0]["text"].upper()


def test_parse_document_dispatches_images():
    from parser import SUPPORTED_EXTENSIONS
    assert ".png" in SUPPORTED_EXTENSIONS
    assert ".jpg" in SUPPORTED_EXTENSIONS