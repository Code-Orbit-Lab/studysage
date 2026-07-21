from embeddings import chunk_pages, embed_and_store, retrieve


def test_chunk_pages_keeps_page_numbers():
    pages = [{"page": 1, "text": " ".join(["word"] * 600)}]
    chunks = chunk_pages(pages, chunk_size=500, overlap=50)
    assert len(chunks) > 1
    assert all(c["page"] == 1 for c in chunks)


def test_chunk_pages_skips_empty_text():
    pages = [{"page": 1, "text": ""}, {"page": 2, "text": "real content here"}]
    chunks = chunk_pages(pages)
    assert len(chunks) == 1
    assert chunks[0]["page"] == 2


def test_embed_and_retrieve_roundtrip():
    chunks = [
        {"text": "Photosynthesis converts light into chemical energy in plants.", "page": 1},
        {"text": "Mitochondria is the powerhouse of the cell.", "page": 2},
    ]
    stored = embed_and_store(chunks, subject_id="test_subject_temp", document_id="test_doc_temp")
    assert stored == 2

    results = retrieve("how do plants make energy", subject_id="test_subject_temp", k=1)
    assert len(results) == 1
    assert results[0]["page"] == 1  # should retrieve the photosynthesis chunk, not mitochondria