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

Phases 1 (ingest + retrieve) and 2 (generate + deterministic quote check) are
built and tested. The tool now produces answers whose every claim is either
verified against a source quote or flagged. Next is Phase 3: the LLM-judge
support leg that assigns a grounding tier (does the source *support* the claim,
not merely contain the quote), and honest rendering of tiers. See
[`docs/roadmap.md`](docs/roadmap.md).
