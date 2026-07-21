"""Chunking — splits parsed page/section text into overlapping chunks
for embedding. Owner: Saurabh

Keeps page number on every chunk, since that's what makes citations
possible downstream in the RAG pipeline.
"""
CHUNK_SIZE = 500       # words, approximating tokens
CHUNK_OVERLAP = 50


def chunk_pages(pages: list[dict], chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[dict]:
    """
    pages: [{"page": int, "text": str}, ...] — output of parser.parse_document()
    Returns: [{"text": str, "page": int}, ...]
    """
    if overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    chunks = []
    for p in pages:
        words = p["text"].split()
        if not words:
            continue
        start = 0
        while start < len(words):
            end = start + chunk_size
            chunk_text = " ".join(words[start:end])
            chunks.append({"text": chunk_text, "page": p["page"]})
            if end >= len(words):
                break
            start = end - overlap
    return chunks