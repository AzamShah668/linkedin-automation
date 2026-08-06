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
DEFAULT_MAX_TOKENS = 300
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

    text = response.content[0].text
    if not text or not text.strip():
        raise LLMError(f"anthropic returned empty text: {response!r}")
    return text.strip()


def _ask_openai_compatible(prompt: str, max_tokens: int) -> str:
    from openai import OpenAI

    client = OpenAI(
        base_url=_require_env("LLM_BASE_URL"),
        api_key=_require_env("LLM_API_KEY"),
    )
    response = client.chat.completions.create(
        model=_require_env("LLM_MODEL"),
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )

    # Measured 2026-07-29 — this is the failure that prints nothing if you index blindly.
    if not getattr(response, "choices", None):
        raise LLMError(f"provider returned no choices: {response!r}")

    message = response.choices[0].message
    text = getattr(message, "content", None)
    if not text or not text.strip():
        raise LLMError(f"provider returned an empty message: {response!r}")
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
