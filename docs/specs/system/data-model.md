# System contract — data model

Deliberately small. Two tables today; a third arrives with verification.

## Sources 🟢

One row per ingested document.

| column | meaning |
|---|---|
| `id` | primary key |
| `path` | absolute path; the stable identity of a source (unique) |
| `title` | first Markdown heading, else the file name |
| `added_at` | ingest timestamp (UTC, ISO 8601) |

Re-ingesting a `path` deletes and re-inserts, so a source is never duplicated.

## Chunks 🟢

One row per chunk of a source.

| column | meaning |
|---|---|
| `id` | primary key; the citation target |
| `source_id` | owning source (cascade delete) |
| `ord` | position within the source (0-based) |
| `text` | **verbatim** chunk text — the frozen record |
| `embedding` | float32 vector, L2-normalised, stored as raw bytes |
| `embed_model` | name of the embedder that produced the vector |

The `text` column is load-bearing: verification checks quotes against it, so it
must be exactly what was in the document. `embed_model` lets retrieval warn when
a corpus was built with a different embedder than the one now active (their
vectors are not comparable — re-ingest to fix). See
[ADR 0005](../../adr/0005-frozen-chunk-text-as-substrate.md).

## Claims 🔵 (arrives with Phase 2–3)

When verification lands, each shown claim persists as a row that ties an answer
back to evidence:

| column (planned) | meaning |
|---|---|
| `claim_text` | the sentence as rendered |
| `quote` | the verbatim supporting span |
| `chunk_id` | the cited chunk |
| `tier` | direct-quote / inferred / cross-source / unsupported |
| `flag` | none / weakly-grounded / below-policy |

This stays a flat table, not a graph. The richer annotation layer of the larger
system it descends from is intentionally out of scope — see
[product.md](../product.md) and [ADR 0002](../../adr/0002-grounding-first-verification-mandatory.md).

## What is not stored

Original file bytes are not retained after parsing — the frozen chunk text is
the record of what a source said. A corrected document is simply re-ingested as
a new set of chunks.
