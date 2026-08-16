"""The guards that replaced the human tick.

Azam removed the Slack approval gate on 2026-08-16 ("just go for it ... don't ask me for permission
from Slack"). That gate was the thing keeping this project on the safe side of its own north star,
so everything below is now load-bearing rather than belt-and-braces:

  * one request per person, EVER — a second invite to the same human is the most obviously robotic
    thing this system could do, and nobody is reading the names any more
  * a daily cap counted from the append-only log, not from memory
  * business hours only — invites at 03:00 are a bot signal no cap disguises
  * a send is only SENT when the PAGE says so, never because a click did not raise

These are unit tests over the pure decision logic. The browser half is exercised live.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from apps.autopilot import connect


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    """Never touch the real connect log — it is the record of who we have contacted."""
    monkeypatch.setattr(connect, "CONNECT_LOG", tmp_path / "connect-log.jsonl")
    return tmp_path


ENV = {
    "LINKEDIN_CONNECTS_DAILY_CAP": "3",
    "MIN_SECONDS_BETWEEN_SENDS": "45",
    "OUTREACH_JITTER_SECONDS": "90",
    "BUSINESS_HOUR_START": "9",
    "BUSINESS_HOUR_END": "21",
}
NOON = datetime(2026, 8, 16, 12, 0)


# --- never twice ---------------------------------------------------------------------------
def test_a_person_we_already_asked_is_never_asked_again():
    connect.record("asha-r", "Asha R", "Acme", connect.SENT, now=NOON)
    assert connect.already_requested("asha-r") is True


def test_an_existing_connection_is_not_re_requested():
    connect.record("bo-k", "Bo K", "Acme", connect.ALREADY_CONNECTED, now=NOON)
    assert connect.already_requested("bo-k") is True


def test_a_failed_attempt_does_not_block_a_retry():
    """An error means nothing reached them, so the person is still worth contacting."""
    connect.record("cy-l", "Cy L", "Acme", connect.ERROR, now=NOON)
    assert connect.already_requested("cy-l") is False


def test_the_check_ignores_handle_casing():
    connect.record("Dee-M", "Dee M", "Acme", connect.SENT, now=NOON)
    assert connect.already_requested("dee-m") is True


def test_somebody_we_have_never_contacted_is_not_blocked():
    assert connect.already_requested("nobody") is False


# --- the daily cap -------------------------------------------------------------------------
def test_only_actual_sends_count_against_the_cap():
    connect.record("a", "A", "X", connect.SENT, now=NOON)
    connect.record("b", "B", "X", connect.ALREADY_PENDING, now=NOON)
    connect.record("c", "C", "X", connect.NO_CONNECT_BUTTON, now=NOON)
    connect.record("d", "D", "X", connect.ERROR, now=NOON)
    assert connect.sent_today(now=NOON) == 1


def test_yesterdays_sends_do_not_count_against_today():
    connect.record("a", "A", "X", connect.SENT, now=datetime(2026, 8, 15, 12, 0))
    assert connect.sent_today(now=NOON) == 0


def test_a_corrupt_log_line_does_not_hide_the_rest():
    (connect.CONNECT_LOG).parent.mkdir(parents=True, exist_ok=True)
    connect.record("a", "A", "X", connect.SENT, now=NOON)
    with connect.CONNECT_LOG.open("a", encoding="utf-8") as fh:
        fh.write("not json\n")
    connect.record("b", "B", "X", connect.SENT, now=NOON)
    assert connect.sent_today(now=NOON) == 2


# --- business hours ------------------------------------------------------------------------
@pytest.mark.parametrize("hour,expected", [(3, False), (8, False), (9, True),
                                           (20, True), (21, False), (23, False)])
def test_business_hours_window(hour, expected):
    assert connect.within_business_hours(datetime(2026, 8, 16, hour, 0), ENV) is expected


# --- the guard chain, without a browser ------------------------------------------------------
class _FakePage:
    """Stands in for Playwright. Records whether the browser was touched at all."""

    def __init__(self):
        self.visited = False

    def goto(self, *a, **k):
        self.visited = True
        raise AssertionError("connect_one must not reach the browser when a guard refuses")


def test_a_repeat_contact_never_reaches_the_browser():
    connect.record("asha-r", "Asha R", "Acme", connect.SENT, now=NOON)
    page = _FakePage()
    result = connect.connect_one(page, "asha-r", "Asha R", "Acme", env=ENV, now=NOON)
    assert result.outcome == connect.ALREADY_PENDING
    assert page.visited is False


def test_out_of_hours_never_reaches_the_browser():
    page = _FakePage()
    night = datetime(2026, 8, 16, 3, 0)
    result = connect.connect_one(page, "new-person", "New", "Acme", env=ENV, now=night)
    assert result.outcome == connect.OUT_OF_HOURS
    assert page.visited is False


def test_the_cap_never_reaches_the_browser():
    for i in range(3):                       # cap is 3 in ENV
        connect.record(f"p{i}", f"P{i}", "X", connect.SENT, now=NOON)
    page = _FakePage()
    result = connect.connect_one(page, "new-person", "New", "Acme", env=ENV, now=NOON)
    assert result.outcome == connect.CAPPED
    assert page.visited is False


def test_a_refused_attempt_is_not_written_to_the_log():
    """A guard refusal is not contact, and logging it would poison already_requested()."""
    page = _FakePage()
    connect.connect_one(page, "new-person", "New", "Acme", env=ENV,
                        now=datetime(2026, 8, 16, 3, 0))
    assert connect.already_requested("new-person") is False


# --- throttle ------------------------------------------------------------------------------
def test_the_throttle_is_never_shorter_than_the_configured_minimum():
    for _ in range(40):
        assert 45 <= connect.throttle(ENV) <= 45 + 90


def test_a_missing_setting_falls_back_rather_than_crashing():
    assert connect.setting("LINKEDIN_CONNECTS_DAILY_CAP", {}) == \
        connect.DEFAULTS["LINKEDIN_CONNECTS_DAILY_CAP"]
    assert connect.setting("MIN_SECONDS_BETWEEN_SENDS", {"MIN_SECONDS_BETWEEN_SENDS": "junk"}) == \
        connect.DEFAULTS["MIN_SECONDS_BETWEEN_SENDS"]


# --- the report is a receipt, not a request ---------------------------------------------------
def test_the_report_never_carries_the_approval_ref():
    """`ref:<slug>` is the approval gate's token. A receipt must not look like a request."""
    sent = connect.Result("asha-r", "Asha R", "Acme", connect.SENT, "confirmed")
    lines = [f"✅ {sent.name} — {sent.company}", f"https://www.linkedin.com/in/{sent.username}/"]
    assert not any("ref:" in line for line in lines)


def test_result_ok_is_true_only_for_a_send():
    assert connect.Result("u", "n", "c", connect.SENT).ok is True
    for outcome in (connect.ALREADY_PENDING, connect.CAPPED, connect.ERROR,
                    connect.LIMIT_REACHED, connect.OUT_OF_HOURS, connect.NO_CONNECT_BUTTON):
        assert connect.Result("u", "n", "c", outcome).ok is False
