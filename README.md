# Grounded

A document question-answering tool built around a single, uncompromising
property: **it cannot fabricate a citation.** Every claim in an answer is
generated *from* a retrieved source, checked that the quoted text actually
exists in that source, and re-checked that the source genuinely supports the
claim as worded. Anything that fails is shown with an honest flag rather than
quietly dropped — and if the corpus can't answer a question, Grounded says so
instead of inventing an answer.

Most "chat with your documents" tools optimise for a fluent reply and let
hallucination slip through. Grounded is defined by the opposite property: an
answer you can interrogate sentence by sentence.

> This is a focused study of the grounding-and-verification discipline drawn
> from a much larger evidence-analysis platform. It keeps that platform's
> trust invariant and documentation approach, and deliberately drops its
> orchestration, multi-capability pipeline, and steering machinery. See
> [`docs/adr/`](docs/adr) for why.

## The idea in one picture

```
Ingest (once)  ── parse → chunk → embed → store frozen text + vectors
                                   │
        ┌──────────────────────────┘   (per question)
        ▼
   Retrieve   top matching chunks
        ▼
   Generate   claim + supporting quote + source id   (structured, not prose)
        ▼
   Verify     ① quote present in the frozen chunk?  (deterministic)
              ② does the source support the claim?  (LLM judge → tier)
              └─ fail → reword down or flag, never delete
        ▼
   Render     answer with per-claim citations, tiers, and gaps
```

The stored chunk text is the *frozen record*: verification always checks the
model against what was actually retrieved, never against the model's memory of a
source.

## Status

| Phase | Scope | State |
|---|---|---|
| 1 | Ingest + retrieve | **built** — this repo |
| 2 | Generate claims with co-emitted citations + deterministic quote check | next |
| 3 | LLM-judge grounding tiers + flag-don't-drop rendering | planned |
| 4 (stretch) | Evaluation set, hybrid retrieval, web UI | planned |

See [`docs/roadmap.md`](docs/roadmap.md).

## Layout

```
backend/                  Python project
  src/grounded/
    config.py             settings (env-overridable, zero-config defaults)
    embedder.py           embedding backends (offline hashing · OpenAI)
    chunker.py            document → overlapping verbatim chunks
    loaders.py            txt/markdown loaders (PDF is a planned extension)
    store.py              SQLite corpus (sources + chunks + vectors)
    ingest.py             the ingest pipeline
    retrieve.py           cosine similarity search
    cli.py                the command-line entry point
  tests/                  mirrors src; runs fully offline
  sample_corpus/          three small documents to try it on
docs/
  specs/                  living product + system contracts
  adr/                    numbered architecture decision records
  roadmap.md
```

## Setup

Requires Python ≥ 3.10. No database to run, no API key needed for the default
(offline) embedder.

```sh
cd backend
pip install -e .            # add ".[openai]" for semantic embeddings, ".[dev]" for tests
```

## Use it

```sh
grounded ingest sample_corpus              # build the corpus
grounded stats                             # what's in it
grounded ask "do naps help memory?" -k 3   # retrieve the most relevant passages
```

Switch from offline lexical matching to real semantic embeddings by setting two
environment variables:

```sh
export GROUNDED_EMBEDDER=openai
export OPENAI_API_KEY=sk-...
grounded reset && grounded ingest sample_corpus   # re-embed under the new backend
```

## Test

```sh
cd backend && pip install -e ".[dev]" && pytest
```

## Licence

MIT — see [LICENSE](LICENSE). Maria Monserrat Perez Villanueva
