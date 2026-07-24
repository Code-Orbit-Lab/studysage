"""
Content-based file type detection — never trust the client's filename
extension or declared Content-Type for security-relevant decisions
(see docs/07_Security/security.md#file-upload-security). Owner: Sumit.
"""
import io
import zipfile

_PDF_MAGIC = b"%PDF-"
_ZIP_MAGIC = b"PK\x03\x04"
_JPEG_MAGIC = b"\xff\xd8\xff"
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def detect_file_type(content: bytes) -> str | None:
    """Returns one of 'pdf' | 'docx' | 'pptx' | 'image', or None if the
    content doesn't match any supported type — regardless of what the
    filename/extension claims."""
    if content.startswith(_PDF_MAGIC):
        return "pdf"
    if content.startswith((_JPEG_MAGIC, _PNG_MAGIC)):
        return "image"
    if content.startswith(_ZIP_MAGIC):
        return _detect_office_type(content)
    return None


def _detect_office_type(content: bytes) -> str | None:
    """DOCX and PPTX are both ZIP containers — distinguish by the internal
    file layout rather than trusting the extension."""
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            names = zf.namelist()
    except zipfile.BadZipFile:
        return None

    if any(n.startswith("word/") for n in names):
        return "docx"
    if any(n.startswith("ppt/") for n in names):
        return "pptx"
    return None