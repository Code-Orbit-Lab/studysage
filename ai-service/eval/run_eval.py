"""Runs the fixed eval set against the live RAG pipeline and reports a
pass rate. This makes real Gemini API calls - run manually/periodically,
NOT in CI (unlike pytest suites, which are fully mocked).

Usage: python eval/run_eval.py

Note: paced with a delay between calls to stay under the Gemini free-tier
rate limit (5 requests/minute as of writing). If you hit a 429
ResourceExhausted error anyway, increase DELAY_BETWEEN_CALLS_SECONDS below.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from embeddings import chunk_pages, embed_and_store
from rag import answer_query
from eval.eval_dataset import KNOWLEDGE_BASE, EVAL_QUESTIONS, EVAL_SUBJECT_ID, EVAL_DOCUMENT_ID

DELAY_BETWEEN_CALLS_SECONDS = 13  # free tier: 5 req/min -> ~12s minimum spacing, +1s buffer


def seed_knowledge_base():
    chunks = chunk_pages(KNOWLEDGE_BASE, chunk_size=200, overlap=20)
    embed_and_store(chunks, subject_id=EVAL_SUBJECT_ID, document_id=EVAL_DOCUMENT_ID)
    print(f"Seeded {len(chunks)} chunks into '{EVAL_SUBJECT_ID}'.\n")


def run_eval():
    seed_knowledge_base()

    passed = 0
    failed = []
    total = len(EVAL_QUESTIONS)

    for i, item in enumerate(EVAL_QUESTIONS, start=1):
        result = answer_query(item["question"], subject_id=EVAL_SUBJECT_ID)
        answer_lower = result["answer"].lower()

        keyword_hit = any(kw.lower() in answer_lower for kw in item["expected_keywords"])

        page_hit = True
        if item["expected_page"] is not None:
            cited_pages = [c["page"] for c in result["citations"]]
            page_hit = item["expected_page"] in cited_pages

        ok = keyword_hit and page_hit
        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        else:
            failed.append(i)

        print(f"[{status}] Q{i}: {item['question']}")
        print(f"  Answer: {result['answer'][:150]}")
        print(f"  Citations: {[c['page'] for c in result['citations']]}")
        if not ok:
            print(f"  Expected keywords: {item['expected_keywords']}, expected page: {item['expected_page']}")
        print()

        if i < total:
            time.sleep(DELAY_BETWEEN_CALLS_SECONDS)

    print(f"{'=' * 50}")
    print(f"RESULT: {passed}/{total} passed ({passed / total * 100:.0f}%)")
    if failed:
        print(f"Failed question numbers: {failed}")
        print("Review the answers above - a failure here means a phrasing")
        print("miss OR an actual quality regression. Use judgment.")


if __name__ == "__main__":
    run_eval()