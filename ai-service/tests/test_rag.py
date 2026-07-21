from embeddings import chunk_pages, embed_and_store
from rag import answer_query


def test_answer_query_returns_grounded_answer_with_citations():
    pages = [
        {"page": 1, "text": "The mitochondria is the powerhouse of the cell. It generates ATP through cellular respiration."},
        {"page": 2, "text": "Photosynthesis occurs in chloroplasts, converting sunlight into chemical energy stored as glucose."},
    ]
    chunks = chunk_pages(pages, chunk_size=100, overlap=10)
    embed_and_store(chunks, subject_id="test_rag_subject", document_id="test_rag_doc")

    result = answer_query("What does the mitochondria do?", subject_id="test_rag_subject")

    assert "answer" in result
    assert "citations" in result
    assert len(result["answer"]) > 0
    assert len(result["citations"]) > 0
    assert result["citations"][0]["page"] == 1  # should cite the mitochondria chunk, not photosynthesis


def test_answer_query_handles_no_relevant_chunks():
    result = answer_query("random question", subject_id="nonexistent_subject_xyz")
    assert result["citations"] == []
    assert len(result["answer"]) > 0