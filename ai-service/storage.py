"""File retrieval for /process — local disk (current) + Supabase Storage
(future). Owner: Saurabh

Sumit's backend currently stores uploads on local disk (see
backend/services/storage.py docstring: "v1 uses the local filesystem...").
storage_path values are therefore local filesystem paths, not Supabase keys,
for now. This only works when ai-service and backend run on the same
machine/filesystem - genuinely fine for local dev (how the team currently
runs things), but NOT how this will work once either service is
containerized/deployed separately (see infrastructure/render.yaml).
Flagged to Sumit as an open question - not urgent, but a real one.

get_document() checks local disk first; if the path doesn't exist there,
falls back to attempting Supabase Storage (still unconfigured - fails with
a clear 503 until real credentials are wired in). This means once Supabase
IS configured, this file's behavior transitions automatically with zero
changes needed elsewhere.
"""
import os
import shutil
from pathlib import Path

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "documents")


def _try_local_disk(storage_path: str, destination_dir: Path) -> Path | None:
    """Returns a local copy of the file if storage_path exists on disk,
    None otherwise (so the caller can fall back to Supabase)."""
    source = Path(storage_path)
    if not source.is_file():
        return None
    destination = destination_dir / source.name
    shutil.copy2(source, destination)
    return destination


def _download_from_supabase(storage_path: str, destination_dir: Path) -> Path:
    """
    TODO(saurabh): implement once SUPABASE_URL/SUPABASE_KEY are available.
    Likely shape (using the supabase-py client):

        from supabase import create_client
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        data = client.storage.from_(SUPABASE_BUCKET).download(storage_path)
        local_path = destination_dir / Path(storage_path).name
        local_path.write_bytes(data)
        return local_path
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError(
            "File not found on local disk, and Supabase Storage is not "
            "configured (SUPABASE_URL/SUPABASE_KEY missing) as a fallback. "
            "If running ai-service and backend on different machines, "
            "local-disk lookup won't work - Supabase credentials are needed."
        )
    raise NotImplementedError("Supabase download not yet implemented")


def download_from_storage(storage_path: str, destination_dir: Path) -> Path:
    """Returns a local file path ready for parsing - either a direct copy
    from local disk (current setup) or downloaded from Supabase Storage
    (future setup, once configured)."""
    local_result = _try_local_disk(storage_path, destination_dir)
    if local_result is not None:
        return local_result
    return _download_from_supabase(storage_path, destination_dir)