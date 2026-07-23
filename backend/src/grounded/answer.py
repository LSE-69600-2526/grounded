"""Composing a grounded answer.

One function ties the per-question stages together so the CLI and the tests
exercise the same path: retrieve -> generate -> verify -> (persist). Retrieval
is done by the caller (it owns the store and embedder); this takes the results
plus a generator and produces verified claims.
"""

from __future__ import annotations

from dataclasses import dataclass

from .generator import Generator
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
    question: str, results: list[Result], generator: Generator
) -> Answer:
    """Generate claims for a question and run the deterministic check."""
    claims = generator.generate(question, results)
    verified = verify_claims(claims, results)
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
        )
        for vc in answer.claims
    ]
    return store.save_answer(answer.question, rows)
