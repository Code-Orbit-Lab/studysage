from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.chat import router as chat_router
from api.flashcards import router as flashcards_router
from api.notes import router as notes_router
from api.planner import router as planner_router
from api.quiz import router as quiz_router
from api.subjects import router as subjects_router
from auth.router import router as auth_router

app = FastAPI(title="StudySage API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(subjects_router, prefix="/subjects", tags=["subjects"])
app.include_router(notes_router, prefix="/notes", tags=["notes"])
app.include_router(chat_router, prefix="/chat", tags=["chat"])
app.include_router(quiz_router, prefix="/quiz", tags=["quiz"])
app.include_router(flashcards_router, prefix="/flashcards", tags=["flashcards"])
app.include_router(planner_router, prefix="/planner", tags=["planner"])


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "studysage-backend"}

