"""The ingest pipeline: documents in, searchable corpus out.

For each document: load it, split it into chunks, embed the chunks, and store
them with their exact text. This is the one-time setup step per corpus (the box
labelled "Ingest (once)" in the architecture).
"""

from __future__ import annotations

from dataclasses import dataclass

from .chunker import chunk_text
from .config import Settings
from .embedder import Embedder
from .loaders import load_path
from .store import Store


@dataclass
class IngestReport:
    """Summary of an ingest run."""

    documents: int
    chunks: int
    embedder: str


def ingest_path(
    store: Store, embedder: Embedder, path: str, settings: Settings
) -> IngestReport:
    """Ingest every supported document at ``path`` into the store.

    Re-ingesting a path already in the corpus replaces it rather than
    duplicating, so this is safe to run repeatedly.
    """
    documents = load_path(path)
    total_chunks = 0
    for doc in documents:
        pieces = chunk_text(doc.text, settings.chunk_size, settings.chunk_overlap)
        if not pieces:
            continue
        embeddings = embedder.embed_texts(pieces)
        store.replace_source(
            path=doc.path,
            title=doc.title,
            chunk_texts=pieces,
            embeddings=embeddings,
            embed_model=embedder.name,
        )
        total_chunks += len(pieces)
    return IngestReport(
        documents=len(documents), chunks=total_chunks, embedder=embedder.name
    )
