"""RAG pipeline — retrieve -> build context -> generate -> extract citations.
Owner: Saurabh

Re-rank strategy: none (trust Chroma's vector-similarity order as-is).
Revisit only if answer quality testing shows retrieval picking irrelevant
chunks over relevant ones.
"""
import os
import re

import google.generativeai as genai

from embeddings import retrieve

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

GENERATION_MODEL = "gemini-2.5-flash"
DEFAULT_TOP_K = 5

SYSTEM_PROMPT_TEMPLATE = """Answer ONLY using the numbered context chunks below.
If the context doesn't contain enough information to answer, say so explicitly
- do not use outside knowledge.

After your answer, on a new line, list the chunk numbers you actually used in
this exact format: CITED: [0, 2]

Context:
{context_block}

Question: {query}
"""


def _build_context_block(chunks: list[dict]) -> str:
    return "\n\n".join(
        f"[{i}] (page {c['page']}) {c['text']}" for i, c in enumerate(chunks)
    )


def _extract_cited_indices(answer_text: str) -> list[int]:
    """Parses 'CITED: [0, 2]' from the model's response. Falls back to
    citing everything retrieved if the model doesn't follow the format."""
    match = re.search(r"CITED:\s*\[([\d,\s]*)\]", answer_text)
    if not match or not match.group(1).strip():
        return []
    return [int(n.strip()) for n in match.group(1).split(",") if n.strip().isdigit()]


def _strip_citation_line(answer_text: str) -> str:
    return re.sub(r"\n?CITED:\s*\[[\d,\s]*\]\s*$", "", answer_text).strip()


def answer_query(query: str, subject_id: str, top_k: int = DEFAULT_TOP_K) -> dict:
    """
    Returns:
        {
            "answer": str,
            "citations": [{"document_id": str, "page": int, "snippet": str}, ...],
        }
    """
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not configured")

    chunks = retrieve(query, subject_id=subject_id, k=top_k)

    if not chunks:
        return {
            "answer": "I couldn't find anything relevant in your uploaded material for this question.",
            "citations": [],
        }

    context_block = _build_context_block(chunks)
    prompt = SYSTEM_PROMPT_TEMPLATE.format(context_block=context_block, query=query)

    model = genai.GenerativeModel(GENERATION_MODEL)
    response = model.generate_content(prompt)
    raw_text = response.text

    cited_indices = _extract_cited_indices(raw_text)
    answer_text = _strip_citation_line(raw_text)

    # Fallback: if the model didn't cite properly, cite everything retrieved
    # rather than returning zero citations for a grounded answer.
    if not cited_indices:
        cited_indices = list(range(len(chunks)))

    citations = [
        {
            "document_id": chunks[i]["document_id"],
            "page": chunks[i]["page"],
            "snippet": chunks[i]["text"][:200],
        }
        for i in cited_indices
        if 0 <= i < len(chunks)
    ]

    return {"answer": answer_text, "citations": citations}