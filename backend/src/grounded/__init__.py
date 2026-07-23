"""Grounded: a document Q&A tool that cannot fabricate a citation.

Phase 1 (this build): ingest a corpus, then retrieve the most relevant chunks
for a question. Every chunk keeps its exact source text on disk, which is what
the later verification step will check quotes against.
"""

__version__ = "0.1.0"
