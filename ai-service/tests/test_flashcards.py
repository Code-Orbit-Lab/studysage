"""Tests for flashcards/flashcards.py. Gemini calls mocked - see test_rag.py."""
import json
from unittest.mock import patch, MagicMock

from embeddings import chunk_pages, embed_and_store
from flashcards import generate_flashcards


def _mock_gemini_json_response(payload):
    mock_response = MagicMock()
    mock_response.text = json.dumps(payload)
    return mock_response


@patch("flashcards.flashcards.genai.GenerativeModel")
def test_generate_flashcards_returns_parsed_cards(mock_model_class):
    fake_cards = [
        {"question": "What does the mitochondria produce?", "answer": "ATP", "difficulty": "easy"},
        {"question": "Where does photosynthesis occur?", "answer": "Chloroplasts", "difficulty": "medium"},
    ]
    mock_model_instance = MagicMock()
    mock_model_instance.generate_content.return_value = _mock_gemini_json_response(fake_cards)
    mock_model_class.return_value = mock_model_instance

    pages = [{"page": 1, "text": "The mitochondria produces ATP. Photosynthesis occurs in chloroplasts."}]
    chunks = chunk_pages(pages, chunk_size=100, overlap=10)
    embed_and_store(chunks, subject_id="test_flashcards_subject", document_id="test_flashcards_doc")

    result = generate_flashcards("test_flashcards_subject", "test_flashcards_doc", card_count=2)

    assert result["card_count"] == 2
    assert result["flashcards"][0]["answer"] == "ATP"


def test_generate_flashcards_invalid_difficulty_raises():
    try:
        generate_flashcards("any_subject", "any_doc", difficulty="impossible")
        assert False, "should have raised ValueError"
    except ValueError:
        pass


def test_generate_flashcards_invalid_count_raises():
    try:
        generate_flashcards("any_subject", "any_doc", card_count=100)
        assert False, "should have raised ValueError"
    except ValueError:
        pass


def test_generate_flashcards_missing_document_returns_empty():
    result = generate_flashcards("nonexistent_subject", "nonexistent_doc")
    assert result["flashcards"] == []
    assert result["card_count"] == 0


@patch("flashcards.flashcards.genai.GenerativeModel")
def test_generate_flashcards_raises_on_malformed_json(mock_model_class):
    mock_model_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "not valid json{{{"
    mock_model_instance.generate_content.return_value = mock_response
    mock_model_class.return_value = mock_model_instance

    pages = [{"page": 1, "text": "Some content here."}]
    chunks = chunk_pages(pages, chunk_size=100, overlap=10)
    embed_and_store(chunks, subject_id="test_flashcards_malformed_subject", document_id="test_flashcards_malformed_doc")

    try:
        generate_flashcards("test_flashcards_malformed_subject", "test_flashcards_malformed_doc")
        assert False, "should have raised RuntimeError"
    except RuntimeError:
        pass