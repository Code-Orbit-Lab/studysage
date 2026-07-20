# Product Requirements Document — StudySage

## Executive Summary
StudySage lets a student upload their own study material and converse with
it, generate revision content from it, and plan study time around it.
Every answer is grounded in the student's own uploaded documents and cited
back to the exact page it came from. See [Project Charter](../00_Project_Charter/charter.md)
for the full problem statement.

## Personas

**Riya — final-year B.Tech student, placement prep**
Has 3 years of scattered notes/slides across subjects. Needs to revise fast
and self-test before interviews. Wants quizzes generated from her own DSA
and CS-fundamentals notes rather than generic question banks.

**Aman — second-year student, semester exams**
Uploads lecture slides right after class. Wants a quick chapter summary and
a study plan that fits around his other subjects and a fixed exam date.

## Functional Requirements
| ID | Requirement |
|---|---|
| FR-1 | User can register/login via email or Google OAuth |
| FR-2 | User can create subjects and upload PDF/DOCX/PPTX/images into them |
| FR-3 | System parses and OCRs uploads, chunks and embeds the text |
| FR-4 | User can ask a question and get an answer grounded in their material, with a citation (document + page) |
| FR-5 | User can request a short/detailed/chapter-wise summary of a document |
| FR-6 | User can generate a quiz (MCQ/fill-blank/true-false) from a subject's material and get scored |
| FR-7 | User can generate flashcards from a subject's material |
| FR-8 | User can generate a study plan given subjects, a deadline, and available hours/day |
| FR-9 | User can see progress analytics (topics covered, quiz scores over time) |
| FR-10 | User can edit/delete/tag/search their notes |

## Non-Functional Requirements
| ID | Requirement |
|---|---|
| NFR-1 | RAG answers must include a citation; no un-cited claims presented as fact |
| NFR-2 | Auth tokens (JWT) expire and refresh; passwords are hashed (bcrypt), never stored in plain text |
| NFR-3 | File uploads validated for type/size before processing (see [Security](../07_Security/security.md)) |
| NFR-4 | Each of the 3 services (frontend/backend/ai-service) can be deployed and scaled independently |
| NFR-5 | Core stack stays free/open-source; only paid dependency is the LLM API |

## User Stories & Acceptance Criteria (sample)
**As a student, I want to upload a PDF and ask questions about it, so that I
don't have to re-read the whole thing to find one fact.**
- Given a PDF is uploaded and processed, when I ask a question covered in
  the document, then I get an answer citing the specific page.
- Given a question is not covered in any of my uploads, then the system
  says so instead of guessing.

**As a student, I want a quiz generated from my notes, so that I can
self-test before an exam.**
- Given a subject has processed documents, when I request a quiz, then I
  get a mix of MCQ/fill-blank/true-false questions with an answer key and
  a score at the end.

## Constraints & Assumptions
See [Project Charter](../00_Project_Charter/charter.md#constraints--assumptions).

## Risks
See [Project Charter](../00_Project_Charter/charter.md#risks).

## Future Roadmap (post-v1)
Voice-based Q&A, handwritten-notes recognition, YouTube lecture
summarization, multi-language support, collaborative study groups, spaced
repetition reminders, AI-generated mind maps, mobile app.
