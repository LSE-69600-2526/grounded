# 11. A category-based evaluation set

Status: accepted

## Context

"It doesn't hallucinate" is a claim that needs evidence, not just a good demo.
Eyeballing one answer at a time doesn't scale and produces no number. And a
naive eval that only asks answerable questions would reward a system that
confidently answers everything — the opposite of the goal.

## Decision

Keep a small, fixed set of hand-written cases (`backend/eval/cases.jsonl`) in
three categories, each testing a different promise:

- **answerable** — the corpus supports an answer; passing = at least one
  verified claim.
- **unanswerable** — the corpus is silent; passing = zero verified claims (an
  honest gap, not an invention).
- **trap** — the corpus contains *related* text a sloppy system would misuse
  (e.g. "caffeine delays sleep" tempting a "caffeine improves sleep" claim);
  passing = zero verified claims (the judge/quote-check resisted).

`grounded eval` runs every case through the real pipeline and prints per-category
and overall pass rates. Scoring deliberately treats a confidently-verified claim
on an unanswerable or trap case as a failure.

## Consequences

- The trust property becomes a reproducible number for the README, and a
  regression check after any prompt or model change.
- The trap category specifically measures the judge's value: those cases pass
  the deterministic leg but should fail without the judge.
- A dozen hand-written cases is indicative, not statistically strong; the set is
  meant to grow. It is honest measurement, not a benchmark claim.
