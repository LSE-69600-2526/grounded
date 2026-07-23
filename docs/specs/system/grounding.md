# System contract — grounding (the trust invariant)

This is the point of the project. The discipline that stops an ungrounded or
mis-cited statement from masquerading as grounded evidence.

## The traceability rule

Every claim in an answer is one of three honest things:

1. **Grounded** — it traces to source text, at a stated tier of strength.
2. **Flagged** — it is shown, but marked as weak, unverifiable, or unsupported.
3. **A gap** — it reports that the corpus does *not* answer something.

The cardinal sin is a statement that presents itself as source-supported but is
not supported by its cited source as worded.

## Grounding tiers 🔵 (assigned by the judge, Phase 3)

Ordered by inference distance from the evidence:

1. **Direct quote** — the claim bottoms out in a verbatim span of a source.
2. **Inferred from a single source** — one document supports it, but not word
   for word.
3. **Reasoning across sources** — synthesised from several; the claim declares
   the set it draws on.

Plus two outcomes that are **not** tiers:

- **Unsupported / mis-cited** — a failure state: the cited source does not
  support the claim as worded (fabricated quote, topical-only match, dropped
  caveat, reversed direction). Remedy: reword the claim down, or report that the
  evidence does not hold.
- **Weakly grounded** — a completeness flag on an otherwise valid claim (thin or
  cut-short support). The claim stands but is under-evidenced.

## Verification 🟢 deterministic · 🔵 judge (Phase 3)

`produce → cite → verify` runs before anything is shown, with cite and verify as
mandatory steps, not optional passes.

- **Deterministic leg.** The supporting quote must appear in the cited chunk's
  stored text under a normalised string match. This is cheap, needs no model,
  and catches the single most common and most damaging failure — an invented
  quote on a real document.
- **Judge leg.** An LLM judge reads the claim and the cited passage and assigns
  exactly one tier, or marks it unsupported. It is *permissive about legitimate
  inference* but *strict about attribution fidelity*: scope, caveats,
  population, direction, and magnitude must be preserved. Topical relevance is
  not support.

See [ADR 0006](../../adr/0006-two-leg-verification.md) for why both legs, and why
this order.

## Appraisal is a separate axis (🟡, later)

*How strong the source is* (quality) and *how far the claim is from the source*
(the tier above) are two different questions and must never be collapsed into
one confidence number. A direct quote from a weak blog is faithfully reported
yet weakly evidenced; a careful inference from strong sources is the reverse.
v1 does not appraise source quality; the tier axis ships first.

## Flag, don't drop

Every failure is surfaced, never hidden. Dropping a failed claim manufactures
false confidence (the answer looks cleaner than the evidence warrants); shipping
it unmarked is the lie the whole tool exists to prevent. The only honest move is
to show it *with its status*. See [ADR 0007](../../adr/0007-flag-dont-drop.md).
