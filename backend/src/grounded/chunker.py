"""Splitting documents into chunks.

Chunks are overlapping windows over the document. Two properties matter:

- **Exactness.** Each chunk is a verbatim slice of the source text (only outer
  whitespace trimmed). The later verification step matches quotes against this
  stored text, so it must be faithful to what was actually in the document.
- **Boundary preference.** Windows try to end on a paragraph or space boundary
  rather than mid-word, so a retrieved chunk reads cleanly.

Character windows are a pragmatic default. Token-aware or structure-aware
splitting (headings, tables) is a natural later refinement, and the interface
here -- text in, list of strings out -- would not change.
"""

from __future__ import annotations


def chunk_text(text: str, size: int = 1000, overlap: int = 150) -> list[str]:
    """Split text into overlapping windows of roughly ``size`` characters.

    Args:
        text: The full document text.
        size: Target window length in characters.
        overlap: How many characters each window shares with the previous one,
            so a sentence split across a boundary is still wholly present in at
            least one chunk.

    Returns:
        A list of verbatim (outer-trimmed) substrings covering the document.
    """
    if size <= 0:
        raise ValueError("size must be positive")
    if not 0 <= overlap < size:
        raise ValueError("overlap must be in [0, size)")

    text = text.strip()
    if not text:
        return []

    chunks: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + size, n)
        if end < n:
            # Prefer a nearby paragraph break, else a space, to avoid cutting a word.
            window = text[start:end]
            para = window.rfind("\n\n")
            brk = para if para > size // 2 else window.rfind(" ")
            if brk > size // 2:
                end = start + brk
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= n:
            break
        start = max(end - overlap, start + 1)
    return chunks
