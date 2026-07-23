# 8. Generation is optional and provider-pluggable

Status: accepted

## Context

Answer generation needs an LLM, which means an API key and cost. Retrieval,
chunking, and the deterministic verification leg need neither. Forcing a key
just to run the tool would undo the zero-setup property established for
embeddings (ADR 0003), and would make a first look at the repo cost money.

## Decision

Generation sits behind a small `Generator` interface, mirroring the embedder
seam. It is **optional**: the default mode is `auto`, which enables the OpenAI
backend when `OPENAI_API_KEY` is present and otherwise falls back to
**retrieval-only** (the tool shows the passages it found and says generation is
off). A `MockGenerator` provides canned claims so the whole generate-verify
pipeline is testable offline.

## Consequences

- `git clone` still runs with nothing configured; adding a key lights up full
  answers with no code change.
- The generate-verify path is covered by offline tests via the mock, with no
  network dependency in the default suite.
- Swapping OpenAI for another provider (or a local model) is one interface
  implementation. The deterministic verification leg is provider-independent by
  construction.
