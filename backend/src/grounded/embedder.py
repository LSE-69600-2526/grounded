"""Embedding backends.

The retrieval code never cares *how* a vector was produced -- it only needs a
consistent way to turn text into a normalised vector. That single seam is what
lets you start offline today and switch to real semantic embeddings later
without touching anything downstream.

Two backends ship:

- ``HashingEmbedder`` -- pure-Python feature hashing (bag of words hashed into a
  fixed-size vector, L2-normalised). No API key, no network, no model download.
  Retrieval is lexical (word overlap), which is crude but real and good enough
  to see the whole pipeline work. This is the default.
- ``OpenAIEmbedder`` -- real semantic embeddings. Needs ``OPENAI_API_KEY`` and
  the ``openai`` package. This is the upgrade you flip to when you want
  retrieval that understands meaning, not just shared words.
"""

from __future__ import annotations

import hashlib
import re
from typing import Protocol

import numpy as np

_TOKEN = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def _l2_normalise(vec: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vec))
    if norm == 0.0:
        return vec
    return vec / norm


class Embedder(Protocol):
    """Anything that can turn text into normalised float32 vectors."""

    name: str
    dim: int

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        """Embed a batch of documents. Returns an (n, dim) float32 array."""
        ...

    def embed_query(self, text: str) -> np.ndarray:
        """Embed a single query. Returns a (dim,) float32 array."""
        ...


class HashingEmbedder:
    """Offline, dependency-free embedder using the hashing trick.

    Each token is hashed to a bucket index and a sign; token counts accumulate
    into that bucket. The result is L2-normalised so a dot product equals cosine
    similarity. Independent per text (no fitting step), which mirrors how real
    embedding APIs behave and keeps ingest of new documents trivial.
    """

    def __init__(self, dim: int = 512) -> None:
        self.dim = dim
        self.name = f"hashing-{dim}"

    def _embed_one(self, text: str) -> np.ndarray:
        vec = np.zeros(self.dim, dtype=np.float32)
        for token in _tokenize(text):
            digest = hashlib.md5(token.encode("utf-8")).digest()
            bucket = int.from_bytes(digest[:4], "little") % self.dim
            sign = 1.0 if digest[4] & 1 else -1.0
            vec[bucket] += sign
        return _l2_normalise(vec)

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        return np.vstack([self._embed_one(t) for t in texts])

    def embed_query(self, text: str) -> np.ndarray:
        return self._embed_one(text)


class OpenAIEmbedder:
    """Real semantic embeddings via the OpenAI embeddings API.

    Requires the ``openai`` package and an ``OPENAI_API_KEY`` in the
    environment. Vectors are L2-normalised on the way in so retrieval treats
    them the same as the hashing backend.
    """

    _DIMS = {"text-embedding-3-small": 1536, "text-embedding-3-large": 3072}

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        dim: int | None = None,
    ) -> None:
        from .llm_client import make_client

        self._client = make_client(base_url=base_url, api_key=api_key)
        self.model = model
        self.name = model
        self.dim = dim or self._DIMS.get(model, 1536)

    def _embed_batch(self, texts: list[str]) -> np.ndarray:
        resp = self._client.embeddings.create(model=self.model, input=texts)
        rows = [np.asarray(item.embedding, dtype=np.float32) for item in resp.data]
        return np.vstack([_l2_normalise(r) for r in rows])

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        out: list[np.ndarray] = []
        for start in range(0, len(texts), 100):  # API batch limit friendliness
            out.append(self._embed_batch(texts[start : start + 100]))
        return np.vstack(out)

    def embed_query(self, text: str) -> np.ndarray:
        return self._embed_batch([text])[0]


class OllamaEmbedder:
    """Semantic embeddings from a local Ollama server -- free, offline.

    Uses Ollama's OpenAI-compatible embeddings endpoint. The model must be
    pulled first (e.g. ``ollama pull nomic-embed-text``). Dimension is inferred
    from the first response, so any embedding model works.
    """

    def __init__(
        self,
        model: str = "nomic-embed-text",
        base_url: str = "http://localhost:11434/v1",
    ) -> None:
        from .llm_client import make_client

        self._client = make_client(base_url=base_url, api_key="ollama")
        self.model = model
        self.name = f"ollama:{model}"
        self._dim: int | None = None

    @property
    def dim(self) -> int:
        if self._dim is None:
            # Probe once to learn the vector size.
            self._dim = self.embed_query("dimension probe").shape[0]
        return self._dim

    def _embed_batch(self, texts: list[str]) -> np.ndarray:
        resp = self._client.embeddings.create(model=self.model, input=texts)
        rows = [np.asarray(item.embedding, dtype=np.float32) for item in resp.data]
        out = np.vstack([_l2_normalise(r) for r in rows])
        self._dim = out.shape[1]
        return out

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        out: list[np.ndarray] = []
        for start in range(0, len(texts), 64):
            out.append(self._embed_batch(texts[start : start + 64]))
        return np.vstack(out)

    def embed_query(self, text: str) -> np.ndarray:
        return self._embed_batch([text])[0]


def get_embedder(settings) -> Embedder:
    """Build the embedder named in settings."""
    if settings.embedder == "openai":
        return OpenAIEmbedder(settings.openai_model)
    if settings.embedder == "ollama":
        return OllamaEmbedder(settings.ollama_embed_model, settings.ollama_base_url)
    if settings.embedder == "hashing":
        return HashingEmbedder(settings.hashing_dim)
    raise ValueError(
        f"Unknown embedder: {settings.embedder!r} (use 'hashing', 'openai', or 'ollama')"
    )
