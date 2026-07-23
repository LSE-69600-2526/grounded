"""Persistent storage for the corpus.

A deliberately tiny data model -- two tables -- backed by SQLite so there is no
database to run. The important design choice: each chunk keeps its *exact*
source text (``chunks.text``). That stored text is the frozen record the later
verification step checks quotes against, so we never trust the model's memory of
a source over what was actually retrieved.

Embeddings are stored as raw float32 bytes. Similarity search loads them into a
matrix and does brute-force cosine in NumPy -- perfect up to tens of thousands
of chunks. pgvector is the drop-in upgrade when a corpus outgrows that.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone

import numpy as np

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
    id        INTEGER PRIMARY KEY,
    path      TEXT UNIQUE NOT NULL,
    title     TEXT NOT NULL,
    added_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS chunks (
    id          INTEGER PRIMARY KEY,
    source_id   INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    ord         INTEGER NOT NULL,
    text        TEXT NOT NULL,
    embedding   BLOB NOT NULL,
    embed_model TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chunks_source ON chunks(source_id);
CREATE TABLE IF NOT EXISTS answers (
    id         INTEGER PRIMARY KEY,
    question   TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS claims (
    id          INTEGER PRIMARY KEY,
    answer_id   INTEGER NOT NULL REFERENCES answers(id) ON DELETE CASCADE,
    claim_text  TEXT NOT NULL,
    quote       TEXT NOT NULL,
    chunk_id    INTEGER,
    status      TEXT NOT NULL,
    reason      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_claims_answer ON claims(answer_id);
"""


@dataclass
class Chunk:
    """A stored chunk with its source context."""

    id: int
    source_id: int
    ord: int
    text: str
    source_title: str
    source_path: str


class Store:
    """Thin wrapper over a SQLite corpus database."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.executescript(_SCHEMA)

    def close(self) -> None:
        self._conn.close()

    def reset(self) -> None:
        """Drop all data. Used by ``grounded reset`` and the tests."""
        self._conn.executescript(
            "DELETE FROM claims; DELETE FROM answers; "
            "DELETE FROM chunks; DELETE FROM sources;"
        )
        self._conn.commit()

    def replace_source(
        self,
        path: str,
        title: str,
        chunk_texts: list[str],
        embeddings: np.ndarray,
        embed_model: str,
    ) -> int:
        """Insert a source and its chunks, replacing any existing source at path.

        Re-ingesting the same path is idempotent: the old rows are removed first,
        so repeated ingest never duplicates a document.
        """
        assert embeddings.shape[0] == len(chunk_texts), "one embedding per chunk"
        cur = self._conn.cursor()
        cur.execute("DELETE FROM sources WHERE path = ?", (path,))
        cur.execute(
            "INSERT INTO sources (path, title, added_at) VALUES (?, ?, ?)",
            (path, title, datetime.now(timezone.utc).isoformat()),
        )
        source_id = int(cur.lastrowid)
        rows = [
            (
                source_id,
                ordinal,
                text,
                embeddings[ordinal].astype(np.float32).tobytes(),
                embed_model,
            )
            for ordinal, text in enumerate(chunk_texts)
        ]
        cur.executemany(
            "INSERT INTO chunks (source_id, ord, text, embedding, embed_model) "
            "VALUES (?, ?, ?, ?, ?)",
            rows,
        )
        self._conn.commit()
        return source_id

    def load_matrix(self) -> tuple[list[Chunk], np.ndarray, set[str]]:
        """Load every chunk plus a stacked embedding matrix for search.

        Returns the chunks (in row order), an (n, dim) float32 matrix aligned to
        them, and the set of embed model names present (used to warn if the
        corpus was built with a different embedder than the current one).
        """
        cur = self._conn.execute(
            "SELECT c.id, c.source_id, c.ord, c.text, c.embedding, c.embed_model, "
            "       s.title AS source_title, s.path AS source_path "
            "FROM chunks c JOIN sources s ON s.id = c.source_id "
            "ORDER BY c.id"
        )
        chunks: list[Chunk] = []
        vectors: list[np.ndarray] = []
        models: set[str] = set()
        for row in cur:
            chunks.append(
                Chunk(
                    id=row["id"],
                    source_id=row["source_id"],
                    ord=row["ord"],
                    text=row["text"],
                    source_title=row["source_title"],
                    source_path=row["source_path"],
                )
            )
            vectors.append(np.frombuffer(row["embedding"], dtype=np.float32))
            models.add(row["embed_model"])
        matrix = np.vstack(vectors) if vectors else np.zeros((0, 0), dtype=np.float32)
        return chunks, matrix, models

    def save_answer(self, question: str, claim_rows: list[tuple]) -> int:
        """Persist an answer and its verified claims.

        Args:
            question: The question that was asked.
            claim_rows: One tuple per claim, as
                ``(claim_text, quote, chunk_id_or_none, status, reason)``.

        Returns:
            The new answer id.
        """
        cur = self._conn.cursor()
        cur.execute(
            "INSERT INTO answers (question, created_at) VALUES (?, ?)",
            (question, datetime.now(timezone.utc).isoformat()),
        )
        answer_id = int(cur.lastrowid)
        cur.executemany(
            "INSERT INTO claims (answer_id, claim_text, quote, chunk_id, status, reason) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            [(answer_id, *row) for row in claim_rows],
        )
        self._conn.commit()
        return answer_id

    def counts(self) -> tuple[int, int]:
        """Return (source_count, chunk_count)."""
        s = self._conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
        c = self._conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        return int(s), int(c)
