# Roadmap

Grounded is built in phases, each a self-contained increment that leaves the
tool working.

## Phase 1 — ingest + retrieve 🟢 built

Load documents, chunk them, embed, store with frozen text, and retrieve the
most relevant chunks for a question. Offline by default. This is the foundation
every later stage consumes.

Done: `config`, `embedder` (hashing + OpenAI), `chunker`, `loaders`, `store`,
`ingest`, `retrieve`, `cli`, tests.

## Phase 2 — generate + the deterministic check 🟢 built

- A `generate` step: given the question and retrieved chunks, emit claims as
  structured output, each with a co-emitted verbatim quote and source chunk id.
- The deterministic quote-presence check against frozen chunk text.
- Persist claims (see `docs/specs/system/data-model.md`).

**Built:** `generator` (mock + OpenAI, structured co-emitted citations),
`verify` (deterministic quote-presence leg), `answer` (compose + persist),
`claims`/`answers` tables, CLI wiring with a retrieval-only fallback, offline
tests. At the end of Phase 2 the tool is *honest*: it cannot show a quote that
isn't in a source.

## Phase 3 — judge + honest rendering 🔵 next

- LLM-as-judge support check assigning a grounding tier per claim.
- Flag-don't-drop rendering: tier badges, weak/unverified flags, explicit gaps.
- A minimal answer view (CLI first).

At the end of Phase 3 the tool is *distinctive*: every claim carries its
grounding, and failures are visible.

## Phase 4 — stretch 🔵

- An **evaluation set**: a handful of questions with known answers, scored for
  "% of claims verified" and "% correctly caught as unsupported." The single
  highest-value addition for a portfolio — it turns the trust claim into a
  measurement.
- Hybrid retrieval (lexical + dense with rank fusion).
- PDF ingestion.
- A small web UI where clicking a claim reveals its source span — the
  interaction that best demonstrates the whole idea.
