"""Configuration for a Grounded workspace.

Everything is overridable by environment variable so the tool runs with zero
setup by default, but can be pointed at real embeddings when you're ready.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Runtime settings for ingest and retrieval.

    Attributes:
        db_path: Where the SQLite corpus lives.
        embedder: Which embedding backend to use ("hashing" or "openai").
        hashing_dim: Vector size for the offline hashing embedder.
        openai_model: Embedding model used when embedder="openai".
        chunk_size: Target chunk length in characters.
        chunk_overlap: Characters of overlap between adjacent chunks.
    """

    db_path: str = "grounded.db"
    embedder: str = "hashing"
    hashing_dim: int = 512
    openai_model: str = "text-embedding-3-small"
    chunk_size: int = 1000
    chunk_overlap: int = 150

    @classmethod
    def from_env(cls) -> "Settings":
        """Build settings from environment variables, falling back to defaults."""
        return cls(
            db_path=os.environ.get("GROUNDED_DB", cls.db_path),
            embedder=os.environ.get("GROUNDED_EMBEDDER", cls.embedder).lower(),
            hashing_dim=int(os.environ.get("GROUNDED_HASHING_DIM", cls.hashing_dim)),
            openai_model=os.environ.get("GROUNDED_OPENAI_MODEL", cls.openai_model),
            chunk_size=int(os.environ.get("GROUNDED_CHUNK_SIZE", cls.chunk_size)),
            chunk_overlap=int(os.environ.get("GROUNDED_CHUNK_OVERLAP", cls.chunk_overlap)),
        )
