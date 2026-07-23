# Contributor & agent protocol

Conventions for anyone (human or AI assistant) working in this repo.

- Use the `Makefile` targets: `make setup`, `make test`, `make verify`.
- Plan before non-trivial edits; touch only what the task needs.
- Write concise Google-style docstrings (`Args:` / `Returns:` / `Raises:`) for
  public modules, classes, and functions. Trivial helpers and tests need none.
- `docs/specs/` is **living intent, not gospel.** If building shows a spec is
  wrong or improvable, change the spec in the same commit — don't silently
  deviate from it or silently obey a spec you know is wrong.
- Record consequential decisions as an ADR in `docs/adr/` (see
  [0001](docs/adr/0001-record-architecture-decisions.md)). One decision per
  file, numbered, immutable once merged (supersede rather than rewrite).
- Deterministic work (chunk boundaries, hashing, counts) is computed in code and
  covered by a test — never left to a model's judgement.
- The trust invariant in
  [`docs/specs/system/grounding.md`](docs/specs/system/grounding.md) is the
  point of the project. No change may let an unsupported claim render as though
  it were grounded. When in doubt, flag; never silently drop.
- Tests run offline by default (the hashing embedder). Don't add a test that
  needs a network call or an API key to the default suite.

## Current phase

Phases 1–3 are built and tested: ingest + retrieve, generate with co-emitted
citations + the deterministic quote check, and the LLM judge that assigns
grounding tiers (the semantic leg). A category-based eval set (`grounded eval`)
measures the trust property. Next is Phase 4 (stretch): PDF ingestion, hybrid
retrieval, and a web UI. See [`docs/roadmap.md`](docs/roadmap.md).
