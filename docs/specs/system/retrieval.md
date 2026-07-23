# System contract — retrieval

How text becomes vectors, and how a question finds its evidence.

## The embedder seam 🟢

Retrieval never cares how a vector was produced — only that text turns into a
normalised vector consistently. That single interface (`embed_texts`,
`embed_query`, `name`, `dim`) is the seam that lets the backend change without
touching anything downstream. See
[ADR 0003](../../adr/0003-pluggable-offline-first-embedder.md).

Two backends ship:

- **Hashing (default).** Pure-Python feature hashing — tokens hashed into a
  fixed-size, L2-normalised vector. No API key, no network, no model download,
  so the whole pipeline runs the moment the repo is cloned. Retrieval is
  *lexical* (word overlap): crude, but real and honest, and enough to exercise
  every downstream stage.
- **OpenAI.** Real semantic embeddings via the embeddings API. The upgrade you
  switch to (`GROUNDED_EMBEDDER=openai`) when you want retrieval that
  understands meaning rather than shared words.
- **Ollama.** The same semantic quality, but from a model running locally
  (`GROUNDED_EMBEDDER=ollama`) — free and offline. See
  [ADR 0009](../../adr/0009-local-inference-via-ollama.md).

A corpus is only comparable to a query embedded by the **same** backend, so the
store records `embed_model` per chunk and retrieval warns on a mismatch. Changing
backend means re-ingesting.

## Similarity search 🟢

Because every stored and query vector is L2-normalised, cosine similarity is a
dot product. All chunk vectors stack into one matrix; a query scores against the
whole matrix and the top-k are returned. Brute force — exact, simple, and fast
enough well into tens of thousands of chunks. See
[ADR 0004](../../adr/0004-sqlite-brute-force-retrieval.md).

## Deferred seams

- **Vector database (pgvector, etc.)** ⏸ — the drop-in replacement for the
  brute-force matrix when a corpus outgrows memory. The `Retriever` class is the
  only thing that changes.
- **Hybrid retrieval** ⏸ — combining lexical (BM25) and dense scores with rank
  fusion. A natural Phase 4 refinement; the candidate-set contract already
  accommodates it.
- **Reranking** ⏸ — a cross-encoder second pass for precision on the final
  shortlist, used where it matters rather than always-on.
