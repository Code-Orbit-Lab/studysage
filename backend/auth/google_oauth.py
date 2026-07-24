"""Verify a Google Sign-In id_token server-side. Owner: Sumit"""

import os

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")


def verify_google_token(token: str) -> dict:
    """
    Returns the verified token payload (has 'email', 'name', 'sub') or
    raises ValueError if the token is invalid / audience mismatch.
    """
    if not GOOGLE_CLIENT_ID:
        raise ValueError("GOOGLE_CLIENT_ID is not configured")
    return google_id_token.verify_oauth2_token(
        token, google_requests.Request(), GOOGLE_CLIENT_ID
    )
