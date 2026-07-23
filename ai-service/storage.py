"""Supabase Storage download helper. Owner: Saurabh

STUB: Supabase credentials not yet configured (Sumit hasn't set up his side
yet either, per team sync 2026-07-23). This raises clearly rather than
silently no-oping, so /process fails loudly and visibly instead of pretending
to work. Swap in the real implementation once SUPABASE_URL/SUPABASE_KEY are
available - ask Sumit for the same credentials his backend uses, don't
provision a separate bucket, or storage_path values won't resolve.
"""
import os
from pathlib import Path

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "documents")


def download_from_storage(storage_path: str, destination_dir: Path) -> Path:
    """
    Downloads a file from Supabase Storage to a local temp path for parsing.
    Returns the local file path.

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
            "Supabase Storage not configured (SUPABASE_URL/SUPABASE_KEY missing). "
            "This is expected until credentials are shared - see storage.py docstring."
        )
    raise NotImplementedError("Supabase download not yet implemented")