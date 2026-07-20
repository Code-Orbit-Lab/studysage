# API Specification — StudySage

Base URL (dev): `http://localhost:8000`. All protected routes require
`Authorization: Bearer <jwt>`.

## Auth

### `POST /auth/register`
- **Auth:** none
- **Body:** `{ "email": str, "password": str, "name": str }`
- **Response 201:** `{ "user_id": uuid, "access_token": str }`
- **Errors:** `409` email already exists · `422` invalid body

### `POST /auth/login`
- **Auth:** none
- **Body:** `{ "email": str, "password": str }`
- **Response 200:** `{ "access_token": str, "refresh_token": str }`
- **Errors:** `401` invalid credentials

### `POST /auth/google`
- **Auth:** none
- **Body:** `{ "id_token": str }` (from Google OAuth client flow)
- **Response 200:** `{ "access_token": str, "refresh_token": str }`

### `POST /auth/refresh`
- **Body:** `{ "refresh_token": str }`
- **Response 200:** `{ "access_token": str }`

## Subjects & Notes

### `POST /subjects`
- **Body:** `{ "name": str }`
- **Response 201:** `{ "subject_id": uuid, "name": str }`

### `POST /notes/upload`
- **Body:** multipart form — `file`, `subject_id`
- **Response 202:** `{ "document_id": uuid, "status": "processing" }`
- Processing is async — the AI Service parses/chunks/embeds after this
  returns; poll `GET /notes/{document_id}` for status.

### `GET /notes?subject_id=`
- **Response 200:** `[ { "document_id": uuid, "filename": str, "status": str, "tags": [str] } ]`

### `DELETE /notes/{document_id}`
- **Response 204**

## Chat

### `POST /chat/query`
- **Body:** `{ "subject_id": uuid, "message": str }`
- **Response 200:** `{ "answer": str, "citations": [ { "document_id": uuid, "page": int, "snippet": str } ] }`
- **Rate limit:** 20 requests/minute/user (LLM cost control)

### `GET /chat/history?subject_id=`
- **Response 200:** `[ { "role": "user"|"assistant", "content": str, "created_at": datetime } ]`

## Quiz & Flashcards

### `POST /quiz/generate`
- **Body:** `{ "subject_id": uuid, "question_count": int, "types": ["mcq","fill_blank","true_false"] }`
- **Response 200:** `{ "quiz_id": uuid, "questions": [ { "id": uuid, "type": str, "prompt": str, "options": [str]|null } ] }`

### `POST /quiz/{quiz_id}/submit`
- **Body:** `{ "answers": { "<question_id>": "<answer>" } }`
- **Response 200:** `{ "score": int, "total": int, "review": [ { "question_id": uuid, "correct": bool, "correct_answer": str } ] }`

### `POST /flashcards/generate`
- **Body:** `{ "subject_id": uuid, "count": int }`
- **Response 200:** `{ "flashcards": [ { "question": str, "answer": str, "difficulty": str } ] }`

## Study Planner

### `POST /planner/generate`
- **Body:** `{ "subjects": [ { "subject_id": uuid, "priority": int } ], "deadline": date, "hours_per_day": number }`
- **Response 200:** `{ "plan": [ { "date": date, "subject_id": uuid, "topic": str, "hours": number } ] }`

## Analytics

### `GET /analytics/progress`
- **Response 200:** `{ "subjects_covered": int, "quiz_avg_score": number, "weak_topics": [str] }`

## Conventions
- All list endpoints support `?page=&page_size=` pagination.
- All error bodies: `{ "detail": str }`.
- All timestamps: ISO 8601, UTC.
