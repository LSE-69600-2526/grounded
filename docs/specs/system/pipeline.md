# System contract — the pipeline

The path a question travels, and the contract each stage owes the next.

```
Ingest ──▶ Retrieve ──▶ Generate ──▶ Verify ──▶ Render
(once)      (per question ─────────────────────────────▶)
```

## Ingest — once per corpus 🟢

Load documents, split them into overlapping chunks, embed each chunk, and store
the chunk's **exact text** alongside its vector. Owns:
[data-model.md](data-model.md), [retrieval.md](retrieval.md).

- Re-ingesting the same file replaces it (idempotent), never duplicates.
- The stored chunk text is verbatim — it is the frozen record later stages
  verify against, so it must faithfully reflect the document.

## Retrieve — per question 🟢

Embed the question, score it against every stored chunk by cosine similarity,
return the top-k. Owes downstream a **traceable candidate set**: each result
carries its source identity and its score, never bare text.

## Generate — per question 🟢

Given the question and the retrieved chunks, produce a list of **claims**, each
co-emitted with (a) the verbatim quote it rests on and (b) the id of the source
chunk. Structured output, not prose. The contract: a claim may only cite a chunk
that was actually retrieved for this question. There is no path that writes prose
first and attaches citations afterward — that route manufactures plausible-looking
mis-attribution. See [ADR 0006](../../adr/0006-two-leg-verification.md).

## Verify — per question 🟢 deterministic leg · 🔵 judge leg (Phase 3)

Two independent checks per claim:

1. **Quote presence (deterministic).** The supporting quote must occur in the
   cited chunk's stored text (normalised match). A fabricated quote is a hard
   fail — no model judgement involved.
2. **Support (LLM judge).** Does the cited passage actually support the claim
   *as worded*, or is it merely on the same topic? Returns a grounding tier.

On failure, the claim is **reworded down** to what the evidence supports, or
kept with a visible flag. It is never silently deleted and never silently
promoted to a clean tier. See [grounding.md](grounding.md).

## Render — per question 🔵 (Phase 3)

Present the answer with each claim carrying its citation and tier badge, weak or
unsupported claims flagged in place, and any gaps ("nothing in this corpus
addresses X") stated explicitly.

## Invariants across the whole pipeline

- **Frozen text is the source of truth.** Verification checks the model against
  retrieved text, never against the model's memory. ([ADR 0005](../../adr/0005-frozen-chunk-text-as-substrate.md))
- **Flag, don't drop.** Nothing load-bearing disappears quietly. ([ADR 0007](../../adr/0007-flag-dont-drop.md))
- **One question, one run.** No cross-question state in v1.
