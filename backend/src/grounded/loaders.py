"""Loading documents into memory.

Phase 1 supports plain text and Markdown -- the formats you can eyeball and that
need no parsing library. PDF is the obvious next format; the extension point is
marked below. Each loader returns ``Document`` records with a stable path (used
as the source identity) and a human title.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

TEXT_EXTENSIONS = {".txt", ".md", ".markdown"}


@dataclass
class Document:
    """A loaded document ready to chunk."""

    path: str
    title: str
    text: str


def _title_from(path: str, text: str) -> str:
    """Use the first Markdown heading if present, else the file name."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or os.path.basename(path)
        if stripped:
            break
    return os.path.basename(path)


def _load_file(path: str) -> Document:
    ext = os.path.splitext(path)[1].lower()
    if ext not in TEXT_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type {ext!r} for {path}. "
            f"Phase 1 handles {sorted(TEXT_EXTENSIONS)}; PDF support is a later step."
        )
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    return Document(path=os.path.abspath(path), title=_title_from(path, text), text=text)


def load_path(path: str) -> list[Document]:
    """Load a single file or every supported file under a directory."""
    if os.path.isfile(path):
        return [_load_file(path)]
    if os.path.isdir(path):
        docs: list[Document] = []
        for root, _dirs, files in os.walk(path):
            for name in sorted(files):
                if os.path.splitext(name)[1].lower() in TEXT_EXTENSIONS:
                    docs.append(_load_file(os.path.join(root, name)))
        if not docs:
            raise ValueError(f"No supported documents found under {path}")
        return docs
    raise FileNotFoundError(path)
