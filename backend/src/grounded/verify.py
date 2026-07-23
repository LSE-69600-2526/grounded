"""Verification -- the deterministic leg.

For each claim, two things must hold for its citation to stand:

1. The cited source must actually be one of the chunks retrieved for this
   question (a model that cites an id we never showed it has fabricated the
   reference).
2. The claim's quote must actually occur in that chunk's frozen text.

Both checks are pure string work -- no model, no network -- which is exactly why
they are trustworthy. Matching normalises whitespace and case so that a quote
that is faithful but re-spaced (line wraps, double spaces) is not a spurious
miss, while an invented quote still fails.

The LLM-judge leg -- does the source *support* the claim as worded, not merely
contain the quote -- is Phase 3 and assigns the grounding tier. Here a passing
claim is "quote verified"; its tier stays pending. Nothing is deleted: a failed
claim is kept with a status and a reason (flag-don't-drop, ADR 0007).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .generator import Claim
from .retrieve import Result
from .store import Chunk

_WS = re.compile(r"\s+")


def _normalise(text: str) -> str:
    """Collapse runs of whitespace and lowercase, for robust substring matching."""
    return _WS.sub(" ", text).strip().lower()


@dataclass
class VerifiedClaim:
    """A claim after the deterministic check.

    Attributes:
        claim: The original model claim.
        status: "verified" (passed the checks) or "unsupported" (failed one).
        reason: Human-readable explanation when unsupported; empty when verified.
        chunk: The cited chunk, if it was a real retrieved source; else None.
        tier: The judge's grounding tier for a verified claim
            ("direct_quote" / "inferred"), or None when the judge hasn't run.
    """

    claim: Claim
    status: str
    reason: str
    chunk: Chunk | None
    tier: str | None = None

    @property
    def verified(self) -> bool:
        return self.status == "verified"


def verify_claims(claims: list[Claim], results: list[Result]) -> list[VerifiedClaim]:
    """Run the deterministic quote-presence check over every claim."""
    by_id: dict[int, Chunk] = {r.chunk.id: r.chunk for r in results}
    out: list[VerifiedClaim] = []
    for claim in claims:
        chunk = by_id.get(claim.source_id)
        if chunk is None:
            out.append(
                VerifiedClaim(
                    claim=claim,
                    status="unsupported",
                    reason=f"cited source id {claim.source_id} was not among the retrieved passages",
                    chunk=None,
                )
            )
            continue
        if not claim.quote.strip():
            out.append(
                VerifiedClaim(claim, "unsupported", "no supporting quote was provided", chunk)
            )
            continue
        if _normalise(claim.quote) in _normalise(chunk.text):
            out.append(VerifiedClaim(claim, "verified", "", chunk))
        else:
            out.append(
                VerifiedClaim(
                    claim,
                    "unsupported",
                    "the quoted text does not appear in the cited source",
                    chunk,
                )
            )
    return out
