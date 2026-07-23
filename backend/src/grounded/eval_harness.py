"""A small evaluation harness.

Runs a fixed set of hand-written cases through the real pipeline and scores
whether the tool did the right *thing* for each -- turning "seems to work" into
a number you can put in a README and re-check after every change.

Cases come in three categories, each testing a different promise:

- ``answerable`` -- the corpus supports an answer; passing means at least one
  claim survived verification (it didn't refuse a real answer).
- ``unanswerable`` -- the corpus says nothing; passing means zero verified
  claims (it reported a gap instead of inventing one).
- ``trap`` -- the corpus contains *related* text a sloppy system would misuse;
  passing means zero verified claims (the judge/quote-check resisted the
  tempting-but-unsupported claim).

The scoring intentionally rewards honesty: on unanswerable and trap cases, a
confidently verified claim is the failure. A small hand-written set is
indicative, not statistically strong -- but it is far more than eyeballing.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable

from .answer import Answer

CATEGORIES = ("answerable", "unanswerable", "trap")


@dataclass
class Case:
    """One evaluation case."""

    question: str
    category: str
    note: str = ""


@dataclass
class CaseResult:
    """The outcome of running one case."""

    case: Case
    verified: int
    flagged: int
    passed: bool


def load_cases(path: str) -> list[Case]:
    """Load cases from a JSONL file (one JSON object per line)."""
    cases: list[Case] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if obj.get("category") not in CATEGORIES:
                raise ValueError(f"bad category in case: {obj!r}")
            cases.append(
                Case(question=obj["question"], category=obj["category"], note=obj.get("note", ""))
            )
    return cases


def judge_case(case: Case, answer: Answer) -> bool:
    """Decide whether the tool did the right thing for a case."""
    verified = len(answer.verified_claims)
    if case.category == "answerable":
        return verified >= 1
    # unanswerable and trap both want the tool NOT to assert a verified claim.
    return verified == 0


def run_eval(cases: list[Case], answer_fn: Callable[[str], Answer]) -> list[CaseResult]:
    """Run every case through ``answer_fn`` (question -> Answer) and grade it."""
    results: list[CaseResult] = []
    for case in cases:
        answer = answer_fn(case.question)
        results.append(
            CaseResult(
                case=case,
                verified=len(answer.verified_claims),
                flagged=len(answer.flagged_claims),
                passed=judge_case(case, answer),
            )
        )
    return results


def scorecard(results: list[CaseResult]) -> dict:
    """Summarise results into per-category and overall pass rates."""
    summary: dict = {"overall": {"passed": 0, "total": 0}}
    for cat in CATEGORIES:
        summary[cat] = {"passed": 0, "total": 0}
    for r in results:
        summary[r.case.category]["total"] += 1
        summary["overall"]["total"] += 1
        if r.passed:
            summary[r.case.category]["passed"] += 1
            summary["overall"]["passed"] += 1
    return summary


def format_scorecard(results: list[CaseResult]) -> str:
    """Render a human-readable scorecard."""
    s = scorecard(results)
    lines = ["Evaluation scorecard", "=" * 20]
    for cat in CATEGORIES:
        c = s[cat]
        if c["total"]:
            lines.append(f"  {cat:<13} {c['passed']}/{c['total']} passed")
    o = s["overall"]
    lines.append(f"  {'overall':<13} {o['passed']}/{o['total']} passed")
    lines.append("")
    lines.append("Failures:")
    fails = [r for r in results if not r.passed]
    if not fails:
        lines.append("  (none)")
    for r in fails:
        lines.append(
            f"  [{r.case.category}] {r.case.question}  "
            f"(verified={r.verified}, flagged={r.flagged})"
        )
    return "\n".join(lines)
