"""Tests for the judge (the semantic verification leg) and its integration.

All offline: the judge is a MockJudge, so no network or key is needed. The key
behaviour under test is that a *real* quote paired with an *unsupported* claim --
which the deterministic check alone would pass -- gets caught by the judge.
"""

from __future__ import annotations

from grounded.answer import compose_answer
from grounded.config import Settings
from grounded.generator import Claim, MockGenerator
from grounded.judge import (
    MockJudge,
    OllamaJudge,
    get_judge,
    parse_verdict,
)
from grounded.retrieve import Result
from grounded.store import Chunk


def _result(chunk_id: int, text: str, title: str = "Doc") -> Result:
    chunk = Chunk(chunk_id, 1, 0, text, title, "/x")
    return Result(score=1.0, chunk=chunk)


# --- verdict parsing ------------------------------------------------------

def test_parse_verdict_reads_json():
    assert parse_verdict('{"tier": "direct_quote", "why": "x"}') == "direct_quote"
    assert parse_verdict('{"tier": "inferred"}') == "inferred"
    assert parse_verdict('{"tier": "unsupported"}') == "unsupported"


def test_parse_verdict_defaults_to_unsupported_on_garbage():
    # Safe direction: unrecognised output should not pass a claim.
    assert parse_verdict("no json here and no keyword") == "unsupported"


def test_parse_verdict_keyword_fallback():
    assert parse_verdict("I think this is inferred from the passage.") == "inferred"


# --- the judge as the second leg ------------------------------------------

def test_judge_assigns_tier_to_a_real_supported_claim():
    results = [_result(1, "Naps improve recall of recently learned material.")]
    gen = MockGenerator([Claim("Naps improve recall", "Naps improve recall", 1)])
    answer = compose_answer("q", results, gen, MockJudge("direct_quote"))
    assert answer.verified_claims
    assert answer.verified_claims[0].tier == "direct_quote"


def test_judge_downgrades_real_quote_that_does_not_support_claim():
    # The quote is genuinely in the source (deterministic check passes)...
    passage = "Caffeine consumed late in the day can delay sleep onset."
    results = [_result(1, passage)]
    gen = MockGenerator([Claim("Caffeine improves sleep", "can delay sleep onset", 1)])
    # ...but the judge sees the claim isn't supported and flags it.
    answer = compose_answer("q", results, gen, MockJudge("unsupported"))
    assert not answer.verified_claims
    assert answer.flagged_claims
    assert "does not support" in answer.flagged_claims[0].reason


def test_judge_not_run_on_a_fabricated_quote():
    # A quote that isn't present fails the deterministic leg; the judge, which
    # would raise here, must never be called for it.
    results = [_result(1, "real text")]
    gen = MockGenerator([Claim("bogus", "not in the source", 1)])

    def exploding_judge(_c, _p):
        raise AssertionError("judge should not run on a quote-check failure")

    answer = compose_answer("q", results, gen, MockJudge(exploding_judge))
    assert not answer.verified_claims
    assert answer.flagged_claims[0].reason.startswith("the quoted text")


def test_compose_without_judge_leaves_tier_none():
    results = [_result(1, "Naps improve recall.")]
    gen = MockGenerator([Claim("Naps improve recall", "Naps improve recall", 1)])
    answer = compose_answer("q", results, gen, judge=None)
    assert answer.verified_claims[0].tier is None


# --- backend selection ----------------------------------------------------

def test_get_judge_none_without_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert get_judge(Settings(generator="auto", judge="auto")) is None


def test_get_judge_follows_generator_when_auto():
    # judge=auto should follow an explicit ollama generator.
    j = get_judge(Settings(generator="ollama", judge="auto", ollama_model="llama3.1"))
    assert isinstance(j, OllamaJudge)
    assert j.name == "ollama:llama3.1"


def test_get_judge_explicit_ollama():
    j = get_judge(Settings(judge="ollama"))
    assert isinstance(j, OllamaJudge)
