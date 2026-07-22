"""Flashcard generation — question/answer pairs with difficulty tags.
Owner: Saurabh

Same JSON-mode pattern as quiz.py: ask Gemini for structured output
directly rather than parsing free text.
"""
import json
import os

import google.generativeai as genai

from embeddings import get_all_chunks_for_document

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

GENERATION_MODEL = "gemini-2.5-flash"

CARD_SCHEMA_INSTRUCTIONS = """Return ONLY a JSON array of flashcard objects, no other text.
Each object must have this exact shape:
{"question": str, "answer": str, "difficulty": "easy"|"medium"|"hard"}

Keep questions short and specific (good for quick recall).
Keep answers concise - 1-2 sentences, not paragraphs.
"""

PROMPT_TEMPLATE = """You are creating spaced-repetition flashcards for a student
studying the material below.

Generate exactly {card_count} flashcards.
Base every card ONLY on the document content - do not invent facts not present in it.
Cover a range of difficulty levels, weighted toward the requested difficulty: {difficulty}.

{schema_instructions}

Document content:
{content}
"""

VALID_DIFFICULTIES = {"easy", "medium", "hard", "mixed"}


def generate_flashcards(
    subject_id: str,
    document_id: str,
    card_count: int = 10,
    difficulty: str = "mixed",
) -> dict:
    """
    Returns: {"flashcards": [...], "card_count": int}
    Raises ValueError for bad input, RuntimeError if Gemini isn't configured
    or returns unparseable output.
    """
    if difficulty not in VALID_DIFFICULTIES:
        raise ValueError(f"difficulty must be one of {VALID_DIFFICULTIES}")
    if card_count < 1 or card_count > 30:
        raise ValueError("card_count must be between 1 and 30")

    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not configured")

    chunks = get_all_chunks_for_document(subject_id, document_id)
    if not chunks:
        return {"flashcards": [], "card_count": 0}

    full_text = "\n\n".join(c["text"] for c in chunks)

    prompt = PROMPT_TEMPLATE.format(
        card_count=card_count,
        difficulty=difficulty,
        schema_instructions=CARD_SCHEMA_INSTRUCTIONS,
        content=full_text,
    )

    model = genai.GenerativeModel(GENERATION_MODEL)
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(response_mime_type="application/json"),
    )

    try:
        flashcards = json.loads(response.text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Model returned invalid JSON: {e}") from e

    if not isinstance(flashcards, list):
        raise RuntimeError("Model output was not a JSON array of flashcards")

    return {"flashcards": flashcards, "card_count": len(flashcards)}