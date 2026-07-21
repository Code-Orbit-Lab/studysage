"""DOCX parsing — python-docx. Owner: Saurabh

DOCX has no fixed page boundaries (pagination depends on the viewer/font/zoom),
so we group paragraphs into fixed-size synthetic "sections" as a page proxy.
Citations for DOCX docs will read "Section N", not "Page N" — flagged to
Sumit/Gaurav so the frontend citation UI handles this format too.
"""
from pathlib import Path
from docx import Document

PARAGRAPHS_PER_SECTION = 15


def parse_docx(path: Path) -> list[dict]:
    """Returns [{"page": int, "text": str}, ...] — "page" here means section index."""
    doc = Document(path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]

    sections = []
    for i in range(0, len(paragraphs), PARAGRAPHS_PER_SECTION):
        chunk = paragraphs[i:i + PARAGRAPHS_PER_SECTION]
        sections.append({
            "page": (i // PARAGRAPHS_PER_SECTION) + 1,
            "text": "\n".join(chunk),
        })
    return sections