"""End-to-end tests for the ingest and retrieval pipeline.

These run entirely offline against the hashing embedder, so they need no API key
and no network. They mirror the source layout: one module of tests per behaviour
that matters.
"""

from __future__ import annotations

import os

import pytest

from grounded.chunker import chunk_text
from grounded.config import Settings
from grounded.embedder import HashingEmbedder, get_embedder
from grounded.ingest import ingest_path
from grounded.retrieve import Retriever
from grounded.store import Store


@pytest.fixture()
def settings(tmp_path) -> Settings:
    return Settings(
        db_path=str(tmp_path / "test.db"),
        embedder="hashing",
        hashing_dim=512,
        chunk_size=400,
        chunk_overlap=60,
    )


@pytest.fixture()
def corpus_dir() -> str:
    here = os.path.dirname(__file__)
    return os.path.join(here, "..", "sample_corpus")


def test_chunk_text_covers_document_with_overlap():
    text = "para one.\n\n" + ("word " * 300)
    pieces = chunk_text(text, size=400, overlap=60)
    assert len(pieces) > 1
    # Every chunk is a verbatim, non-empty slice of the source.
    for piece in pieces:
        assert piece.strip() == piece
        assert piece in text or piece.replace("  ", " ") in text.replace("  ", " ")


def test_chunk_text_rejects_bad_overlap():
    with pytest.raises(ValueError):
        chunk_text("hello", size=100, overlap=100)


def test_ingest_reports_documents_and_chunks(settings, corpus_dir):
    store = Store(settings.db_path)
    embedder = get_embedder(settings)
    report = ingest_path(store, embedder, corpus_dir, settings)
    sources, chunks = store.counts()
    store.close()
    assert report.documents == 3
    assert report.chunks == chunks > 0
    assert sources == 3


def test_reingest_is_idempotent(settings, corpus_dir):
    store = Store(settings.db_path)
    embedder = get_embedder(settings)
    ingest_path(store, embedder, corpus_dir, settings)
    first = store.counts()
    ingest_path(store, embedder, corpus_dir, settings)
    second = store.counts()
    store.close()
    assert first == second  # replacing, not duplicating


def test_retrieval_ranks_the_relevant_document_first(settings, corpus_dir):
    store = Store(settings.db_path)
    embedder = get_embedder(settings)
    ingest_path(store, embedder, corpus_dir, settings)
    retriever = Retriever(store, embedder)

    top = retriever.search("do naps improve memory consolidation", k=3)
    store.close()

    assert top, "expected at least one result"
    # The sleep/memory document should win on a sleep/memory question.
    assert "sleep" in top[0].chunk.source_title.lower() or "memory" in top[0].chunk.text.lower()
    # Scores are sorted descending.
    assert all(a.score >= b.score for a, b in zip(top, top[1:]))


def test_empty_corpus_returns_no_results(settings):
    store = Store(settings.db_path)
    retriever = Retriever(store, HashingEmbedder(settings.hashing_dim))
    assert retriever.is_empty
    assert retriever.search("anything", k=5) == []
    store.close()
