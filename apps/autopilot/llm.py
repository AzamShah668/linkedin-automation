"""The single LLM entry point for the whole app.

One function: ask(prompt, max_tokens) -> str. The provider is a config value, not an
architecture decision, so switching costs one line in .env:

    LLM_PROVIDER   openrouter (default) | anthropic
    LLM_BASE_URL   OpenAI-compatible endpoint (OpenRouter / OmniRouter / any gateway)
    LLM_API_KEY    key for that endpoint
    LLM_MODEL      model id for that endpoint

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


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise LLMError(
            f"{name} is not set. Phase 0 needs no LLM; if you are calling ask() you must "
            f"configure LLM_PROVIDER / LLM_BASE_URL / LLM_API_KEY / LLM_MODEL in .env."
        )
    return value


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


def _ask_openai_compatible(prompt: str, max_tokens: int) -> str:
    """Always streams, then joins. This is a correctness requirement, not a preference.

    Measured 2026-08-13 against OmniRoute: a NON-streaming request silently loses the
    first content chunk. Asked to echo "HELLO WORLD" the same provider returned:

        stream=False        -> 'WORLD'          first chunk dropped
        stream=True joined  -> 'HELLO WORLD'    correct, 4 chunks

    Confirmed on felo-chat, felo-search and big-pickle, on BOTH the OpenAI and the
    Anthropic paths, so it is the gateway's aggregation and not one bad provider. The
    HTTP status is 200 and the JSON is well formed, so no structural check can catch it:
    a fit score comes back plausible and wrong. Streaming avoids the aggregator entirely.

    See docs/knowledge/29-omniroute-gateway.md and tools/omniroute_canary.py.
    """
    from openai import OpenAI

    client = OpenAI(
        base_url=_require_env("LLM_BASE_URL"),
        api_key=_require_env("LLM_API_KEY"),
    )
    stream = client.chat.completions.create(
        model=_require_env("LLM_MODEL"),
        max_tokens=max_tokens,
        stream=True,
        messages=[{"role": "user", "content": prompt}],
    )

    chunks: list[str] = []
    for event in stream:
        # Measured 2026-07-29: free providers emit chunks with an empty choices list.
        if not getattr(event, "choices", None):
            continue
        delta = getattr(event.choices[0], "delta", None)
        piece = getattr(delta, "content", None) if delta else None
        if piece:
            chunks.append(piece)

    text = "".join(chunks)
    if not text.strip():
        raise LLMError(
            "provider streamed no content at all "
            f"(model={os.getenv('LLM_MODEL')!r}, base_url={os.getenv('LLM_BASE_URL')!r}). "
            "Treat this as 'no answer' - never fall back to a guess."
        )
    return text.strip()


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
