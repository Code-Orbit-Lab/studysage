"""Flashcard generation — question/answer pairs with difficulty tags.
Owner: Saurabh

Same JSON-mode + schema-validation pattern as quiz.py.
"""
import json
import os

import google.generativeai as genai

from embeddings import get_all_chunks_for_document
from gemini_utils import safe_generate_content, truncate_content

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
CARD_DIFFICULTY_VALUES = {"easy", "medium", "hard"}


def _validate_flashcards(flashcards: list) -> None:
    for i, card in enumerate(flashcards):
        if not isinstance(card, dict):
            raise RuntimeError(f"Flashcard {i} is not an object")
        if not card.get("question") or not isinstance(card["question"], str):
            raise RuntimeError(f"Flashcard {i} missing a valid 'question' string")
        if not card.get("answer") or not isinstance(card["answer"], str):
            raise RuntimeError(f"Flashcard {i} missing a valid 'answer' string")
        if card.get("difficulty") not in CARD_DIFFICULTY_VALUES:
            raise RuntimeError(f"Flashcard {i} has invalid or missing difficulty: {card.get('difficulty')!r}")


def generate_flashcards(
    subject_id: str,
    document_id: str,
    card_count: int = 10,
    difficulty: str = "mixed",
) -> dict:
    """
    Returns: {"flashcards": [...], "card_count": int}
    Raises ValueError for bad input, RuntimeError if Gemini isn't configured,
    the API call fails, or the model's output doesn't match our schema.
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

    full_text = truncate_content("\n\n".join(c["text"] for c in chunks))

    prompt = PROMPT_TEMPLATE.format(
        card_count=card_count,
        difficulty=difficulty,
        schema_instructions=CARD_SCHEMA_INSTRUCTIONS,
        content=full_text,
    )

    model = genai.GenerativeModel(GENERATION_MODEL)
    response = safe_generate_content(
        model,
        prompt,
        generation_config=genai.types.GenerationConfig(response_mime_type="application/json"),
    )

    try:
        flashcards = json.loads(response.text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Model returned invalid JSON: {e}") from e

    if not isinstance(flashcards, list):
        raise RuntimeError("Model output was not a JSON array of flashcards")

    _validate_flashcards(flashcards)

    return {"flashcards": flashcards, "card_count": len(flashcards)}