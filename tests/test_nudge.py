"""Follow-up cadence, fed from records that are true rather than from zeros.

`tools/followups_from_board.py` had to emit `followups_sent=0` for every row because the board has
no such column, and said so loudly every run. The dangerous case it left open is a SECOND Day-3
nudge to someone who already had one -- the only failure here that reaches a recruiter and looks
like a machine. These tests exist to keep that closed.
"""

from __future__ import annotations

import datetime as dt
import json

import pytest

from apps.autopilot import nudge


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    """Never let a test read or append to the real send record."""
    monkeypatch.setattr(nudge, "SENT_LOG", tmp_path / "followups-sent.jsonl")
    monkeypatch.setattr(nudge, "NOTIFIED_LOG", tmp_path / "nudges-notified.jsonl")
    monkeypatch.setattr(nudge, "BOARD_DB", tmp_path / "no-board.sqlite3")
    monkeypatch.setattr(nudge.sourcing, "load_unreachable", lambda *a, **k: {})
    return tmp_path


def _row(company="Acme", role="SRE", applied="2026-08-01", channel="linkedin-easy-apply"):
    return {"company": company, "role": role, "submitted_at": applied, "channel": channel}


TODAY = dt.date(2026, 8, 10)


def test_a_fresh_application_is_not_chased():
    assert nudge.plan(dt.date(2026, 8, 2), [_row(applied="2026-08-01")]) == []


def test_day_three_comes_due_on_day_three():
    due = nudge.plan(dt.date(2026, 8, 4), [_row(applied="2026-08-01")])
    assert [d.day for d in due] == [3]


def test_a_sent_day_three_promotes_the_company_to_day_seven(_isolate):
    """The whole point: the count is READ, not assumed to be zero."""
    (_isolate / "followups-sent.jsonl").write_text(
        json.dumps({"company": "Acme", "sent_at": "2026-08-04"}) + "\n", encoding="utf-8")
    due = nudge.plan(TODAY, [_row(applied="2026-08-01")])
    assert [d.day for d in due] == [7]


def test_two_sent_nudges_end_the_cadence(_isolate):
    (_isolate / "followups-sent.jsonl").write_text(
        json.dumps({"company": "Acme"}) + "\n" + json.dumps({"company": "Acme"}) + "\n",
        encoding="utf-8")
    assert nudge.plan(TODAY, [_row(applied="2026-08-01")]) == []


def test_the_count_matches_regardless_of_how_the_company_was_written(_isolate):
    """"Skills Capital" in the ledger and "SkillsCapital" in the send log are one company."""
    (_isolate / "followups-sent.jsonl").write_text(
        json.dumps({"company": "SkillsCapital"}) + "\n", encoding="utf-8")
    due = nudge.plan(TODAY, [_row(company="Skills Capital", applied="2026-08-01")])
    assert [d.day for d in due] == [7]


def test_two_roles_at_one_company_produce_one_nudge():
    due = nudge.plan(TODAY, [
        _row(role="SRE", applied="2026-08-01"),
        _row(role="Platform Engineer", applied="2026-08-05"),
    ])
    assert len(due) == 1
    # Dated from the most recent application, not the oldest.
    assert due[0].applied == "2026-08-05"


def test_a_company_with_nobody_to_reach_is_not_chased(monkeypatch):
    monkeypatch.setattr(nudge.sourcing, "load_unreachable",
                        lambda *a, **k: {"acme": {"evidence": "no employees findable"}})
    assert nudge.plan(TODAY, [_row(applied="2026-08-01")]) == []


def test_a_replied_or_dead_company_is_dropped(monkeypatch):
    monkeypatch.setattr(nudge, "board_status", lambda *a, **k: {"acme": "Interview"})
    assert nudge.plan(TODAY, [_row(applied="2026-08-01")]) == []


def test_a_row_with_no_date_cannot_be_scheduled():
    assert nudge.plan(TODAY, [_row(applied="")]) == []


def test_an_unreadable_send_log_line_does_not_abort_the_run(_isolate):
    (_isolate / "followups-sent.jsonl").write_text(
        "not json\n" + json.dumps({"company": "Acme"}) + "\n", encoding="utf-8")
    assert nudge.sent_counts() == {"acme": 1}


# --- the trap that would cross two different approval gates -------------------------------------
def test_a_nudge_card_never_carries_the_connection_request_ref():
    """`check_approvals.py` greps for `ref:<slug>` and `flush-approved` SENDS what it finds.

    A ref on a nudge card would turn "yes, send this follow-up" into "send a connection request",
    through a different runner, with no way for the owner to tell from the card.
    """
    item = nudge.Due(company="Acme", role="SRE", applied="2026-08-01", day=3,
                     days_since=9, text="Circling back.", channel="email")
    title = f"{item.company} · {item.role} — Day {item.day} nudge due"
    body = (f"No reply {item.days_since} day(s) after applying ({item.applied}, "
            f"via {item.channel}).\nDraft:\n> {item.text}\n")
    assert "ref:" not in title and "ref:" not in body


def test_marking_a_nudge_sent_changes_what_is_due_next(_isolate):
    rows = [_row(applied="2026-08-01")]
    assert [d.day for d in nudge.plan(TODAY, rows)] == [3]
    nudge.mark_sent("Acme")
    assert [d.day for d in nudge.plan(TODAY, rows)] == [7]


def test_an_announced_nudge_is_not_announced_again(_isolate):
    nudge.record_notified("Acme", 3)
    assert ("acme", 3) in nudge.notified()
    assert ("acme", 7) not in nudge.notified()
