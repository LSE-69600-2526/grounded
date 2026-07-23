# 5. Frozen chunk text is the substrate for verification

Status: accepted

## Context

Verification must decide whether a claim's quote really came from a source. If
it checked against a freshly re-parsed document, or worse against the model's
paraphrase, the check could pass on text the model never actually read.

## Decision

At ingest, store each chunk's **verbatim text** and treat that stored text as
the frozen record. Every later check — the deterministic quote-presence test in
particular — runs against this stored text, i.e. against exactly what retrieval
handed the model. Original file bytes are not retained; the frozen chunks are
the record of what a source said.

## Consequences

- The quote-presence check is meaningful: it compares the model's cited quote to
  the precise text that was available to cite.
- Chunking must preserve source text faithfully (only outer whitespace trimmed),
  which constrains the chunker.
- A corrected document is handled by re-ingesting it as new chunks, not by
  mutating stored text.
