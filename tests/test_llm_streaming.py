"""Tests for the LLM entry point — specifically the corruption that has no symptom.

Measured 2026-08-13 against OmniRoute: a NON-streaming request silently loses the first
content chunk. The same provider, asked to echo "HELLO WORLD", returned 'WORLD' with
stream=False and 'HELLO WORLD' when streamed and joined. HTTP 200, well-formed JSON,
nothing to catch. A fit score comes back plausible and wrong (D30, D31).

So `_ask_openai_compatible` MUST stream. These tests exist to stop someone simplifying it
back to a single non-streaming call, which would look tidier and reintroduce the bug.

Offline — the openai client is stubbed, so no provider is called. See D42.
"""

from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from apps.autopilot import llm


def _chunk(content=None, *, no_choices: bool = False):
    """One streamed event, shaped like the openai SDK's."""
    if no_choices:
        return SimpleNamespace(choices=[])
    delta = SimpleNamespace(content=content)
    return SimpleNamespace(choices=[SimpleNamespace(delta=delta)])


@pytest.fixture
def fake_openai(monkeypatch):
    """Install a stub `openai` module; return the dict recording the call made."""
    recorded: dict = {}

    def make(events):
        class _Completions:
            def create(self, **kwargs):
                recorded.update(kwargs)
                if not kwargs.get("stream"):
                    # Mirror the real failure: the aggregator eats the first chunk.
                    raise AssertionError("non-streaming request would silently truncate")
                return iter(events)

        class _Client:
            def __init__(self, **kwargs):
                recorded["_init"] = kwargs
                self.chat = SimpleNamespace(completions=_Completions())

        monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=_Client))
        return recorded

    return make


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("LLM_BASE_URL", "http://localhost:20128/v1")
    monkeypatch.setenv("LLM_API_KEY", "local")
    monkeypatch.setenv("LLM_MODEL", "test/model")


def test_streams_rather_than_aggregating(fake_openai):
    """The request must set stream=True — the whole point of the fix."""
    recorded = fake_openai([_chunk("HELLO"), _chunk(" WORLD")])
    assert llm.ask("echo") == "HELLO WORLD"
    assert recorded["stream"] is True


def test_keeps_the_first_chunk(fake_openai):
    """The exact regression: the first chunk must survive into the answer."""
    fake_openai([_chunk("P"), _chunk("ONG")])
    assert llm.ask("echo") == "PONG"


def test_survives_chunks_with_no_choices(fake_openai):
    """Free providers emit empty-choices chunks mid-stream; they are skipped, not fatal."""
    fake_openai([_chunk(no_choices=True), _chunk("OK"), _chunk(None), _chunk(no_choices=True)])
    assert llm.ask("echo") == "OK"


def test_empty_stream_raises_rather_than_returning_blank(fake_openai):
    """A silent '' would be treated as an answer downstream. It must be loud instead."""
    fake_openai([_chunk(no_choices=True), _chunk(None)])
    with pytest.raises(llm.LLMError) as exc:
        llm.ask("echo")
    assert "no content" in str(exc.value)
    # The message must name the model/endpoint, or debugging starts from nothing.
    assert "test/model" in str(exc.value)


def test_anthropic_skips_thinking_blocks(monkeypatch):
    """A reasoning model puts `thinking` first; content[0].text is not the answer."""
    blocks = [
        SimpleNamespace(type="thinking", thinking="deliberating"),
        SimpleNamespace(type="text", text="PONG"),
    ]
    response = SimpleNamespace(content=blocks)

    class _Messages:
        def create(self, **_kwargs):
            return response

    class _Anthropic:
        def __init__(self, **_kwargs):
            self.messages = _Messages()

    monkeypatch.setitem(sys.modules, "anthropic", SimpleNamespace(Anthropic=_Anthropic))
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    assert llm.ask("echo") == "PONG"


def test_anthropic_with_only_thinking_raises(monkeypatch):
    """No text block at all is 'no answer', not an empty string."""
    response = SimpleNamespace(content=[SimpleNamespace(type="thinking", thinking="...")])

    class _Messages:
        def create(self, **_kwargs):
            return response

    class _Anthropic:
        def __init__(self, **_kwargs):
            self.messages = _Messages()

    monkeypatch.setitem(sys.modules, "anthropic", SimpleNamespace(Anthropic=_Anthropic))
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    with pytest.raises(llm.LLMError) as exc:
        llm.ask("echo")
    assert "thinking" in str(exc.value)
