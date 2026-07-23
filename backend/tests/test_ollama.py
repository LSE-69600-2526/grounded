"""Tests for the local (Ollama) backends.

Ollama can't be reached from the test environment, so these assert the *wiring*:
that selecting "ollama" builds a client pointed at localhost with the right
model, without making any network call. Construction is offline; only an actual
request would touch the server.
"""

from __future__ import annotations

import pytest

from grounded.config import Settings
from grounded.embedder import OllamaEmbedder, get_embedder
from grounded.generator import OllamaGenerator, get_generator


def test_get_generator_selects_ollama():
    settings = Settings(generator="ollama", ollama_model="llama3.1")
    gen = get_generator(settings)
    assert isinstance(gen, OllamaGenerator)
    assert gen.name == "ollama:llama3.1"


def test_ollama_generator_points_at_local_server():
    gen = OllamaGenerator(model="mistral", base_url="http://localhost:11434/v1")
    # The underlying client is configured for the local endpoint, no key needed.
    assert "11434" in str(gen._client.base_url)
    assert gen.model == "mistral"


def test_get_embedder_selects_ollama():
    settings = Settings(embedder="ollama", ollama_embed_model="nomic-embed-text")
    emb = get_embedder(settings)
    assert isinstance(emb, OllamaEmbedder)
    assert emb.name == "ollama:nomic-embed-text"


def test_ollama_embedder_points_at_local_server():
    emb = OllamaEmbedder(base_url="http://localhost:11434/v1")
    assert "11434" in str(emb._client.base_url)


def test_env_overrides_ollama_settings(monkeypatch):
    monkeypatch.setenv("GROUNDED_GENERATOR", "ollama")
    monkeypatch.setenv("GROUNDED_OLLAMA_MODEL", "qwen2.5")
    settings = Settings.from_env()
    assert settings.generator == "ollama"
    assert settings.ollama_model == "qwen2.5"
    assert get_generator(settings).name == "ollama:qwen2.5"
