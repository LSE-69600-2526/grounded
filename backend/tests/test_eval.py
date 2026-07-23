"""Tests for the evaluation harness -- offline, via mock generator and judge.

The mocks are scripted so that the three case categories exercise their
distinct pass conditions: answerable -> a verified claim, unanswerable -> no
claims, trap -> a real quote the judge rejects.
"""

from __future__ import annotations

import os

from grounded.answer import Answer, compose_answer
from grounded.config import Settings
from grounded.embedder import get_embedder
from grounded.eval_harness import (
    Case,
    format_scorecard,
    judge_case,
    load_cases,
    run_eval,
    scorecard,
)
from grounded.generator import Claim, MockGenerator
from grounded.ingest import ingest_path
from grounded.judge import MockJudge
from grounded.retrieve import Retriever
from grounded.store import Chunk, Store


def _answer(verified: int, flagged: int) -> Answer:
    from grounded.verify import VerifiedClaim

    claims = []
    for _ in range(verified):
        claims.append(VerifiedClaim(Claim("c", "q", 1), "verified", "", None, "inferred"))
    for _ in range(flagged):
        claims.append(VerifiedClaim(Claim("c", "q", 1), "unsupported", "why", None, None))
    return Answer("q", claims, [])


def test_judge_case_rules():
    ans_ok = _answer(verified=1, flagged=0)
    ans_none = _answer(verified=0, flagged=1)
    assert judge_case(Case("q", "answerable"), ans_ok) is True
    assert judge_case(Case("q", "answerable"), ans_none) is False
    # unanswerable/trap pass only when nothing was asserted as verified.
    assert judge_case(Case("q", "unanswerable"), ans_none) is True
    assert judge_case(Case("q", "unanswerable"), ans_ok) is False
    assert judge_case(Case("q", "trap"), ans_none) is True
    assert judge_case(Case("q", "trap"), ans_ok) is False


def test_load_cases_reads_jsonl():
    path = os.path.join(os.path.dirname(__file__), "..", "eval", "cases.jsonl")
    cases = load_cases(path)
    assert len(cases) >= 6
    assert {c.category for c in cases} <= {"answerable", "unanswerable", "trap"}


def test_scorecard_counts_and_formats():
    results = run_eval(
        [Case("a", "answerable"), Case("b", "unanswerable")],
        lambda q: _answer(1, 0) if q == "a" else _answer(0, 0),
    )
    s = scorecard(results)
    assert s["overall"] == {"passed": 2, "total": 2}
    assert "overall" in format_scorecard(results)


def test_end_to_end_eval_over_sample_corpus(tmp_path):
    settings = Settings(db_path=str(tmp_path / "e.db"), embedder="hashing", hashing_dim=512)
    store = Store(settings.db_path)
    embedder = get_embedder(settings)
    corpus = os.path.join(os.path.dirname(__file__), "..", "sample_corpus")
    ingest_path(store, embedder, corpus, settings)
    retriever = Retriever(store, embedder)

    # A generator that answers the answerable case with a real quote, and
    # returns nothing for the unanswerable one. A judge that supports it.
    top = retriever.search("do naps help memory", k=3)[0].chunk
    real_quote = " ".join(top.text.split()[3:9])

    def gen_for(question: str):
        if "nap" in question:
            return MockGenerator([Claim("naps help", real_quote, top.id)])
        return MockGenerator([])  # honest gap

    def answer_fn(question: str):
        results = retriever.search(question, k=3)
        return compose_answer(question, results, gen_for(question), MockJudge("inferred"))

    cases = [Case("do naps help memory", "answerable"), Case("capital of Mars", "unanswerable")]
    results = run_eval(cases, answer_fn)
    store.close()

    passed = {r.case.question: r.passed for r in results}
    assert passed["do naps help memory"] is True
    assert passed["capital of Mars"] is True
