# 10. An LLM judge assigns grounding tiers (the second verification leg)

Status: accepted

## Context

The deterministic quote check (ADR 0006) proves a quote *exists* in its cited
source. It is blind to whether the source actually *supports* the claim: a real
quote can be attached to a claim it contradicts, narrows, or merely shares a
topic with. That is the failure mode the "trap" eval cases target.

## Decision

Add a second verification leg: a narrow LLM **judge**, one call per claim, shown
only the claim and its cited passage and asked whether the passage supports the
claim *as worded*. It returns a grounding tier — `direct_quote`, `inferred`, or
`unsupported`. A claim earns a clean tier only if it passes both legs; a real
quote the judge rejects is downgraded to flagged, not shown as grounded.

The judge is **permissive about legitimate inference, strict about attribution
fidelity** (scope, direction, magnitude, caveats, population). It is a separate
call from generation on purpose: the generator is biased toward a fluent,
complete answer, while a judge with one narrow job is a harsher, more reliable
critic. Unparseable judge output defaults to `unsupported` (fail safe).

By default the judge **follows the generator backend** (`judge=auto`): Ollama
generation judges with Ollama, OpenAI with OpenAI. `GROUNDED_JUDGE` overrides.

## Consequences

- Closes the meaning-level gap the deterministic leg cannot see; the two legs
  are complementary (fabricated quote vs. real-but-unsupported quote).
- Costs one extra LLM call per surviving claim. The quote check runs first, so
  the judge never runs on a claim whose quote isn't even present.
- Judge quality depends on model quality — a small local model is a weaker
  critic than a frontier model. The eval set (ADR 0011) is how that is measured
  rather than assumed.
- Grounding tiers are persisted on the claim record for later review.
