"""Tests for summarizer/summarizer.py. Gemini calls mocked - see test_rag.py
for why."""
from unittest.mock import patch, MagicMock

from embeddings import chunk_pages, embed_and_store
from summarizer import summarize_document


def _mock_gemini_response(text: str):
    mock_response = MagicMock()
    mock_response.text = text
    return mock_response


@patch("summarizer.summarizer.genai.GenerativeModel")
def test_summarize_document_short(mock_model_class):
    mock_model_instance = MagicMock()
    mock_model_instance.generate_content.return_value = _mock_gemini_response(
        "Photosynthesis converts light energy into chemical energy in chloroplasts."
    )
    mock_model_class.return_value = mock_model_instance

    pages = [
        {"page": 1, "text": "Photosynthesis is the process by which plants convert light energy into chemical energy. It occurs in chloroplasts using chlorophyll."},
        {"page": 2, "text": "The process has two stages: light-dependent reactions and the Calvin cycle. Light reactions produce ATP and NADPH."},
    ]
    chunks = chunk_pages(pages, chunk_size=100, overlap=10)
    embed_and_store(chunks, subject_id="test_summary_subject", document_id="test_summary_doc")

    result = summarize_document("test_summary_subject", "test_summary_doc", length="short")

    assert len(result["summary"]) > 0
    assert result["length"] == "short"
    assert result["chunk_count"] > 0
    mock_model_instance.generate_content.assert_called_once()


def test_summarize_invalid_length_raises():
    # Validation happens before any Gemini call, so no mocking needed.
    try:
        summarize_document("any_subject", "any_doc", length="not_a_real_option")
        assert False, "should have raised ValueError"
    except ValueError:
        pass


def test_summarize_missing_document_returns_graceful_message():
    # Empty-document path short-circuits before calling Gemini too.
    result = summarize_document("nonexistent_subject", "nonexistent_doc")
    assert result["chunk_count"] == 0
    assert "No content found" in result["summary"]