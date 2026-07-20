# Database Design — StudySage (PostgreSQL)

Vector embeddings live in the separate Vector DB (ChromaDB/Qdrant), not
here — PostgreSQL holds relational/metadata only.

## Tables

### `users`
| Column | Type | Notes |
|---|---|---|
| id | uuid, PK | |
| email | text, unique | |
| password_hash | text, nullable | null if Google-OAuth-only |
| name | text | |
| auth_provider | text | `email` \| `google` |
| created_at | timestamptz | |

### `subjects`
| Column | Type | Notes |
|---|---|---|
| id | uuid, PK | |
| user_id | uuid, FK → users.id | |
| name | text | |
| created_at | timestamptz | |

### `documents`
| Column | Type | Notes |
|---|---|---|
| id | uuid, PK | |
| subject_id | uuid, FK → subjects.id | |
| filename | text | |
| file_type | text | pdf \| docx \| pptx \| image |
| storage_path | text | Supabase Storage path |
| status | text | uploaded \| processing \| ready \| failed |
| page_count | int, nullable | |
| created_at | timestamptz | |

### `document_tags`
| Column | Type | Notes |
|---|---|---|
| document_id | uuid, FK → documents.id | |
| tag | text | composite PK (document_id, tag) |

### `chat_messages`
| Column | Type | Notes |
|---|---|---|
| id | uuid, PK | |
| subject_id | uuid, FK → subjects.id | |
| role | text | user \| assistant |
| content | text | |
| citations | jsonb, nullable | `[{document_id, page, snippet}]` |
| created_at | timestamptz | |

### `quizzes`
| Column | Type | Notes |
|---|---|---|
| id | uuid, PK | |
| subject_id | uuid, FK → subjects.id | |
| created_at | timestamptz | |

### `quiz_questions`
| Column | Type | Notes |
|---|---|---|
| id | uuid, PK | |
| quiz_id | uuid, FK → quizzes.id | |
| type | text | mcq \| fill_blank \| true_false |
| prompt | text | |
| options | jsonb, nullable | |
| correct_answer | text | |

### `quiz_attempts`
| Column | Type | Notes |
|---|---|---|
| id | uuid, PK | |
| quiz_id | uuid, FK → quizzes.id | |
| user_id | uuid, FK → users.id | |
| score | int | |
| total | int | |
| completed_at | timestamptz | |

### `flashcards`
| Column | Type | Notes |
|---|---|---|
| id | uuid, PK | |
| subject_id | uuid, FK → subjects.id | |
| question | text | |
| answer | text | |
| difficulty | text | easy \| medium \| hard |

### `study_plans`
| Column | Type | Notes |
|---|---|---|
| id | uuid, PK | |
| user_id | uuid, FK → users.id | |
| deadline | date | |
| hours_per_day | numeric | |
| plan_json | jsonb | day-by-day schedule |
| created_at | timestamptz | |

## Relationships
`users 1—N subjects 1—N documents`, `subjects 1—N chat_messages`,
`subjects 1—N quizzes 1—N quiz_questions`, `quizzes 1—N quiz_attempts`.

## Indexes
- `documents(subject_id)`, `chat_messages(subject_id, created_at)`,
  `quiz_attempts(user_id)` — all foreign-key + common-filter columns.
- `users(email)` unique index (also the login lookup path).

## Migration Strategy
Alembic, one migration per schema change, reviewed in the same PR as the
model change. No manual schema edits in any environment.

## Backup Strategy
Supabase automated daily backups (managed Postgres). For anything beyond
the free tier's retention window, a weekly `pg_dump` to Supabase Storage is
a cheap fallback — add this in Phase 5 if needed.
