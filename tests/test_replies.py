"""Tests for the LinkedIn inbox reply detector.

The bug being locked down (D35): a warm insider replied on 2026-07-26 asking for the CV, and eight
consecutive reply checks reported "zero replies" because none of them ever opened LinkedIn.

The load-bearing property here is NOT accuracy. It is which way the check fails: an unreadable or
unfamiliar row must escalate, never go quiet.
"""

from __future__ import annotations

import pytest

from apps.autopilot.replies import InboxReport, Thread, classify


def test_the_real_missed_reply_is_flagged():
    """THE test. This is the actual preview LinkedIn showed for fifteen unanswered days."""
    t = classify("Showkat Gaffar", "Showkat: Wa Alaikum As Salam")
    assert t.they_spoke_last
    assert t.needs_attention


@pytest.mark.parametrize("preview", [
    "You: Hi Swaleha, thanks for connecting! I emailed you earlier this week...",
    "you: short note",
    "  You:   leading whitespace",
])
def test_our_own_last_message_is_not_flagged(preview):
    assert not classify("Someone", preview).needs_attention


def test_sponsored_inmail_is_not_a_reply():
    """LinkedIn shows ads in the same list as real conversations."""
    t = classify("Krishna Kumar", "Sponsored Hi Azam, As a DevOps Engineer at Verventech...")
    assert t.sponsored
    assert not t.needs_attention


def test_an_empty_preview_escalates_rather_than_going_quiet():
    """'Could not tell' must never be rendered as 'nothing to do'. That equivalence IS the bug."""
    t = classify("Someone", "")
    assert t.undetermined
    assert t.needs_attention


def test_an_unfamiliar_preview_shape_escalates():
    """A locale or thread type we have not seen must land in the WAITING pile, not be dropped."""
    t = classify("Someone", "Vous : bonjour")
    assert t.needs_attention


def test_a_read_failure_is_not_an_empty_inbox():
    """An error must not produce the same output as a clean, empty scan."""
    failed = InboxReport(threads=[], error="linkedin-logged-out")
    clean = InboxReport(threads=[Thread("A", "You: hi", they_spoke_last=False)])
    assert failed.error and not clean.error
    assert failed.waiting == [] and clean.waiting == []
    # Both have zero waiting threads. Only the error field distinguishes them, which is why main()
    # branches on error BEFORE reporting any count.


def test_waiting_excludes_sponsored_but_keeps_undetermined():
    report = InboxReport(threads=[
        classify("Ad", "Sponsored buy this"),
        classify("Real", "Real: sure, send it over"),
        classify("Blank", ""),
    ])
    names = {t.name for t in report.waiting}
    assert names == {"Real", "Blank"}
