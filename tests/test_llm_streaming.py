"""Tests for the LLM entry point — specifically the corruption that has no symptom.

Measured 2026-08-13 against OmniRoute. The gateway breaks in BOTH directions, and which
way depends on the provider:

    provider   streamed                  non-streamed
    felo       'HELLO WORLD'  correct    'WORLD'        first chunk eaten
    groq       ''             keepalive  'Hello World'  correct
    gemini     'HELLO WORLD'  correct    'HELLO WORLD'  correct

Both failures are HTTP 200 with well-formed JSON, so neither is visible from the response
shape. A fit score comes back plausible and wrong (D30, D31).

Streaming is therefore the DEFAULT but not a law: `LLM_STREAM=false` exists for providers
whose streaming is broken. Streaming is preferred because its failure is loud (no content
-> LLMError) while the non-streaming failure is silent (an answer missing its first word).

These tests stop someone collapsing this back to a single hardcoded transport, which would
look tidier and would be wrong for one provider or the other.

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
    # The fallback is opt-in. Leaving a stray value set would make every other test in
    # this file silently exercise a two-endpoint chain, which changes the error path.
    for name in (
        "LLM_FALLBACK_BASE_URL",
        "LLM_FALLBACK_API_KEY",
        "LLM_FALLBACK_MODEL",
        "LLM_FALLBACK_STREAM",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("LLM_STREAM", raising=False)


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


def test_llm_stream_false_uses_the_non_streaming_call(monkeypatch):
    """LLM_STREAM=false exists for providers whose streaming is broken (groq: the
    gateway sends only keepalive frames, then closes, at HTTP 200). The stub raises
    if a stream is requested, proving the flag actually changes transport."""
    recorded: dict = {}

    class _Completions:
        def create(self, **kwargs):
            recorded.update(kwargs)
            if kwargs.get("stream"):
                raise AssertionError("LLM_STREAM=false must not request a stream")
            message = SimpleNamespace(content="PONG")
            return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    class _Client:
        def __init__(self, **_kwargs):
            self.chat = SimpleNamespace(completions=_Completions())

    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=_Client))
    monkeypatch.setenv("LLM_STREAM", "false")
    assert llm.ask("echo") == "PONG"
    assert not recorded.get("stream")


def test_keepalive_only_stream_raises(fake_openai):
    """A stream of nothing but keepalives is 'no answer', and must be loud.

    The gateway returns HTTP 200 and closes; without this the caller gets ''.
    """
    fake_openai([_chunk(no_choices=True), _chunk(no_choices=True)])
    with pytest.raises(llm.LLMError) as exc:
        llm.ask("echo")
    assert "keepalive" in str(exc.value).lower()


# --------------------------------------------------------------------------------------
# The fallback chain.
#
# The primary endpoint is a LOCAL process (OmniRoute on :20128). When the laptop sleeps or
# the npm process dies, EVERY model behind it dies too, including the Gemini one that
# works — so a "fallback" pointed at the same gateway is not a fallback at all.
#
# Measured 2026-08-13: Groq reached directly answers exactly in both transports, while the
# SAME key through OmniRoute returns 403 on every completion. The fallback is a second
# road, not a spare tyre of the same rubber.
# --------------------------------------------------------------------------------------

PRIMARY_URL = "http://localhost:20128/v1"
FALLBACK_URL = "https://api.groq.com/openai/v1"


@pytest.fixture
def by_base_url(monkeypatch):
    """Stub `openai` whose behaviour depends on base_url. Returns the call log.

    Behaviour values: a str answers with it, None streams nothing (an LLMError), an
    Exception instance is raised as a transport failure.
    """
    calls: list[tuple[str, str]] = []

    def install(behaviour: dict):
        class _Completions:
            def __init__(self, base_url: str):
                self._base = base_url

            def create(self, **kwargs):
                calls.append((self._base, kwargs.get("model")))
                action = behaviour[self._base]
                if isinstance(action, Exception):
                    raise action
                if action is None:
                    return iter([_chunk(no_choices=True)])
                return iter([_chunk(action)])

        class _Client:
            def __init__(self, **kwargs):
                self.chat = SimpleNamespace(completions=_Completions(kwargs.get("base_url")))

        monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=_Client))
        return calls

    return install


@pytest.fixture
def with_fallback(monkeypatch):
    monkeypatch.setenv("LLM_FALLBACK_BASE_URL", FALLBACK_URL)
    monkeypatch.setenv("LLM_FALLBACK_API_KEY", "groq-key")
    monkeypatch.setenv("LLM_FALLBACK_MODEL", "llama-3.3-70b-versatile")


def test_fallback_answers_when_the_primary_streams_nothing(by_base_url, with_fallback):
    """The exact production failure: the gateway 200s with only keepalives."""
    calls = by_base_url({PRIMARY_URL: None, FALLBACK_URL: "PONG"})
    assert llm.ask("echo") == "PONG"
    assert [c[0] for c in calls] == [PRIMARY_URL, FALLBACK_URL]


def test_fallback_answers_when_the_primary_is_unreachable(by_base_url, with_fallback):
    """A dead gateway raises a transport error, not an LLMError. Still must fall over."""
    calls = by_base_url(
        {PRIMARY_URL: ConnectionError("connection refused"), FALLBACK_URL: "PONG"}
    )
    assert llm.ask("echo") == "PONG"
    assert [c[0] for c in calls] == [PRIMARY_URL, FALLBACK_URL]


def test_fallback_is_not_touched_when_the_primary_works(by_base_url, with_fallback):
    """A fallback that runs on every call doubles cost and hides a broken primary."""
    calls = by_base_url({PRIMARY_URL: "PONG", FALLBACK_URL: "WRONG"})
    assert llm.ask("echo") == "PONG"
    assert [c[0] for c in calls] == [PRIMARY_URL]


def test_all_endpoints_failing_names_every_one(by_base_url, with_fallback):
    """Never return junk, and never hide WHY each leg died — that just moves the
    debugging one layer further away."""
    by_base_url({PRIMARY_URL: None, FALLBACK_URL: ConnectionError("dns")})
    with pytest.raises(llm.LLMError) as exc:
        llm.ask("echo")
    message = str(exc.value)
    assert "test/model" in message
    assert "llama-3.3-70b-versatile" in message
    assert "primary" in message and "fallback" in message


def test_single_endpoint_error_is_reraised_unchanged(fake_openai):
    """With no fallback configured the original error must survive intact, so the
    message still names the model and the exact failure mode."""
    fake_openai([_chunk(no_choices=True)])
    with pytest.raises(llm.LLMError) as exc:
        llm.ask("echo")
    assert "keepalive" in str(exc.value).lower()
    assert "every configured endpoint failed" not in str(exc.value)


def test_partial_fallback_config_is_ignored(by_base_url, monkeypatch):
    """A URL with no model is a half-finished edit, not a fallback. Using it would send
    the primary's model id to a provider that has never heard of it."""
    monkeypatch.setenv("LLM_FALLBACK_BASE_URL", FALLBACK_URL)
    monkeypatch.delenv("LLM_FALLBACK_MODEL", raising=False)
    calls = by_base_url({PRIMARY_URL: "PONG"})
    assert llm.ask("echo") == "PONG"
    assert [c[0] for c in calls] == [PRIMARY_URL]


# =================================================================================================
# 2026-08-16 — the budget floor.
#
# Measured against gemini-3.5-flash-lite through OmniRoute, asking it to echo exact strings:
#
#     max_tokens=128   exact 0/4    'ALPHA 12345 OMEGA' -> 'ALPHA 12'
#     max_tokens=512   exact 4/4
#
# Every short-budget answer was well-formed, plausible, HTTP 200, and cut off at the END. The
# hidden thinking pass spends the same budget as the answer, so "this reply is five words, 128 is
# plenty" produces a fragment with nothing raised anywhere. Same lesson as FREETEXT_MAX_TOKENS,
# one layer down.
# =================================================================================================

def test_a_small_budget_is_raised_to_the_floor(monkeypatch):
    seen = {}

    def _spy(prompt, max_tokens, model=None):
        seen["max_tokens"] = max_tokens
        return "ok"

    monkeypatch.setattr(llm, "_ask_openai_compatible", _spy)
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    llm.ask("hello", max_tokens=64)
    assert seen["max_tokens"] == llm.MIN_SAFE_MAX_TOKENS


def test_a_generous_budget_is_left_alone(monkeypatch):
    seen = {}

    def _spy(prompt, max_tokens, model=None):
        seen["max_tokens"] = max_tokens
        return "ok"

    monkeypatch.setattr(llm, "_ask_openai_compatible", _spy)
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    llm.ask("hello", max_tokens=4096)
    assert seen["max_tokens"] == 4096


def test_the_floor_is_high_enough_to_have_fixed_the_measured_failure():
    """128 truncated every one of four echoes; 512 passed all four."""
    assert llm.MIN_SAFE_MAX_TOKENS >= 512


def test_the_default_is_at_or_above_the_floor():
    assert llm.DEFAULT_MAX_TOKENS >= llm.MIN_SAFE_MAX_TOKENS


# --- model tiers ---------------------------------------------------------------------------------
def test_the_heavy_tier_falls_back_to_the_fast_one_when_unset(monkeypatch):
    """A missing setting must degrade to a working pipeline, not a crash."""
    monkeypatch.delenv("LLM_CV_MODEL", raising=False)
    assert llm.heavy_model() is None


def test_the_heavy_tier_is_used_when_configured(monkeypatch):
    monkeypatch.setenv("LLM_CV_MODEL", "some/bigger-model")
    assert llm.heavy_model() == "some/bigger-model"


def test_an_explicit_model_overrides_only_the_primary(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "http://localhost:20128/v1")
    monkeypatch.setenv("LLM_API_KEY", "x")
    monkeypatch.setenv("LLM_MODEL", "fast/one")
    monkeypatch.setenv("LLM_FALLBACK_BASE_URL", "https://api.groq.com/openai/v1")
    monkeypatch.setenv("LLM_FALLBACK_MODEL", "fallback/one")
    chain = llm._endpoints("heavy/one")
    assert chain[0].model == "heavy/one"
    # The fallback is a different provider; its model ids are not the gateway's.
    assert chain[1].model == "fallback/one"
