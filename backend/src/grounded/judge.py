"""The judge -- the second verification leg.

The deterministic check (verify.py) proves a quote *exists* in its cited source.
It cannot tell whether that source actually *supports* the claim: a real quote
can be paired with a claim it contradicts, narrows, or merely shares a topic
with. The judge closes that gap.

It is a narrow LLM call, one per claim, shown only the claim and its cited
passage and asked a single question: does the passage support the claim as
worded? It returns a grounding tier:

- ``direct_quote`` -- the claim is the source stated plainly.
- ``inferred``     -- the source reasonably implies the claim.
- ``unsupported``  -- the passage does not back the claim (contradiction,
  topic-only overlap, dropped caveat, reversed direction, wrong population).

Design stance: **permissive about legitimate inference, strict about
attribution fidelity** (scope, direction, magnitude, caveats, population). A
fair paraphrase passes; a meaning change does not. Separating this critic from
the generator matters -- the generator is biased toward a fluent, complete
answer, while a judge with one narrow job is a harsher, more reliable check.
See docs/adr/0010-llm-judge-grounding-tiers.md.
"""

from __future__ import annotations

import re
from typing import Protocol

TIERS = ("direct_quote", "inferred", "unsupported")

_PROMPT = """You are a strict grounding checker. You are shown a CLAIM and a PASSAGE.
Decide whether the passage supports the claim *as worded*.

Be permissive about legitimate inference and fair paraphrase, but strict about
attribution fidelity: scope, direction, magnitude, caveats, and population must
be preserved. Topical relevance is NOT support. If the passage contradicts,
narrows, or only shares a topic with the claim, it is unsupported.

Answer with ONLY a JSON object of this exact shape, nothing else:
{{"tier": "direct_quote" | "inferred" | "unsupported", "why": "<one short sentence>"}}

CLAIM: {claim}

PASSAGE: {passage}
"""


def build_prompt(claim: str, passage: str) -> str:
    """Render the judge prompt for a single claim/passage pair."""
    return _PROMPT.format(claim=claim, passage=passage)


def parse_verdict(text: str) -> str:
    """Parse the judge's JSON into one of TIERS.

    Pure and side-effect-free for offline testing. Anything unrecognised is
    treated as ``unsupported`` -- the safe direction (we would rather flag a
    good claim than pass a bad one).
    """
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        import json

        try:
            tier = json.loads(match.group(0)).get("tier", "")
            if tier in TIERS:
                return tier
        except json.JSONDecodeError:
            pass
    # Fall back to a keyword scan if the model didn't emit clean JSON.
    lowered = text.lower()
    for tier in TIERS:
        if tier.replace("_", " ") in lowered or tier in lowered:
            return tier
    return "unsupported"


class Judge(Protocol):
    """Anything that can rate how well a passage supports a claim."""

    name: str

    def judge(self, claim: str, passage: str) -> str:
        ...


class MockJudge:
    """Offline judge for tests.

    Constructed either with a fixed verdict, or with a callable
    ``(claim, passage) -> tier`` to script per-claim behaviour.
    """

    def __init__(self, verdict="inferred") -> None:
        self._verdict = verdict
        self.name = "mock"

    def judge(self, claim: str, passage: str) -> str:
        if callable(self._verdict):
            return self._verdict(claim, passage)
        return self._verdict


class _ChatJudge:
    """Shared judge logic over any OpenAI-compatible chat client."""

    def __init__(self, client, model: str, name: str) -> None:
        self._client = client
        self.model = model
        self.name = name

    def judge(self, claim: str, passage: str) -> str:
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": build_prompt(claim, passage)}],
            response_format={"type": "json_object"},
            temperature=0,
        )
        return parse_verdict(resp.choices[0].message.content or "")


class OpenAIJudge(_ChatJudge):
    """Judge via the OpenAI API."""

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        from .llm_client import make_client

        super().__init__(make_client(), model=model, name=model)


class OllamaJudge(_ChatJudge):
    """Judge via a local Ollama server -- free, offline."""

    def __init__(
        self, model: str = "llama3.1", base_url: str = "http://localhost:11434/v1"
    ) -> None:
        from .llm_client import make_client

        client = make_client(base_url=base_url, api_key="ollama")
        super().__init__(client, model=model, name=f"ollama:{model}")


def get_judge(settings) -> Judge | None:
    """Build the judge, or None when no LLM backend is available.

    Defaults to following the generator backend ("auto"): if you generate with
    Ollama, you judge with Ollama; with OpenAI, OpenAI. Override with
    GROUNDED_JUDGE. Returns None when the resolved backend is "none", in which
    case only the deterministic quote check runs.
    """
    from .generator import resolve_backend

    mode = settings.judge
    if mode == "auto":
        mode = resolve_backend(settings.generator)
    else:
        mode = resolve_backend(mode)

    if mode == "none":
        return None
    if mode == "openai":
        return OpenAIJudge(settings.openai_chat_model)
    if mode == "ollama":
        return OllamaJudge(settings.ollama_model, settings.ollama_base_url)
    raise ValueError(f"Unknown judge backend: {settings.judge!r}")
