"""The single LLM entry point for the whole app.

One function: ask(prompt, max_tokens) -> str. The provider is a config value, not an
architecture decision, so switching costs one line in .env:

    LLM_PROVIDER   openrouter (default) | anthropic
    LLM_BASE_URL   OpenAI-compatible endpoint (OpenRouter / OmniRoute / any gateway)
    LLM_API_KEY    key for that endpoint
    LLM_MODEL      model id for that endpoint
    LLM_STREAM     true (default) | false — see _ask_openai_compatible

An OPTIONAL second endpoint, tried only when the first fails outright:

    LLM_FALLBACK_BASE_URL / _API_KEY / _MODEL / _STREAM

NOT WIRED INTO PHASE 0. fill.py makes zero LLM calls by design — an unanswerable field is
logged and left blank so the timing run completes. This module exists for Phase 1+ (fit
scoring, the one genuinely odd screening question).

Measured 2026-07-29: free providers return a 200 with an EMPTY choices list. The resulting
IndexError surfaces as a crash that prints nothing useful, which cost real debugging time.
Every failure mode below therefore raises LLMError with the provider's actual response in
the message.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_PROVIDER = "openrouter"

# Reasoning models spend tokens on a hidden thinking pass BEFORE the answer, out of the
# SAME budget. Measured 2026-08-13: at max_tokens=64 gemini-flash-latest returned an empty
# string with finish_reason=length (thinking consumed all of it) and gemini-3.5-flash-lite
# answered '123' to "12345". The old default of 300 is in that danger zone for a long
# prompt. Free providers make a high ceiling cheap, and running out mid-answer is silent.
DEFAULT_MAX_TOKENS = 1024
ANTHROPIC_DEFAULT_MODEL = "claude-haiku-4-5"


class LLMError(RuntimeError):
    """Any failure to get usable text out of a provider. Always carries the raw response."""


@dataclass(frozen=True)
class _Endpoint:
    """One OpenAI-compatible place to ask. Immutable; built fresh from env per call."""

    label: str
    base_url: str
    api_key: str
    model: str
    stream: bool


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise LLMError(
            f"{name} is not set. Phase 0 needs no LLM; if you are calling ask() you must "
            f"configure LLM_PROVIDER / LLM_BASE_URL / LLM_API_KEY / LLM_MODEL in .env."
        )
    return value


def _wants_stream(name: str, default: str = "true") -> bool:
    return os.getenv(name, default).strip().lower() not in ("false", "0", "no")


def _endpoints() -> list[_Endpoint]:
    """The primary endpoint, plus the fallback if one is configured.

    The fallback exists because the primary is a LOCAL process. OmniRoute runs on
    localhost:20128; when the laptop sleeps, the npm process dies, or the gateway wedges,
    every model behind it goes with it — including the Gemini one that works. Measured
    2026-08-13: Groq reached DIRECTLY (api.groq.com, no gateway) answers exactly in both
    transports, while the SAME key through OmniRoute returns 403 on every completion.
    So the fallback is not a spare tyre of the same rubber: it is a second road.
    """
    chain = [
        _Endpoint(
            label="primary",
            base_url=_require_env("LLM_BASE_URL"),
            api_key=_require_env("LLM_API_KEY"),
            model=_require_env("LLM_MODEL"),
            stream=_wants_stream("LLM_STREAM"),
        )
    ]
    fallback_url = os.getenv("LLM_FALLBACK_BASE_URL")
    fallback_model = os.getenv("LLM_FALLBACK_MODEL")
    if fallback_url and fallback_model:
        chain.append(
            _Endpoint(
                label="fallback",
                base_url=fallback_url,
                api_key=os.getenv("LLM_FALLBACK_API_KEY", ""),
                model=fallback_model,
                stream=_wants_stream("LLM_FALLBACK_STREAM"),
            )
        )
    return chain


def _ask_anthropic(prompt: str, max_tokens: int) -> str:
    from anthropic import Anthropic

    model = os.getenv("LLM_MODEL", ANTHROPIC_DEFAULT_MODEL)
    response = Anthropic().messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    if not response.content:
        raise LLMError(f"anthropic returned no content blocks: {response!r}")

    # Do NOT assume content[0] is the answer. A reasoning model puts a `thinking` block
    # first, so content[0].text is empty or absent and the real answer is further down.
    # Cost a wrong "the gateway returns empty responses" conclusion on 2026-08-13.
    text = "".join(
        block.text
        for block in response.content
        if getattr(block, "type", None) == "text" and getattr(block, "text", None)
    )
    if not text.strip():
        kinds = [getattr(b, "type", "?") for b in response.content]
        raise LLMError(f"anthropic returned no text block (blocks: {kinds}): {response!r}")
    return text.strip()


def _ask_endpoint(endpoint: _Endpoint, prompt: str, max_tokens: int) -> str:
    """Ask one endpoint. Streams by default; `stream=False` for broken streaming.

    There is NO single correct setting, because gateways break in both directions.
    Measured 2026-08-13 against OmniRoute, asked to echo "HELLO WORLD":

        provider            streamed                 non-streamed
        felo (gateway)      'HELLO WORLD'  correct   'WORLD'        first chunk eaten
        groq (gateway)      ''             keepalive  403           unusable either way
        groq (DIRECT)       'HELLO WORLD'  correct   'HELLO WORLD'  correct
        gemini (gateway)    'HELLO WORLD'  correct   'HELLO WORLD'  correct

    Both gateway failures return HTTP 200 with well-formed JSON, so neither is detectable
    from the response shape - only by echoing a known multi-token string and comparing
    exactly. That is what tools/omniroute_canary.py does; it reports the safe mode per
    model. Pin a model it passes and set LLM_STREAM to match.

    Streaming stays the default because its failure is LOUD (no content -> LLMError)
    while the non-streaming failure is SILENT (a plausible answer missing its first
    word). Given a choice of bugs, take the one that cannot reach an employer's form.
    """
    from openai import OpenAI

    client = OpenAI(base_url=endpoint.base_url, api_key=endpoint.api_key)

    if not endpoint.stream:
        response = client.chat.completions.create(
            model=endpoint.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        if not getattr(response, "choices", None):
            raise LLMError(f"provider returned no choices: {response!r}")
        text = getattr(response.choices[0].message, "content", None) or ""
        if not text.strip():
            raise LLMError(f"provider returned an empty message: {response!r}")
        return text.strip()

    stream = client.chat.completions.create(
        model=endpoint.model,
        max_tokens=max_tokens,
        stream=True,
        messages=[{"role": "user", "content": prompt}],
    )

    chunks: list[str] = []
    for event in stream:
        # Measured 2026-07-29: free providers emit chunks with an empty choices list.
        # Measured 2026-08-13: OmniRoute also emits `omniroute-keepalive` frames, and a
        # stream can consist of NOTHING BUT those and then close, with no error at all.
        if not getattr(event, "choices", None):
            continue
        delta = getattr(event.choices[0], "delta", None)
        piece = getattr(delta, "content", None) if delta else None
        if piece:
            chunks.append(piece)

    text = "".join(chunks)
    if not text.strip():
        raise LLMError(
            "provider streamed no content at all - only keepalives, or nothing "
            f"(model={endpoint.model!r}, base_url={endpoint.base_url!r}). "
            "Some providers' streaming is broken through the gateway: check "
            "tools/omniroute_canary.py and try LLM_STREAM=false. "
            "Treat this as 'no answer' - never fall back to a guess."
        )
    return text.strip()


def _ask_openai_compatible(prompt: str, max_tokens: int) -> str:
    """Try each configured endpoint in order; the first real answer wins.

    A single-endpoint chain re-raises the original error UNCHANGED, so the message still
    names the model and the exact failure. Only a genuine multi-endpoint failure gets
    wrapped, and the wrapper keeps every sub-message — a fallback that hides why the
    primary died just moves the debugging one layer further away.
    """
    endpoints = _endpoints()
    failures: list[str] = []
    for endpoint in endpoints:
        try:
            return _ask_endpoint(endpoint, prompt, max_tokens)
        except LLMError as exc:
            if len(endpoints) == 1:
                raise
            failures.append(f"[{endpoint.label} {endpoint.model}] {exc}")
        except Exception as exc:  # noqa: BLE001 - transport errors are failures too
            detail = f"[{endpoint.label} {endpoint.model}] {type(exc).__name__}: {exc}"
            if len(endpoints) == 1:
                raise LLMError(detail) from exc
            failures.append(detail)

    raise LLMError("every configured endpoint failed:\n  " + "\n  ".join(failures))


def ask(prompt: str, max_tokens: int = DEFAULT_MAX_TOKENS) -> str:
    """Send one prompt, get one string back. Raises LLMError rather than returning junk.

    Callers must treat an empty/refused answer as 'no answer' and act accordingly —
    on an employer's form that means leave the field blank, never guess.
    """
    if not prompt or not prompt.strip():
        raise LLMError("ask() called with an empty prompt")

    provider = os.getenv("LLM_PROVIDER", DEFAULT_PROVIDER).strip().lower()
    if provider == "anthropic":
        return _ask_anthropic(prompt, max_tokens)
    if provider in ("openrouter", "omnirouter", "openai", "compatible"):
        return _ask_openai_compatible(prompt, max_tokens)
    raise LLMError(f"unknown LLM_PROVIDER {provider!r}; expected 'openrouter' or 'anthropic'")
