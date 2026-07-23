"""A single place to build an OpenAI-compatible client.

Both the real OpenAI API and a local Ollama server speak the same wire format,
so the *only* difference between talking to the cloud and talking to your own
machine is the base URL (and a throwaway key for Ollama, which ignores it).
Centralising client construction here is what lets the generator and embedder
support both with almost no extra code. See
docs/adr/0009-local-inference-via-ollama.md.
"""

from __future__ import annotations


def make_client(base_url: str | None = None, api_key: str | None = None):
    """Construct an OpenAI-compatible client.

    Args:
        base_url: Override the endpoint (e.g. Ollama's
            ``http://localhost:11434/v1``). None uses OpenAI's default.
        api_key: Explicit key. None lets the OpenAI client read
            ``OPENAI_API_KEY`` from the environment. For Ollama, pass any
            non-empty string -- it is ignored by the server but the client
            requires one to be present.

    Constructing a client does not make a network call; the first request does.
    """
    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "The 'openai' package is required (it is also the client for Ollama). "
            "Install it with: pip install openai"
        ) from exc
    kwargs: dict[str, str] = {}
    if base_url:
        kwargs["base_url"] = base_url
    if api_key:
        kwargs["api_key"] = api_key
    return OpenAI(**kwargs)
