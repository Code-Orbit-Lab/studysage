"""Quiz endpoints — generation proxies to the AI Service's /quiz and
persists the quiz + its questions; submission scores an attempt against
the stored answer key. Owner: Sumit.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from database.session import get_db
from models import Quiz, QuizAttempt, QuizQuestion, User
from services.ai_client import generate_quiz
from services.ownership import get_owned_document, get_owned_quiz
from services.rate_limit import LLM_ENDPOINT_LIMIT, limiter

router = APIRouter()


class QuizGenerateRequest(BaseModel):
    document_id: uuid.UUID
    question_count: int = Field(default=5, ge=1, le=20)
    types: list[str] = ["mcq", "true_false", "fill_blank"]


@router.post("/generate")
@limiter.limit(LLM_ENDPOINT_LIMIT)
def generate_quiz_endpoint(
    request: Request,
    body: QuizGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = get_owned_document(db, body.document_id, current_user)
    if document.status != "ready":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Document isn't processed yet"
        )

    result = generate_quiz(
        str(document.subject_id), str(document.id), body.question_count, body.types
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service unavailable",
        )

    quiz = Quiz(subject_id=document.subject_id)
    db.add(quiz)
    db.flush()  # assigns quiz.id without committing, so questions can FK to it

    questions = [
        QuizQuestion(
            quiz_id=quiz.id,
            type=q["type"],
            prompt=q["question"],
            options=q.get("options"),
            correct_answer=q["answer"],
        )
        for q in result.get("questions", [])
    ]
    db.add_all(questions)
    db.commit()
    for q in questions:
        db.refresh(q)

    # Never return correct_answer here -- this is what the user is about
    # to be quizzed on, not the answer key.
    return {
        "quiz_id": quiz.id,
        "questions": [
            {"id": q.id, "type": q.type, "prompt": q.prompt, "options": q.options}
            for q in questions
        ],
    }


class QuizSubmitRequest(BaseModel):
    answers: dict[str, str]  # {"<question_id>": "<submitted_answer>"}


@router.post("/{quiz_id}/submit")
def submit_quiz(
    quiz_id: uuid.UUID,
    body: QuizSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    quiz = get_owned_quiz(db, quiz_id, current_user)
    questions = db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz.id).all()
    if not questions:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Quiz has no questions"
        )

    review = []
    score = 0
    for q in questions:
        submitted = body.answers.get(str(q.id))
        correct = (
            submitted is not None
            and submitted.strip().lower() == q.correct_answer.strip().lower()
        )
        if correct:
            score += 1
        review.append(
            {
                "question_id": q.id,
                "correct": correct,
                "correct_answer": q.correct_answer,
            }
        )

    attempt = QuizAttempt(
        quiz_id=quiz.id, user_id=current_user.id, score=score, total=len(questions)
    )
    db.add(attempt)
    db.commit()

    return {"score": score, "total": len(questions), "review": review}
