# Evaluation Set

A fixed set of ~20 question/answer checks against a known knowledge base,
used to catch RAG answer-quality regressions over time - NOT a unit test.

## Why this is separate from `tests/`

- Makes real Gemini API calls (costs money, ~12 calls per run)
- Checks answer *quality* via keyword matching, which requires human judgment
  on borderline results, not a strict pass/fail like unit tests
- Not run in CI - run manually before major RAG pipeline changes, or
  periodically to catch drift

## Running it
cd ai-service
python eval/run_eval.py

## Rate limits

The free-tier Gemini API allows 5 requests/minute. This script paces calls
automatically to stay under that limit - a full run takes ~2-3 minutes.
If you still hit a 429 error, increase `DELAY_BETWEEN_CALLS_SECONDS` in
`run_eval.py`.

## When to run this

- Before merging any change to `rag/pipeline.py` (prompt changes, retrieval
  changes, re-ranking changes)
- Periodically (e.g. monthly) to catch silent quality drift from model updates
- After changing the embedding model or chunking strategy

A "FAIL" doesn't always mean something's broken - read the printed answer.
Sometimes the model phrases things differently than the expected keywords
predict. Use this as a signal to investigate, not an automatic gate.