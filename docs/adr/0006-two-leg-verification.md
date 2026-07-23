# 6. Two-leg verification: deterministic check then judge

Status: accepted

## Context

An LLM asked to "answer with citations" will sometimes attach a real source to a
claim it does not support, or quote text that is not in the source at all. A
single LLM "is this right?" pass is itself fallible and expensive to run on
every claim.

## Decision

Verify each claim in **two independent legs**:

1. A **deterministic** quote-presence check — the cited quote must occur in the
   frozen chunk text (normalised match). No model involved; a fabricated quote
   is a hard fail here, cheaply.
2. An **LLM-as-judge** support check — does the passage support the claim *as
   worded*? It assigns a grounding tier and is strict about attribution fidelity
   (scope, caveats, direction) while permissive about legitimate inference.

Citations are **co-emitted** with claims during generation; there is no path
that writes prose and staples citations on afterward.

## Consequences

- The cheap deterministic leg catches the most common, most damaging failure
  before any model judgement is spent.
- The two legs fail differently, so together they cover more than either alone.
- Co-emission means "re-grounding" is regenerating a claim from evidence, not
  relabelling fixed prose — which is what prevents citation theatre.
