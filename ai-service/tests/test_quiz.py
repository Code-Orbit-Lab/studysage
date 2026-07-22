"""Tests for quiz/quiz.py. Gemini calls mocked - see test_rag.py for why."""
import json
from unittest.mock import patch, MagicMock

from embeddings import chunk_pages, embed_and_store
from quiz import generate_quiz


def _mock_gemini_json_response(payload):
    mock_response = MagicMock()
    mock_response.text = json.dumps(payload)
    return mock_response


@patch("quiz.quiz.genai.GenerativeModel")
def test_generate_quiz_returns_parsed_questions(mock_model_class):
    fake_questions = [
        {"type": "mcq", "question": "What powers the cell?", "options": ["Nucleus", "Mitochondria", "Ribosome", "Golgi"], "answer": "Mitochondria", "difficulty": "easy"},
        {"type": "true_false", "question": "Mitochondria produces ATP.", "answer": "true", "difficulty": "easy"},
    ]
    mock_model_instance = MagicMock()
    mock_model_instance.generate_content.return_value = _mock_gemini_json_response(fake_questions)
    mock_model_class.return_value = mock_model_instance

    pages = [{"page": 1, "text": "The mitochondria is the powerhouse of the cell, producing ATP."}]
    chunks = chunk_pages(pages, chunk_size=100, overlap=10)
    embed_and_store(chunks, subject_id="test_quiz_subject", document_id="test_quiz_doc")

    result = generate_quiz("test_quiz_subject", "test_quiz_doc", question_count=2)

    assert result["question_count"] == 2
    assert result["questions"][0]["type"] == "mcq"
    assert result["questions"][1]["type"] == "true_false"


def test_generate_quiz_invalid_type_raises():
    try:
        generate_quiz("any_subject", "any_doc", types=["essay"])
        assert False, "should have raised ValueError"
    except ValueError:
        pass


def test_generate_quiz_invalid_question_count_raises():
    try:
        generate_quiz("any_subject", "any_doc", question_count=50)
        assert False, "should have raised ValueError"
    except ValueError:
        pass


def test_generate_quiz_missing_document_returns_empty():
    result = generate_quiz("nonexistent_subject", "nonexistent_doc")
    assert result["questions"] == []
    assert result["question_count"] == 0


@patch("quiz.quiz.genai.GenerativeModel")
def test_generate_quiz_raises_on_malformed_json(mock_model_class):
    mock_model_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "not valid json{{{"
    mock_model_instance.generate_content.return_value = mock_response
    mock_model_class.return_value = mock_model_instance

    pages = [{"page": 1, "text": "Some content here."}]
    chunks = chunk_pages(pages, chunk_size=100, overlap=10)
    embed_and_store(chunks, subject_id="test_quiz_malformed_subject", document_id="test_quiz_malformed_doc")

    try:
        generate_quiz("test_quiz_malformed_subject", "test_quiz_malformed_doc")
        assert False, "should have raised RuntimeError"
    except RuntimeError:
        pass

@patch("quiz.quiz.genai.GenerativeModel")
def test_generate_quiz_raises_on_mcq_missing_options(mock_model_class):
    bad_questions = [
        {"type": "mcq", "question": "What powers the cell?", "answer": "Mitochondria", "difficulty": "easy"}
        # missing "options" entirely
    ]
    mock_model_instance = MagicMock()
    mock_model_instance.generate_content.return_value = _mock_gemini_json_response(bad_questions)
    mock_model_class.return_value = mock_model_instance

    pages = [{"page": 1, "text": "The mitochondria produces ATP."}]
    chunks = chunk_pages(pages, chunk_size=100, overlap=10)
    embed_and_store(chunks, subject_id="test_quiz_badschema_subject", document_id="test_quiz_badschema_doc")

    try:
        generate_quiz("test_quiz_badschema_subject", "test_quiz_badschema_doc", question_count=1)
        assert False, "should have raised RuntimeError for missing options"
    except RuntimeError:
        pass