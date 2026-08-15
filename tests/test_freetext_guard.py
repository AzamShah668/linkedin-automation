"""The freetext fallback must answer motivation prose and NOTHING else.

This is the one place an LLM writes onto a real employer's form, so the guard matters more
than the feature. A wrong motivation sentence is embarrassing; an invented "3 years of
Databricks" is caught in the first technical screen and ends the process (D31 - the bank
proves where a value came from, never that it is right).

Offline: `answer()` is only exercised through a stubbed llm.ask.
"""

from __future__ import annotations

import pytest

from apps.autopilot import freetext

# Every one of these appeared on a REAL form in the 2026-08-15 survey of 44 jobs.
FACTUAL_LABELS = [
    "How many years of hands-on experience do you have with Azure AI Foundry, Azure OpenAI, or Databricks?",
    "How many years of hands-on Databricks experience do you have in AI/ML or data engineering projects?",
    "What is your current total annual compensation (CTC)?",
    "What is your expected total annual compensation (CTC)?",
    "What is your current pay in INR per month",
    "Have you completed any relevant certifications or training programs? Please list them.",
    "If you are serving notice currently, please mention your last working date. (DDMMYY)",
    "Do You Have Any Offer in Hand?",
    "Have you managed teams before? If yes, what was the team size and structure?",
    "Are you comfortable with an hourly compensation of $8 USD?",
    "Are you servibg your notice currently?",
    "Do you have experience in build AI-agents using LLM?",
    "How would you rate your communication and stakeholder engagement skills? (Scale of 1-5)",
    "Please enter your full name.",
    "Have you worked on both small-scale and large-scale projects/products? Please provide examples.",
]

MOTIVATION_LABELS = [
    "Why Do You Want to Join Our Company?",
    "Why do you want to work here?",
    "Why are you interested in this role?",
    "What excites you about this position?",
]


@pytest.mark.parametrize("label", FACTUAL_LABELS)
def test_refuses_every_factual_question(label):
    """A checkable fact must never reach the model."""
    assert freetext.is_llm_answerable(label) is False, label


@pytest.mark.parametrize("label", MOTIVATION_LABELS)
def test_accepts_motivation_questions(label):
    assert freetext.is_llm_answerable(label) is True, label


def test_short_or_empty_labels_are_refused():
    for label in ("", "   ", "Name", "Why?"):
        assert freetext.is_llm_answerable(label) is False


def test_prompt_forbids_inventing_company_knowledge():
    p = freetext.build_prompt("Why do you want to join our company?", "Acme", "SRE")
    assert "use nothing else" in p.lower()
    assert "do not invent anything about this company" in p.lower()
    # The prompt must NOT carry a word count: asking for "70 words or fewer" made
    # the model number words inline and truncate. Constrain by sentences instead.
    assert "words or fewer" not in p.lower()
    assert "Acme" in p and "SRE" in p


def test_answer_returns_none_when_the_model_is_down(monkeypatch):
    """Any failure means BLANK. Blank beats wrong - the rule does not bend for convenience."""
    def boom(*_a, **_k):
        raise RuntimeError("gateway down")
    monkeypatch.setattr(freetext.llm, "ask", boom)
    text, why = freetext.answer("Why do you want to join our company?", "Acme", "SRE")
    assert text is None
    assert "llm unavailable" in why


def test_answer_returns_none_on_empty_model_output(monkeypatch):
    monkeypatch.setattr(freetext.llm, "ask", lambda *a, **k: "   ")
    text, _ = freetext.answer("Why do you want to join our company?", "Acme", "SRE")
    assert text is None


def test_rambling_answer_is_refused_not_truncated(monkeypatch):
    """Ignoring the length brief suggests the grounding rule was ignored too, and a truncated
    sentence reads worse on a form than an empty field."""
    monkeypatch.setattr(freetext.llm, "ask", lambda *a, **k: "word " * 200)
    text, why = freetext.answer("Why do you want to join our company?", "Acme", "SRE")
    assert text is None
    assert "cap" in why


def test_em_dashes_are_stripped_from_a_good_answer(monkeypatch):
    monkeypatch.setattr(
        freetext.llm, "ask",
        lambda *a, **k: "I build infrastructure end to end — and want to do it at scale.",
    )
    text, why = freetext.answer("Why do you want to join our company?", "Acme", "SRE")
    assert text is not None
    assert "—" not in text
    assert "llm-generated" in why


def test_factual_label_never_calls_the_model(monkeypatch):
    """The whitelist must short-circuit BEFORE any network call."""
    called = []
    monkeypatch.setattr(freetext.llm, "ask", lambda *a, **k: called.append(1) or "3")
    text, why = freetext.answer("How many years of Databricks experience do you have?")
    assert text is None
    assert called == []
    assert "not a motivation question" in why


def test_truncated_answer_is_refused(monkeypatch):
    """The dangerous direction is SHORT, not long.

    Measured 2026-08-15: at max_tokens=300 Gemini's hidden thinking pass ate the budget and
    the answer came back as "I want to scale my end-to-end" - fluent, grounded, and cut off
    mid-sentence. Every other check passed it. A half-sentence on an employer's form is worse
    than a blank field because nobody notices it.
    """
    monkeypatch.setattr(freetext.llm, "ask", lambda *a, **k: "I want to scale my end-to-end")
    text, why = freetext.answer("Why do you want to join our company?", "Acme", "SRE")
    assert text is None
    assert "truncated" in why


def test_answer_without_end_punctuation_is_refused(monkeypatch):
    monkeypatch.setattr(
        freetext.llm, "ask",
        lambda *a, **k: "I build and ship infrastructure end to end and want to do that at a "
                        "larger scale with a stronger team around me",
    )
    text, why = freetext.answer("Why do you want to join our company?", "Acme", "SRE")
    assert text is None
    assert "truncated" in why


def test_complete_answer_is_accepted(monkeypatch):
    monkeypatch.setattr(
        freetext.llm, "ask",
        lambda *a, **k: "I build and ship infrastructure end to end, and I want to do that at "
                        "a larger scale alongside engineers who have run these systems in "
                        "production longer than I have.",
    )
    text, why = freetext.answer("Why do you want to join our company?", "Acme", "SRE")
    assert text is not None and text.endswith(".")
    assert "llm-generated" in why


def test_uses_the_full_token_budget(monkeypatch):
    """A too-small budget is indistinguishable from a bad model. Pin the default."""
    seen = {}
    monkeypatch.setattr(
        freetext.llm, "ask",
        lambda p, max_tokens=None: seen.update(max_tokens=max_tokens)
        or "I build infrastructure end to end and want to do it at a larger scale with others.",
    )
    freetext.answer("Why do you want to join our company?", "Acme", "SRE")
    assert seen["max_tokens"] == freetext.FREETEXT_MAX_TOKENS >= 4096
