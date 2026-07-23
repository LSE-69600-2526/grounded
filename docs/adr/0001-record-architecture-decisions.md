# 1. Record architecture decisions

Status: accepted

## Context

This is a portfolio project as much as a working tool. Part of its value is
showing *how* decisions were reasoned about, not just the final code. Decisions
made silently in commits are invisible six months later.

## Decision

We keep Architecture Decision Records (ADRs) in `docs/adr/`, one file per
decision, numbered sequentially. An ADR states the context, the decision, and
its consequences. ADRs are immutable once merged: a later decision that reverses
an earlier one is a new ADR that supersedes it, rather than an edit.

## Consequences

- The reasoning behind the design is legible to a reviewer reading the repo.
- Specs in `docs/specs/` describe the current intent; ADRs preserve *why* it got
  there. The two are complementary.
