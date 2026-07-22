"""Tests for gemini_utils.py — the shared error-handling and truncation
helpers used across all Gemini-calling modules."""
from unittest.mock import MagicMock

import google.api_core.exceptions as google_exceptions
import pytest

from gemini_utils import safe_generate_content, truncate_content


def test_truncate_content_leaves_short_text_unchanged():
    text = "short document content"
    assert truncate_content(text) == text


def test_truncate_content_truncates_long_text():
    text = "x" * 200_000
    result = truncate_content(text, max_chars=1000)
    assert len(result) < len(text)
    assert "truncated" in result


def test_safe_generate_content_returns_response_on_success():
    mock_model = MagicMock()
    mock_model.generate_content.return_value = "fake response"
    result = safe_generate_content(mock_model, "some prompt")
    assert result == "fake response"


def test_safe_generate_content_converts_google_api_error():
    mock_model = MagicMock()
    mock_model.generate_content.side_effect = google_exceptions.ResourceExhausted("quota exceeded")

    with pytest.raises(RuntimeError, match="AI generation service error"):
        safe_generate_content(mock_model, "some prompt")


def test_safe_generate_content_converts_unexpected_error():
    mock_model = MagicMock()
    mock_model.generate_content.side_effect = ValueError("something weird")

    with pytest.raises(RuntimeError, match="AI generation failed unexpectedly"):
        safe_generate_content(mock_model, "some prompt")