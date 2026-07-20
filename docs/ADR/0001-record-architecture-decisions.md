# ADR 0001 — Record Architecture Decisions

**Status:** Accepted
**Date:** 2026-07-20

## Context
As the team makes architecture-level decisions (framework choices, data
store choices, structural splits), we need a lightweight record of *why*,
not just *what* — so a decision made in Week 1 still makes sense to revisit
in Week 10, and so a new contributor doesn't have to reverse-engineer the
reasoning from code.

## Decision
Use short Architecture Decision Records (ADRs) in `docs/ADR/`, one file per
decision, numbered sequentially. Each ADR states the context, the decision,
and the consequences (including trade-offs accepted).

## Consequences
- Any team member proposing a structural change adds an ADR in the same PR.
- ADRs are never edited to reflect a reversal — a superseding decision gets
  its own new ADR that references the old one as "Superseded by ADR-000X".
