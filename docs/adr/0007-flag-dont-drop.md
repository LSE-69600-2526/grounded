# 7. Flag, don't drop

Status: accepted

## Context

When a claim fails verification there are three options: delete it, show it as
if it were fine, or show it with its status. The first makes the answer look
better-evidenced than it is; the second is exactly the hallucination the tool
exists to prevent.

## Decision

Failed and weak claims are **kept and flagged**, never silently removed and
never silently promoted to a clean tier. Gaps — things the corpus does not
answer — are reported explicitly rather than left as silence.

## Consequences

- The rendered answer is an honest picture of the evidence, including its holes.
- The UI must have a vocabulary for status (tier badges, weak/unverified flags,
  gap notes) — this shapes the Phase 3 render design.
- "Absence of a claim" and "a claim we couldn't support" are distinct and both
  visible.
