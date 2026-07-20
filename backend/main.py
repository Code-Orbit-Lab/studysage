"""
StudySage Backend — FastAPI entrypoint.
Owner: Sumit

Run locally:
    uvicorn main:app --reload --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="StudySage API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # frontend dev URL
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "studysage-backend"}


# TODO(sumit): mount routers as they're built
# from api.auth import router as auth_router
# from api.notes import router as notes_router
# app.include_router(auth_router, prefix="/auth", tags=["auth"])
# app.include_router(notes_router, prefix="/notes", tags=["notes"])
