from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.notes import router as notes_router
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


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "studysage-backend"}