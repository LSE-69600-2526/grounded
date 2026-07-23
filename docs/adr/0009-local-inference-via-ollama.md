# 9. Local inference via Ollama (a free, offline mode)

Status: accepted

## Context

Generation and (optionally) semantic embeddings require a model. The OpenAI
backend is cheap but needs an API key, a funded account, and a network call per
request. For a portfolio project we also want a path that costs nothing and runs
without any account at all.

## Decision

Support **Ollama** as a local backend for both generation and embeddings. Ollama
runs a model on the user's own machine and exposes an **OpenAI-compatible**
endpoint at `http://localhost:11434/v1`. Because the wire format matches, the
same client code serves both: a shared `make_client(base_url, api_key)` helper
builds either a cloud OpenAI client or a local Ollama client, and the generator
and embedder classes are otherwise identical. Selection is by setting
(`GROUNDED_GENERATOR=ollama`, `GROUNDED_EMBEDDER=ollama`).

## Consequences

- A fully offline, zero-cost mode: local hashing or Ollama embeddings + local
  Ollama generation + the deterministic verifier means no data leaves the
  machine and no bill is incurred.
- The tradeoff is honest and documented: local models are smaller and rougher
  than the paid frontier, and inference uses the user's own hardware/RAM. The
  extraction-and-quote task is well within reach of small models, and the
  deterministic quote check catches failures regardless of model quality.
- Adding Ollama cost almost no new code, which validates the pluggable-backend
  seams from ADRs 0003 and 0008.
- The `name` of a local backend is prefixed `ollama:` so the store records which
  model embedded a corpus (a corpus is only comparable to a query from the same
  backend — see docs/specs/system/retrieval.md).
