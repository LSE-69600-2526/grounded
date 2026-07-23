"""Retrieval: find the chunks most relevant to a question.

Because every stored vector and every query vector is L2-normalised, cosine
similarity is just a dot product. We stack all chunk vectors into one matrix and
take the top-k scores -- brute force, but exact and plenty fast for a
project-scale corpus. The seam to a vector database (pgvector, etc.) is this one
class; nothing above it would change.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .embedder import Embedder
from .store import Chunk, Store


@dataclass
class Result:
    """A retrieved chunk with its similarity score."""

    score: float
    chunk: Chunk


class Retriever:
    """Loads the corpus into memory once and answers similarity queries."""

    def __init__(self, store: Store, embedder: Embedder) -> None:
        self._embedder = embedder
        self._chunks, self._matrix, models = store.load_matrix()
        # A corpus embedded with a different backend won't compare meaningfully.
        if models and embedder.name not in models:
            self.embedder_mismatch = (
                f"corpus was embedded with {sorted(models)} but the active "
                f"embedder is {embedder.name!r}; re-ingest to compare correctly"
            )
        else:
            self.embedder_mismatch = None

    @property
    def is_empty(self) -> bool:
        return len(self._chunks) == 0

    def search(self, query: str, k: int = 5) -> list[Result]:
        """Return the top-``k`` chunks most similar to ``query``."""
        if self.is_empty:
            return []
        q = self._embedder.embed_query(query)
        scores = self._matrix @ q  # cosine, since everything is normalised
        k = min(k, len(self._chunks))
        top = np.argpartition(-scores, k - 1)[:k]
        top = top[np.argsort(-scores[top])]
        return [Result(score=float(scores[i]), chunk=self._chunks[i]) for i in top]
