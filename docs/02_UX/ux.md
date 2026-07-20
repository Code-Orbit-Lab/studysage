# UX Notes — StudySage

Owner for implementation: Gaurav (Frontend). This doc captures the shared
decisions; screens themselves live in `frontend/app/`.

## Primary User Flow
```
Sign up / Login
      │
Create a Subject
      │
Upload material (PDF/DOCX/PPTX/image)
      │
      ├──> Chat with the material (RAG, citations)
      ├──> Generate a summary
      ├──> Generate a quiz / flashcards
      └──> Generate a study plan
      │
Dashboard shows progress across all subjects
```

## Information Architecture
- **Dashboard** — subjects overview, recent uploads, progress snapshot
- **Notes Manager** — per-subject list of uploaded material, CRUD, tag, search
- **Chat** — conversation view per subject, citations link into the PDF viewer
- **Quiz** — generate → attempt → score → review
- **Settings** — profile, theme

## Navigation
Left sidebar: Dashboard · Notes · Chat · Quiz · Settings. Persistent across
all screens once logged in; landing page is the only unauthenticated route.

## Screen Notes
| Screen | Key elements | Complexity |
|---|---|---|
| Landing | Hero, feature highlights, sign-up CTA | Low |
| Dashboard | Subject cards, recent activity, progress widget | Low–Medium |
| Notes Manager | List/grid of files, upload button, tag/search | Low–Medium |
| Chat | Message list, markdown rendering, citation chips, streaming | High |
| PDF Viewer | Renders alongside chat, jumps to and highlights cited page | High |
| Quiz | Question flow, answer selection, score screen | Medium |
| Settings | Profile form, theme toggle | Low |

Chat and PDF Viewer are the two state-heavy screens — see
[Team Responsibilities](../../README.md#team--ownership) for how these are
staffed (paired rather than solo-owned).

## Design System
- **Component library:** shadcn/ui on Tailwind CSS — gives accessible,
  consistent components out of the box instead of styling from scratch.
- **Color roles:** primary (brand/actions), neutral (text/surfaces),
  success/warning/error (quiz scoring, validation states).
- **Typography:** one clean sans-serif family, condensed weight reserved for
  headings/labels to keep dense screens (dashboard, notes list) scannable.

## Accessibility
- All interactive elements keyboard-navigable (shadcn/Radix primitives
  handle most of this by default).
- Sufficient color contrast for text and status colors (quiz correct/incorrect).
- PDF viewer citations are also readable as plain text (page number + quoted
  snippet), not solely a visual jump — so the info isn't lost for
  screen-reader users.

## Responsiveness
Desktop-first (students studying at a laptop), but Dashboard, Notes Manager,
and Settings should degrade cleanly to a single-column mobile layout. Chat +
PDF Viewer side-by-side is desktop-only for v1; on mobile, Chat and PDF
Viewer are separate tabs.
