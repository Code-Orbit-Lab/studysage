"""
Local-disk file storage for uploads. Owner: Sumit.

v1 uses the local filesystem so the upload flow is testable without a
Supabase account/credentials. Swap this module's internals for the
Supabase Storage SDK when ready — callers only see save_file()/
delete_file(), nothing outside this file needs to change.
"""
import os
import uuid
from pathlib import Path

STORAGE_ROOT = Path(os.getenv("UPLOAD_STORAGE_DIR", "./uploads")).resolve()

def save_file(user_id: str, subject_id: str, filename: str, content: bytes) -> str:
    """Writes the file to disk, returns the storage_path to save on the
    Document row."""
    directory = STORAGE_ROOT / user_id / subject_id
    directory.mkdir(parents=True, exist_ok=True)

    safe_name = f"{uuid.uuid4()}_{filename}"
    path = directory / safe_name
    path.write_bytes(content)
    return str(path)


def delete_file(storage_path: str) -> None:
    path = Path(storage_path)
    if path.exists():
        path.unlink()