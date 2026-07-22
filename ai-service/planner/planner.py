"""Study planner — subjects x deadline x available hours -> day-by-day plan.
Owner: Saurabh

Unlike the other generators, this doesn't touch document retrieval at all -
it's pure scheduling logic based on user-provided subject/deadline/hours
input, so Gemini is reasoning over a structured request, not document chunks.
"""
import json
import os
from datetime import date

import google.generativeai as genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

GENERATION_MODEL = "gemini-2.5-flash"

PLAN_SCHEMA_INSTRUCTIONS = """Return ONLY a JSON array of day objects, no other text.
Each object must have this exact shape:
{"day": int, "date": "YYYY-MM-DD", "sessions": [{"subject": str, "hours": number, "focus": str}]}

"focus" should briefly describe what to concentrate on that session
(e.g. "review weak topics", "practice problems", "first pass through new material").
Sum of "hours" per day must not exceed the available hours per day.
"""

PROMPT_TEMPLATE = """You are creating a study plan for a student.

Subjects and priority (1=highest priority/most difficult, 5=lowest): {subjects}
Days available: {days_available}
Hours available per day: {hours_per_day}
Plan starts on: {start_date}

Allocate more time to higher-priority (lower-numbered) subjects, but ensure
every subject gets covered at least once. Front-load harder subjects earlier
when the student is fresher, and schedule lighter review sessions closer to
the deadline.

{schema_instructions}
"""


def generate_study_plan(
    subjects: list[dict],
    deadline: str,
    hours_per_day: float,
    start_date: str | None = None,
) -> dict:
    """
    subjects: [{"name": str, "priority": int (1-5)}, ...]
    deadline: "YYYY-MM-DD"
    start_date: "YYYY-MM-DD", defaults to today

    Returns: {"plan": [...], "days_available": int}
    Raises ValueError for bad input, RuntimeError if Gemini isn't configured
    or returns unparseable output.
    """
    if not subjects:
        raise ValueError("subjects list cannot be empty")
    for s in subjects:
        if "name" not in s or "priority" not in s:
            raise ValueError("each subject must have 'name' and 'priority'")
        if not (1 <= s["priority"] <= 5):
            raise ValueError("priority must be between 1 and 5")
    if hours_per_day <= 0 or hours_per_day > 16:
        raise ValueError("hours_per_day must be between 0 and 16")

    start = date.fromisoformat(start_date) if start_date else date.today()
    try:
        end = date.fromisoformat(deadline)
    except ValueError as e:
        raise ValueError(f"deadline must be in YYYY-MM-DD format: {e}") from e

    days_available = (end - start).days
    if days_available < 1:
        raise ValueError("deadline must be after start_date")

    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not configured")

    subjects_str = ", ".join(f"{s['name']} (priority {s['priority']})" for s in subjects)

    prompt = PROMPT_TEMPLATE.format(
        subjects=subjects_str,
        days_available=days_available,
        hours_per_day=hours_per_day,
        start_date=start.isoformat(),
        schema_instructions=PLAN_SCHEMA_INSTRUCTIONS,
    )

    model = genai.GenerativeModel(GENERATION_MODEL)
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(response_mime_type="application/json"),
    )

    try:
        plan = json.loads(response.text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Model returned invalid JSON: {e}") from e

    if not isinstance(plan, list):
        raise RuntimeError("Model output was not a JSON array of days")

    return {"plan": plan, "days_available": days_available}