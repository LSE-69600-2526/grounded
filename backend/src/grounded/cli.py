"""Command-line interface for Grounded.

    grounded ingest <path>       add a file or folder to the corpus
    grounded ask "<question>"    retrieve the most relevant chunks
    grounded stats               show corpus size and active embedder
    grounded reset               empty the corpus

In Phase 1, ``ask`` shows the retrieved evidence. Generation of an answer, and
the two-leg verification of every claim against this evidence, are the next
steps -- they consume exactly what ``ask`` returns here.
"""

from __future__ import annotations

import argparse
import sys

from .answer import compose_answer, persist_answer
from .config import Settings
from .embedder import get_embedder
from .generator import get_generator
from .ingest import ingest_path
from .retrieve import Retriever
from .store import Store


def _cmd_ingest(args: argparse.Namespace, settings: Settings) -> int:
    store = Store(settings.db_path)
    embedder = get_embedder(settings)
    report = ingest_path(store, embedder, args.path, settings)
    store.close()
    print(
        f"Ingested {report.documents} document(s), {report.chunks} chunk(s) "
        f"using embedder '{report.embedder}'."
    )
    return 0


def _cmd_ask(args: argparse.Namespace, settings: Settings) -> int:
    store = Store(settings.db_path)
    embedder = get_embedder(settings)
    retriever = Retriever(store, embedder)
    if retriever.embedder_mismatch:
        print(f"warning: {retriever.embedder_mismatch}\n", file=sys.stderr)
    if retriever.is_empty:
        print("The corpus is empty. Run 'grounded ingest <path>' first.")
        store.close()
        return 1

    results = retriever.search(args.question, k=args.k)
    generator = get_generator(settings)

    if generator is None or args.retrieve_only:
        _print_passages(args.question, results, embedder.name)
        if generator is None and not args.retrieve_only:
            print(
                "note: answer generation is off (no OPENAI_API_KEY / GROUNDED_GENERATOR). "
                "Showing retrieved passages only.\n"
            )
        store.close()
        return 0

    answer = compose_answer(args.question, results, generator)
    persist_answer(store, answer)
    _print_answer(answer, generator.name)
    store.close()
    return 0


def _print_passages(question: str, results, embedder_name: str) -> None:
    print(f"Question: {question}")
    print(f"Top {len(results)} passages (embedder '{embedder_name}'):\n")
    for rank, res in enumerate(results, 1):
        c = res.chunk
        snippet = " ".join(c.text.split())
        if len(snippet) > 280:
            snippet = snippet[:277] + "..."
        print(f"[{rank}] score={res.score:.3f}  {c.source_title}  (chunk #{c.ord})")
        print(f"    {snippet}\n")


def _print_answer(answer, generator_name: str) -> None:
    print(f"Question: {answer.question}")
    print(f"(generator '{generator_name}')\n")
    if not answer.claims:
        print("No claims could be grounded in this corpus for that question.")
        print("(An honest gap: the sources don't answer it.)\n")
        return
    for vc in answer.claims:
        if vc.verified:
            src = vc.chunk.source_title if vc.chunk else "?"
            print(f"  [verified] {vc.claim.text}")
            print(f"      \u201c{vc.claim.quote}\u201d  \u2014 {src}")
        else:
            print(f"  [flagged]  {vc.claim.text}")
            print(f"      reason: {vc.reason}")
        print()
    n_ok = len(answer.verified_claims)
    n_flag = len(answer.flagged_claims)
    print(f"{n_ok} verified, {n_flag} flagged. Flagged claims are shown, not hidden.")


def _cmd_stats(_args: argparse.Namespace, settings: Settings) -> int:
    store = Store(settings.db_path)
    sources, chunks = store.counts()
    store.close()
    print(f"Corpus: {sources} source(s), {chunks} chunk(s)")
    print(f"Database: {settings.db_path}")
    print(f"Active embedder: {settings.embedder}")
    return 0


def _cmd_reset(_args: argparse.Namespace, settings: Settings) -> int:
    store = Store(settings.db_path)
    store.reset()
    store.close()
    print("Corpus emptied.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="grounded", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_ingest = sub.add_parser("ingest", help="add a file or folder to the corpus")
    p_ingest.add_argument("path", help="file or directory to ingest")
    p_ingest.set_defaults(func=_cmd_ingest)

    p_ask = sub.add_parser("ask", help="retrieve the most relevant passages")
    p_ask.add_argument("question", help="the question to search for")
    p_ask.add_argument("-k", type=int, default=5, help="how many passages to retrieve")
    p_ask.add_argument(
        "--retrieve-only",
        action="store_true",
        help="skip generation; just show the retrieved passages",
    )
    p_ask.set_defaults(func=_cmd_ask)

    p_stats = sub.add_parser("stats", help="show corpus size and embedder")
    p_stats.set_defaults(func=_cmd_stats)

    p_reset = sub.add_parser("reset", help="empty the corpus")
    p_reset.set_defaults(func=_cmd_reset)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = Settings.from_env()
    return args.func(args, settings)


if __name__ == "__main__":
    raise SystemExit(main())
