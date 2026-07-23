# 3. A pluggable, offline-first embedder

Status: accepted

## Context

Semantic embeddings normally require an API key (and cost) or a large local
model download. That is friction for anyone who clones the repo just to see it
work, and it would make the test suite depend on a network or a secret.

## Decision

Define a small `Embedder` interface and ship two implementations. The **default
is an offline hashing embedder** (pure Python, no key, no download) that
produces real — if lexical — vectors. A real **OpenAI embedder** is a one
environment-variable switch. The store records which embedder produced each
vector and retrieval warns on a mismatch.

## Consequences

- `git clone` → run, with nothing else to set up. The whole pipeline is
  demonstrable immediately.
- Tests run offline and deterministically.
- Retrieval quality on the default backend is limited to word overlap; the
  README and `retrieval.md` are explicit that OpenAI is the semantic upgrade.
- Adding a third backend (a local model, another API) is an interface
  implementation, nothing more.
