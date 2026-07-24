"""Progress analytics — aggregates quiz performance across a user's
subjects. Owner: Sumit.

Schema note: `weak_topics` in the API spec implies topic-level tagging,
but nothing below `subjects` is tagged in the current schema (quiz
questions have no topic/tag column). This computes "weak" at subject
granularity instead -- subjects where the user's average quiz score is
below WEAK_THRESHOLD -- which is the finest grain the current tables
support. Revisit if/when quiz_questions gets a topic column.
"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from database.session import get_db
from models import Quiz, QuizAttempt, Subject, User

router = APIRouter()

WEAK_THRESHOLD = 0.6  # avg score below 60% on a subject's quizzes counts as "weak"


@router.get("/progress")
def get_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    subjects_covered = (
        db.query(Subject).filter(Subject.user_id == current_user.id).count()
    )

    attempts = (
        db.query(QuizAttempt, Quiz.subject_id)
        .join(Quiz, QuizAttempt.quiz_id == Quiz.id)
        .filter(QuizAttempt.user_id == current_user.id)
        .all()
    )

    if not attempts:
        return {
            "subjects_covered": subjects_covered,
            "quiz_avg_score": None,
            "weak_topics": [],
        }

    scored_attempts = [
        (a.score / a.total, subject_id) for a, subject_id in attempts if a.total
    ]
    overall_avg = (
        round(sum(s for s, _ in scored_attempts) / len(scored_attempts) * 100, 1)
        if scored_attempts
        else None
    )

    per_subject_scores: dict[uuid.UUID, list[float]] = {}
    for score_fraction, subject_id in scored_attempts:
        per_subject_scores.setdefault(subject_id, []).append(score_fraction)

    weak_subject_ids = [
        sid
        for sid, scores in per_subject_scores.items()
        if (sum(scores) / len(scores)) < WEAK_THRESHOLD
    ]
    weak_topics = []
    if weak_subject_ids:
        weak_topics = [
            s.name
            for s in db.query(Subject).filter(Subject.id.in_(weak_subject_ids)).all()
        ]

    return {
        "subjects_covered": subjects_covered,
        "quiz_avg_score": overall_avg,
        "weak_topics": weak_topics,
    }
