"""Composing a grounded answer.

One function ties the per-question stages together so the CLI and the tests
exercise the same path: retrieve -> generate -> verify (deterministic quote
check) -> judge (semantic support check) -> (persist). Retrieval is done by the
caller (it owns the store and embedder); this takes the results plus a generator
and an optional judge.
"""

from __future__ import annotations

from dataclasses import dataclass

from .generator import Generator
from .judge import Judge
from .retrieve import Result
from .store import Store
from .verify import VerifiedClaim, verify_claims


@dataclass
class Answer:
    """A verified answer to a question."""

    question: str
    claims: list[VerifiedClaim]
    results: list[Result]

    @property
    def verified_claims(self) -> list[VerifiedClaim]:
        return [c for c in self.claims if c.verified]

    @property
    def flagged_claims(self) -> list[VerifiedClaim]:
        return [c for c in self.claims if not c.verified]


def compose_answer(
    question: str,
    results: list[Result],
    generator: Generator,
    judge: Judge | None = None,
) -> Answer:
    """Run the full per-question pipeline for a question.

    The deterministic quote check runs first (cheap, certain). Claims that pass
    it then go to the judge, if one is provided: the judge assigns a grounding
    tier, or downgrades the claim to unsupported when the source does not
    support it as worded (a real quote paired with an unsupported claim). Claims
    that already failed the quote check are left untouched -- no point judging a
    quote that isn't even present.
    """
    claims = generator.generate(question, results)
    verified = verify_claims(claims, results)
    if judge is None:
        return Answer(question=question, claims=verified, results=results)

    for vc in verified:
        if not vc.verified or vc.chunk is None:
            continue
        tier = judge.judge(vc.claim.text, vc.chunk.text)
        if tier == "unsupported":
            vc.status = "unsupported"
            vc.reason = "the cited source does not support the claim as worded"
            vc.tier = None
        else:
            vc.tier = tier
    return Answer(question=question, claims=verified, results=results)


def persist_answer(store: Store, answer: Answer) -> int:
    """Save an answer and its claims, returning the answer id."""
    rows = [
        (
            vc.claim.text,
            vc.claim.quote,
            vc.chunk.id if vc.chunk else None,
            vc.status,
            vc.reason,
            vc.tier,
        )
        for vc in answer.claims
    ]
    return store.save_answer(answer.question, rows)
