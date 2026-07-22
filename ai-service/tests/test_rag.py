"""Tests for rag/pipeline.py.

Gemini calls are mocked - these tests verify our prompt construction,
retrieval wiring, and citation parsing logic, not whether Google's API
is currently reachable. That's intentionally out of scope for CI: a
third-party API being briefly down or rate-limited shouldn't block
everyone's merges.
"""
from unittest.mock import patch, MagicMock

from embeddings import chunk_pages, embed_and_store
from rag import answer_query


def _mock_gemini_response(text: str):
    """Builds a fake response object matching genai's response.text shape."""
    mock_response = MagicMock()
    mock_response.text = text
    return mock_response


@patch("rag.pipeline.genai.GenerativeModel")
def test_answer_query_returns_grounded_answer_with_citations(mock_model_class):
    mock_model_instance = MagicMock()
    mock_model_instance.generate_content.return_value = _mock_gemini_response(
        "The mitochondria generates ATP through cellular respiration.\nCITED: [0]"
    )
    mock_model_class.return_value = mock_model_instance

    pages = [
        {"page": 1, "text": "The mitochondria is the powerhouse of the cell. It generates ATP through cellular respiration."},
        {"page": 2, "text": "Photosynthesis occurs in chloroplasts, converting sunlight into chemical energy stored as glucose."},
    ]
    chunks = chunk_pages(pages, chunk_size=100, overlap=10)
    embed_and_store(chunks, subject_id="test_rag_subject", document_id="test_rag_doc")

    result = answer_query("What does the mitochondria do?", subject_id="test_rag_subject")

    assert "answer" in result
    assert "CITED" not in result["answer"]  # citation line should be stripped
    assert len(result["citations"]) > 0
    assert result["citations"][0]["page"] == 1
    mock_model_instance.generate_content.assert_called_once()


def test_answer_query_handles_no_relevant_chunks():
    # No Gemini call happens here at all - empty retrieval short-circuits
    # before generation, so no mocking needed for this path.
    result = answer_query("random question", subject_id="nonexistent_subject_xyz")
    assert result["citations"] == []
    assert len(result["answer"]) > 0


@patch("rag.pipeline.genai.GenerativeModel")
def test_answer_query_falls_back_to_all_chunks_when_model_skips_citation_format(mock_model_class):
    """If the model doesn't follow the CITED: [...] format, we should
    still return citations for everything retrieved, not zero."""
    mock_model_instance = MagicMock()
    mock_model_instance.generate_content.return_value = _mock_gemini_response(
        "The mitochondria generates ATP."  # no CITED line
    )
    mock_model_class.return_value = mock_model_instance

    pages = [{"page": 5, "text": "The mitochondria generates ATP through respiration."}]
    chunks = chunk_pages(pages, chunk_size=100, overlap=10)
    embed_and_store(chunks, subject_id="test_rag_fallback_subject", document_id="test_rag_fallback_doc")

    result = answer_query("What does the mitochondria do?", subject_id="test_rag_fallback_subject")

    assert len(result["citations"]) > 0