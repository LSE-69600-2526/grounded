"""Answer generation with co-emitted citations.

The contract (see docs/specs/system/pipeline.md): given a question and the chunks
retrieval returned, produce a list of **claims**, each carrying the verbatim
quote it rests on and the id of the chunk that quote came from. The citation is
emitted *with* the claim -- there is no path that writes prose first and attaches
sources afterward, which is where fabrication creeps in.

Like the embedder, generation is a swappable backend and is *optional*: with no
model configured the tool falls back to showing retrieved passages (Phase 1
behaviour). See docs/adr/0008-optional-pluggable-generation.md.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Protocol

from .retrieve import Result

_PROMPT = """You answer questions strictly from the numbered sources below.

Rules:
- Make claims ONLY if a source supports them. Do not use outside knowledge.
- Every claim must quote the exact supporting text, copied verbatim from one source.
- Cite the source by its id number.
- If the sources do not answer the question, return an empty "claims" list.

Return ONLY a JSON object of this exact shape, nothing else:
{{"claims": [{{"text": "<the claim>", "quote": "<verbatim span from the source>", "source_id": <id number>}}]}}

Question: {question}

Sources:
{sources}
"""


@dataclass
class Claim:
    """A model-produced claim with the citation it was emitted with.

    ``text`` is the assertion, ``quote`` is the verbatim span the model says
    supports it, and ``source_id`` is the chunk id it attributes the quote to.
    None of this is trusted yet -- verification checks it (see verify.py).
    """

    text: str
    quote: str
    source_id: int


class Generator(Protocol):
    """Anything that turns a question + retrieved chunks into cited claims."""

    name: str

    def generate(self, question: str, results: list[Result]) -> list[Claim]:
        ...


def build_prompt(question: str, results: list[Result]) -> str:
    """Render the generation prompt, labelling each source with its chunk id."""
    blocks = []
    for res in results:
        c = res.chunk
        blocks.append(f"[id={c.id}] ({c.source_title})\n{c.text}")
    return _PROMPT.format(question=question, sources="\n\n".join(blocks))


def parse_response(text: str, valid_ids: set[int]) -> list[Claim]:
    """Parse the model's JSON into claims, keeping only well-formed ones.

    Pure and side-effect-free so it can be tested without a network call. A
    claim whose ``source_id`` is not among the retrieved chunks is still parsed
    (verification will flag it as a mis-citation); malformed entries are skipped.
    """
    # Tolerate accidental code fences or prose around the JSON object.
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return []
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []

    claims: list[Claim] = []
    for item in data.get("claims", []):
        if not isinstance(item, dict):
            continue
        text_val = item.get("text")
        quote_val = item.get("quote")
        source_val = item.get("source_id")
        if not isinstance(text_val, str) or not isinstance(quote_val, str):
            continue
        try:
            source_id = int(source_val)
        except (TypeError, ValueError):
            continue
        claims.append(Claim(text=text_val.strip(), quote=quote_val.strip(), source_id=source_id))
    return claims


class MockGenerator:
    """A canned generator for offline tests -- returns preset claims verbatim."""

    def __init__(self, claims: list[Claim]) -> None:
        self._claims = claims
        self.name = "mock"

    def generate(self, question: str, results: list[Result]) -> list[Claim]:
        return list(self._claims)


class OpenAIGenerator:
    """Generation via an OpenAI chat model with JSON output."""

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "The 'openai' package is required for OpenAIGenerator. "
                "Install it with: pip install openai"
            ) from exc
        self._client = OpenAI()
        self.model = model
        self.name = model

    def generate(self, question: str, results: list[Result]) -> list[Claim]:
        if not results:
            return []
        prompt = build_prompt(question, results)
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0,
        )
        content = resp.choices[0].message.content or ""
        valid_ids = {r.chunk.id for r in results}
        return parse_response(content, valid_ids)


def get_generator(settings) -> Generator | None:
    """Build the configured generator, or None for retrieval-only mode.

    "auto" enables OpenAI generation when an API key is present and otherwise
    returns None, so the tool runs with zero setup and lights up when a key is
    added. See docs/adr/0008-optional-pluggable-generation.md.
    """
    import os

    mode = settings.generator
    if mode == "none":
        return None
    if mode == "auto":
        mode = "openai" if os.environ.get("OPENAI_API_KEY") else "none"
    if mode == "none":
        return None
    if mode == "openai":
        return OpenAIGenerator(settings.openai_chat_model)
    raise ValueError(f"Unknown generator: {settings.generator!r}")
