"""Quiz generation — MCQ, true/false, fill-in-the-blank. Owner: Saurabh

Uses Gemini's JSON response mode rather than parsing free text. JSON mode
guarantees valid JSON, but NOT that it matches our exact schema - so we
validate the parsed structure ourselves before returning it, rather than
trusting the model blindly and letting a malformed question break the
frontend later.
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
VALID_TYPES = {"mcq", "true_false", "fill_blank"}
VALID_DIFFICULTIES = {"easy", "medium", "hard"}

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


def _validate_questions(questions: list) -> None:
    """Raises RuntimeError with a specific reason if the model's output
    doesn't match our schema. Better to fail loudly here than hand the
    frontend a malformed question it can't render."""
    for i, q in enumerate(questions):
        if not isinstance(q, dict):
            raise RuntimeError(f"Question {i} is not an object")

        q_type = q.get("type")
        if q_type not in VALID_TYPES:
            raise RuntimeError(f"Question {i} has invalid or missing type: {q_type!r}")

        if not q.get("question") or not isinstance(q["question"], str):
            raise RuntimeError(f"Question {i} missing a valid 'question' string")

        if q.get("difficulty") not in VALID_DIFFICULTIES:
            raise RuntimeError(f"Question {i} has invalid or missing difficulty: {q.get('difficulty')!r}")

        if q_type == "mcq":
            options = q.get("options")
            if not isinstance(options, list) or len(options) < 2:
                raise RuntimeError(f"Question {i} (mcq) missing valid 'options' list")
            if q.get("answer") not in options:
                raise RuntimeError(f"Question {i} (mcq) 'answer' does not match any option")

        elif q_type == "true_false":
            if str(q.get("answer")).lower() not in {"true", "false"}:
                raise RuntimeError(f"Question {i} (true_false) has invalid 'answer': {q.get('answer')!r}")

        elif q_type == "fill_blank":
            if not q.get("answer") or not isinstance(q["answer"], str):
                raise RuntimeError(f"Question {i} (fill_blank) missing a valid 'answer' string")


def generate_quiz(
    subject_id: str,
    document_id: str,
    question_count: int = 5,
    types: list[str] | None = None,
) -> dict:
    """
    Returns: {"questions": [...], "question_count": int}
    Raises ValueError for bad input, RuntimeError if Gemini isn't configured,
    the API call fails, or the model's output doesn't match our schema.
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

    full_text = truncate_content("\n\n".join(c["text"] for c in chunks))

    prompt = PROMPT_TEMPLATE.format(
        question_count=question_count,
        types=", ".join(types),
        schema_instructions=QUIZ_SCHEMA_INSTRUCTIONS,
        content=full_text,
    )

    model = genai.GenerativeModel(GENERATION_MODEL)
    response = safe_generate_content(
        model,
        prompt,
        generation_config=genai.types.GenerationConfig(response_mime_type="application/json"),
    )

    try:
        questions = json.loads(response.text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Model returned invalid JSON: {e}") from e

    if not isinstance(questions, list):
        raise RuntimeError("Model output was not a JSON array of questions")

    _validate_questions(questions)

    return {"questions": questions, "question_count": len(questions)}