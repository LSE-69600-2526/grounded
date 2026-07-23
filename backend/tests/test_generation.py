"""Tests for Phase 2: generation parsing, verification, and answer composition.

All offline. The LLM is replaced by a MockGenerator, and the verification legs
are pure string work, so nothing here needs a network or an API key.
"""

from __future__ import annotations

import os

import pytest

from grounded.answer import compose_answer, persist_answer
from grounded.config import Settings
from grounded.embedder import get_embedder
from grounded.generator import Claim, MockGenerator, get_generator, parse_response
from grounded.ingest import ingest_path
from grounded.retrieve import Result
from grounded.store import Chunk, Store
from grounded.verify import verify_claims


def _result(chunk_id: int, text: str, title: str = "Doc") -> Result:
    chunk = Chunk(
        id=chunk_id, source_id=1, ord=0, text=text, source_title=title, source_path="/x"
    )
    return Result(score=1.0, chunk=chunk)


# --- parser ---------------------------------------------------------------

def test_parse_response_extracts_valid_claims():
    raw = '{"claims": [{"text": "A", "quote": "q", "source_id": 3}]}'
    claims = parse_response(raw, valid_ids={3})
    assert claims == [Claim(text="A", quote="q", source_id=3)]


def test_parse_response_tolerates_surrounding_prose_and_fences():
    raw = 'Here you go:\n```json\n{"claims": [{"text": "A", "quote": "q", "source_id": 1}]}\n```'
    claims = parse_response(raw, valid_ids={1})
    assert len(claims) == 1 and claims[0].text == "A"


def test_parse_response_skips_malformed_entries():
    raw = '{"claims": [{"text": "ok", "quote": "q", "source_id": 1}, {"text": 5}, "junk"]}'
    claims = parse_response(raw, valid_ids={1})
    assert len(claims) == 1


def test_parse_response_handles_non_json():
    assert parse_response("I don't know.", valid_ids=set()) == []


# --- verification (the headline behaviour) --------------------------------

def test_verify_passes_a_real_quote():
    results = [_result(1, "The sky appears blue because of Rayleigh scattering.")]
    claims = [Claim("Sky is blue due to scattering", "because of Rayleigh scattering", 1)]
    verified = verify_claims(claims, results)
    assert verified[0].verified
    assert verified[0].chunk is not None


def test_verify_flags_a_fabricated_quote():
    results = [_result(1, "The sky appears blue because of Rayleigh scattering.")]
    claims = [Claim("Sky is blue because of pollution", "because of pollution", 1)]
    verified = verify_claims(claims, results)
    assert not verified[0].verified
    assert "does not appear" in verified[0].reason


def test_verify_flags_citation_to_unretrieved_source():
    results = [_result(1, "some text")]
    claims = [Claim("claim", "some text", 999)]  # id 999 was never retrieved
    verified = verify_claims(claims, results)
    assert not verified[0].verified
    assert "not among the retrieved" in verified[0].reason


def test_verify_is_whitespace_and_case_insensitive():
    results = [_result(1, "Naps of about ninety minutes\nproduced the largest gains.")]
    # Quote differs in spacing and case but is faithful.
    claims = [Claim("Long naps help most", "naps of about ninety minutes produced the LARGEST gains", 1)]
    verified = verify_claims(claims, results)
    assert verified[0].verified


# --- end-to-end composition, still offline --------------------------------

def test_compose_and_persist_over_sample_corpus(tmp_path):
    settings = Settings(db_path=str(tmp_path / "t.db"), embedder="hashing", hashing_dim=512)
    store = Store(settings.db_path)
    embedder = get_embedder(settings)
    corpus = os.path.join(os.path.dirname(__file__), "..", "sample_corpus")
    ingest_path(store, embedder, corpus, settings)

    from grounded.retrieve import Retriever

    results = Retriever(store, embedder).search("do naps help memory", k=3)
    assert results

    # Build a mock generator: one faithful claim, one fabricated, from real chunks.
    top = results[0].chunk
    real_quote = " ".join(top.text.split()[3:9])  # a genuine span of the top chunk
    generator = MockGenerator(
        [
            Claim("A real, grounded claim", real_quote, top.id),
            Claim("A fabricated claim", "this exact phrase is not in any source", top.id),
        ]
    )

    answer = compose_answer("do naps help memory", results, generator)
    answer_id = persist_answer(store, answer)

    assert len(answer.verified_claims) == 1
    assert len(answer.flagged_claims) == 1
    assert answer_id > 0
    # Persisted rows match.
    rows = store._conn.execute(
        "SELECT status FROM claims WHERE answer_id = ? ORDER BY id", (answer_id,)
    ).fetchall()
    store.close()
    assert sorted(r[0] for r in rows) == ["unsupported", "verified"]


def test_get_generator_auto_is_none_without_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    settings = Settings(generator="auto")
    assert get_generator(settings) is None


def test_get_generator_none_is_explicit():
    assert get_generator(Settings(generator="none")) is None
