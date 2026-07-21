from pathlib import Path
from parser import parse_document

SAMPLE_PDF = Path(__file__).parent.parent / "spike" / "sample.pdf"


def test_parse_pdf_returns_pages_with_text():
    result = parse_document(SAMPLE_PDF)
    assert len(result) > 0
    assert all("page" in r and "text" in r for r in result)
    assert all(isinstance(r["page"], int) for r in result)