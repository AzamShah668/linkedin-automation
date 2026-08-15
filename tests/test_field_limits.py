"""Respect the field's character cap, or leave it blank. Never send a fragment.

Caught by Azam 2026-08-15: LinkedIn caps free-text answers (the live counter reads "0/20",
"0/300"). Playwright's fill() does not error on an over-long string - the BROWSER truncates -
so a banked paragraph arrives on a real employer's form ending mid-word, with nothing raised
anywhere. Same shape as every other bug this project keeps finding: plausible, well-formed,
wrong, and silent.
"""

from __future__ import annotations

import json
from pathlib import Path

from apps.autopilot.fill import _fit_to_limit

BANK = Path(__file__).resolve().parents[1] / "profile" / "application-answers.json"


def test_no_limit_passes_through():
    text = "x" * 5000
    assert _fit_to_limit(text, None) == (text, "")


def test_value_within_the_limit_is_untouched():
    assert _fit_to_limit("Srinagar", 100) == ("Srinagar", "")


def test_exactly_at_the_limit_is_untouched():
    value, why = _fit_to_limit("abcde", 5)
    assert (value, why) == ("abcde", "")


def test_trims_at_a_sentence_boundary():
    text = ("I build infrastructure end to end. I want to do that at a larger scale with a "
            "stronger team around me. A third sentence that will not fit at all.")
    value, why = _fit_to_limit(text, 120)
    assert value is not None
    assert value.endswith(".")
    assert len(value) <= 120
    assert "sentence end" in why
    # It must not stop mid-word.
    assert not value.endswith(("wi", "th", "stron"))


def test_trims_at_a_clause_break_when_no_sentence_fits():
    text = "Docker, Kubernetes and Proxmox for infrastructure, Jenkins and Ansible for CI/CD"
    value, why = _fit_to_limit(text, 45)
    assert value is not None
    assert len(value) <= 45
    assert "clause break" in why
    assert not value.endswith(",")


def test_refuses_rather_than_send_a_stub():
    """Below roughly a third of the limit there is no answer left, only a stub - and a stub is
    worse than a blank because nobody notices it."""
    text = "Supercalifragilistic " + "x" * 200
    value, why = _fit_to_limit(text, 20)
    assert value is None
    assert "will not trim cleanly" in why


def test_a_20_char_field_rejects_a_paragraph():
    """The real case: the years fields cap at 20 and the prose answers are 200+."""
    bank = json.loads(BANK.read_text(encoding="utf-8"))
    prose = bank["narrative"]["primary_technologies"]
    value, _ = _fit_to_limit(prose, 20)
    assert value is None


def test_banked_prose_fits_a_300_char_field_whole():
    """Every narrative answer must arrive as FINISHED prose in the common 300-char field, not
    as something the trimmer had to rescue."""
    bank = json.loads(BANK.read_text(encoding="utf-8"))
    for key, text in bank["narrative"].items():
        if key.startswith("_"):
            continue
        assert len(text) <= 300, f"{key} is {len(text)} chars; LinkedIn commonly caps at 300"
        assert text.rstrip().endswith("."), f"{key} does not end on a full stop"
        value, why = _fit_to_limit(text, 300)
        assert value == text and why == "", f"{key} needed trimming at 300"
