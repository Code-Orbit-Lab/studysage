"""Quiz generation — MCQ, true/false, fill-in-the-blank. Owner: Saurabh

Uses Gemini's JSON response mode (response_mime_type="application/json")
rather than asking it to format text and parsing that - JSON mode is far
more reliable for structured output than regex-parsing free text.
"""
import json
import os

import google.generativeai as genai

from embeddings import get_all_chunks_for_document

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

GENERATION_MODEL = "gemini-2.5-flash"
VALID_TYPES = {"mcq", "true_false", "fill_blank"}

QUIZ_SCHEMA_INSTRUCTIONS = """Return ONLY a JSON array of question objects, no other text.
Each object must have this exact shape based on its "type":

MCQ: {"type": "mcq", "question": str, "options": [str, str, str, str], "answer": str, "difficulty": "easy"|"medium"|"hard"}
  - "answer" must exactly match one of the strings in "options"

True/False: {"type": "true_false", "question": str, "answer": "true"|"false", "difficulty": "easy"|"medium"|"hard"}

Fill in the blank: {"type": "fill_blank", "question": str (contains a "___" blank), "answer": str, "difficulty": "easy"|"medium"|"hard"}
"""

PROMPT_TEMPLATE = """You are creating a quiz for a student studying the material below.

Generate exactly {question_count} questions, using only these types: {types}.
Distribute question types roughly evenly across the requested types.
Base every question ONLY on the document content - do not invent facts not present in it.

{schema_instructions}

Document content:
{content}
"""


def generate_quiz(
    subject_id: str,
    document_id: str,
    question_count: int = 5,
    types: list[str] | None = None,
) -> dict:
    """
    Returns: {"questions": [...], "question_count": int}
    Raises ValueError for bad input, RuntimeError if Gemini isn't configured
    or returns unparseable output.
    """
    types = types or ["mcq", "true_false", "fill_blank"]
    invalid_types = set(types) - VALID_TYPES
    if invalid_types:
        raise ValueError(f"Invalid question types: {invalid_types}. Must be from {VALID_TYPES}")
    if question_count < 1 or question_count > 20:
        raise ValueError("question_count must be between 1 and 20")

    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not configured")

    chunks = get_all_chunks_for_document(subject_id, document_id)
    if not chunks:
        return {"questions": [], "question_count": 0}

    full_text = "\n\n".join(c["text"] for c in chunks)

    prompt = PROMPT_TEMPLATE.format(
        question_count=question_count,
        types=", ".join(types),
        schema_instructions=QUIZ_SCHEMA_INSTRUCTIONS,
        content=full_text,
    )

    model = genai.GenerativeModel(GENERATION_MODEL)
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(response_mime_type="application/json"),
    )

    try:
        questions = json.loads(response.text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Model returned invalid JSON: {e}") from e

    if not isinstance(questions, list):
        raise RuntimeError("Model output was not a JSON array of questions")

    return {"questions": questions, "question_count": len(questions)}