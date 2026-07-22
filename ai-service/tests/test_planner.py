"""Tests for planner/planner.py. Gemini calls mocked - see test_rag.py."""
import json
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

from planner import generate_study_plan


def _mock_gemini_json_response(payload):
    mock_response = MagicMock()
    mock_response.text = json.dumps(payload)
    return mock_response


@patch("planner.planner.genai.GenerativeModel")
def test_generate_study_plan_returns_parsed_days(mock_model_class):
    fake_plan = [
        {"day": 1, "date": "2026-08-01", "sessions": [{"subject": "Math", "hours": 2, "focus": "new material"}]},
        {"day": 2, "date": "2026-08-02", "sessions": [{"subject": "Physics", "hours": 2, "focus": "practice problems"}]},
    ]
    mock_model_instance = MagicMock()
    mock_model_instance.generate_content.return_value = _mock_gemini_json_response(fake_plan)
    mock_model_class.return_value = mock_model_instance

    start = date.today()
    deadline = (start + timedelta(days=5)).isoformat()

    result = generate_study_plan(
        subjects=[{"name": "Math", "priority": 1}, {"name": "Physics", "priority": 2}],
        deadline=deadline,
        hours_per_day=3,
        start_date=start.isoformat(),
    )

    assert result["days_available"] == 5
    assert len(result["plan"]) == 2


def test_generate_study_plan_empty_subjects_raises():
    try:
        generate_study_plan(subjects=[], deadline="2026-12-01", hours_per_day=2)
        assert False, "should have raised ValueError"
    except ValueError:
        pass


def test_generate_study_plan_invalid_priority_raises():
    try:
        generate_study_plan(subjects=[{"name": "Math", "priority": 10}], deadline="2026-12-01", hours_per_day=2)
        assert False, "should have raised ValueError"
    except ValueError:
        pass


def test_generate_study_plan_deadline_before_start_raises():
    try:
        generate_study_plan(
            subjects=[{"name": "Math", "priority": 1}],
            deadline="2020-01-01",
            hours_per_day=2,
        )
        assert False, "should have raised ValueError"
    except ValueError:
        pass


def test_generate_study_plan_invalid_hours_raises():
    try:
        generate_study_plan(subjects=[{"name": "Math", "priority": 1}], deadline="2026-12-01", hours_per_day=0)
        assert False, "should have raised ValueError"
    except ValueError:
        pass


@patch("planner.planner.genai.GenerativeModel")
def test_generate_study_plan_raises_on_malformed_json(mock_model_class):
    mock_model_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "not valid json{{{"
    mock_model_instance.generate_content.return_value = mock_response
    mock_model_class.return_value = mock_model_instance

    start = date.today()
    deadline = (start + timedelta(days=3)).isoformat()

    try:
        generate_study_plan(
            subjects=[{"name": "Math", "priority": 1}],
            deadline=deadline,
            hours_per_day=2,
            start_date=start.isoformat(),
        )
        assert False, "should have raised RuntimeError"
    except RuntimeError:
        pass