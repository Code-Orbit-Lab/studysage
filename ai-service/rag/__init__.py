# TODO(saurabh): retrieve -> re-rank -> build context -> call LLM -> return answer + citations
# def answer_query(query: str, subject_id: str) -> dict: ...

from .pipeline import answer_query

__all__ = ["answer_query"]