"""Document summarization — short/detailed/chapter-wise. Owner: Saurabh

Unlike RAG query, this pulls ALL chunks for a document (not top-k similarity
matches), since a summary must represent the whole document, not just the
parts most similar to some query.
"""
import os

import google.generativeai as genai

from embeddings import get_all_chunks_for_document
from gemini_utils import safe_generate_content, truncate_content

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

GENERATION_MODEL = "gemini-2.5-flash"

SUMMARY_LENGTH_INSTRUCTIONS = {
    "short": "Write a concise summary in 3-5 sentences covering only the most important points.",
    "detailed": "Write a thorough summary in 5-8 paragraphs, covering all major points and supporting details.",
    "chapter-wise": "Break the summary into sections, one per major topic/chapter found in the document, each 2-4 sentences.",
}

PROMPT_TEMPLATE = """You are summarizing study material for a student.

{length_instruction}

Base your summary ONLY on the document content below. Do not add outside
information. Use clear, student-friendly language.

Document content:
{content}
"""


def summarize_document(subject_id: str, document_id: str, length: str = "short") -> dict:
    """
    length: one of "short", "detailed", "chapter-wise"
    Returns: {"summary": str, "length": str, "chunk_count": int}
    Raises ValueError for bad input, RuntimeError if Gemini isn't configured
    or the API call fails.
    """
    if length not in SUMMARY_LENGTH_INSTRUCTIONS:
        raise ValueError(f"length must be one of {list(SUMMARY_LENGTH_INSTRUCTIONS)}")

    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not configured")

    chunks = get_all_chunks_for_document(subject_id, document_id)
    if not chunks:
        return {"summary": "No content found for this document.", "length": length, "chunk_count": 0}

    full_text = truncate_content("\n\n".join(c["text"] for c in chunks))

    prompt = PROMPT_TEMPLATE.format(
        length_instruction=SUMMARY_LENGTH_INSTRUCTIONS[length],
        content=full_text,
    )

    model = genai.GenerativeModel(GENERATION_MODEL)
    response = safe_generate_content(model, prompt)

    return {"summary": response.text.strip(), "length": length, "chunk_count": len(chunks)}