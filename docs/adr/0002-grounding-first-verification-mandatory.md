# 2. Grounding is the product; verification is not optional

Status: accepted

## Context

This tool descends from a large evidence-analysis platform with many
capabilities — acquisition, planning, steering, multi-stage synthesis. Trying to
reproduce all of it would produce an unfinished imitation. A focused project
needs a single defensible thesis.

## Decision

The thesis is the **grounding-and-verification discipline**: an answer whose
every claim is checked against the source it cites. Everything else from the
parent system — going out to find evidence, planning runs, human-in-the-loop
steering, multi-user hosting — is explicitly out of scope (see
`docs/specs/product.md`). Verification is a mandatory stage of the pipeline, not
a feature that can be toggled off.

## Consequences

- The project is finishable and has a clear, memorable identity.
- The hardest and most valuable part of the parent system is what we keep; the
  operationally heavy parts are what we drop.
- Scope discipline is enforced in specs and ADRs so the project doesn't
  gradually regrow the whole platform.
