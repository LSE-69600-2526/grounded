# Spec index

This is the map of Grounded's intent. Specs are **living** — they describe what
the system is meant to do and why, and they change when building shows them
wrong (see [AGENTS.md](../../AGENTS.md)). Architecture decisions with lasting
consequences are recorded separately as ADRs in [`../adr/`](../adr).

## What to read for a task

| If the task touches… | Read |
|---|---|
| What Grounded is and isn't; where the scope line sits | [product.md](product.md) |
| The stages a question flows through end to end | [system/pipeline.md](system/pipeline.md) |
| Claims, citations, tiers, verification, honest flags | [system/grounding.md](system/grounding.md) — the core contract |
| Sources, chunks, frozen text, stored vectors | [system/data-model.md](system/data-model.md) |
| Embedding backends and similarity search | [system/retrieval.md](system/retrieval.md) |

## Status legend

🟢 built · 🟡 leaning (provisional) · 🔵 planned · ⏸ deferred (out of scope, seam left open)
