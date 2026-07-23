# 4. SQLite plus brute-force cosine, not a vector database

Status: accepted

## Context

The parent system uses Postgres with pgvector on Aurora. Standing up a database
and a vector extension is real setup cost, and at portfolio-corpus scale
(documents in the tens to low thousands) it buys nothing.

## Decision

Store the corpus in **SQLite** (a file, no server) with embeddings as raw
float32 bytes. Similarity search loads all vectors into a NumPy matrix and takes
the top-k by dot product — exact brute force. Because vectors are
L2-normalised, the dot product is cosine similarity.

## Consequences

- Zero infrastructure: no Docker, no database process.
- Exact results (no approximate-nearest-neighbour recall loss) and trivially
  simple code.
- Memory-bound and linear in corpus size. The `Retriever` class isolates this;
  swapping in pgvector or an ANN index later touches only that one class. Marked
  as a deferred seam in `retrieval.md`.
