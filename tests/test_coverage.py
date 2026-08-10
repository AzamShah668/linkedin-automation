"""Tests for the "did this application reach a human?" report.

The defect being locked down (D32): eight submissions went out and five reached nobody. That was
found by a hand audit on the day someone happened to ask. Nothing tracked it.

The load-bearing property: **over-reporting coverage hides a real gap.** So a signal must mean a
human was actually identified, and anything ambiguous counts as NOT covered.
"""

from __future__ import annotations

import json

import pytest

from apps.autopilot import coverage


@pytest.fixture
def tree(tmp_path, monkeypatch):
    out = tmp_path / "outreach"
    out.mkdir()
    invites = out / "pending-invites.json"
    monkeypatch.setattr(coverage, "OUTREACH_DIR", out)
    monkeypatch.setattr(coverage, "INVITES_PATH", invites)
    monkeypatch.setattr(coverage.sourcing, "load_unreachable", lambda *a, **k: {})
    return out, invites


def _contact(out, slug, body="# Contact\n\nRecruiter: someone real\n"):
    d = out / slug
    d.mkdir(parents=True, exist_ok=True)
    (d / "contact.md").write_text(body, encoding="utf-8")


def _row(company, role="DevOps Engineer", when="2026-08-09", channel="linkedin-easy-apply"):
    return {"company": company, "role": role, "submitted_at": when, "channel": channel}


def test_an_application_with_no_contact_is_a_gap(tree):
    assert [g.company for g in coverage.gaps([_row("Recro")])] == ["Recro"]


def test_a_researched_company_is_covered(tree):
    out, _ = tree
    _contact(out, "celigo")
    assert coverage.gaps([_row("Celigo")]) == []


def test_a_pending_invite_counts_as_coverage(tree):
    _, invites = tree
    invites.write_text(json.dumps({"invites": [
        {"slug": "neurones-it-asia", "status": "pending"}]}), encoding="utf-8")
    assert coverage.gaps([_row("Neurones IT Asia")]) == []


def test_a_contact_file_recording_NOBODY_is_not_coverage(tree):
    """Crossing Hurdles has a contact.md whose content is 'no contact findable'.

    Treating the mere existence of the file as coverage would mark the exact company that proved
    the problem as solved.
    """
    out, _ = tree
    _contact(out, "crossing-hurdles",
             "# Contact - Crossing Hurdles - NO CONTACT FINDABLE\n\nzero employees\n")
    assert [g.company for g in coverage.gaps([_row("Crossing Hurdles")])] == ["Crossing Hurdles"]


def test_a_company_recorded_unreachable_is_not_reported_as_a_gap(tree, monkeypatch):
    """A dead end is not an outstanding task. Reporting it forever would train the reader to
    ignore the report, which is how a real gap gets missed."""
    monkeypatch.setattr(coverage.sourcing, "load_unreachable",
                        lambda *a, **k: {"crossinghurdles": {"evidence": "none found"}})
    assert coverage.gaps([_row("Crossing Hurdles")]) == []


def test_company_name_and_folder_slug_need_not_match_exactly(tree):
    out, _ = tree
    _contact(out, "goodspace")
    assert coverage.gaps([_row("GoodSpace AI")]) == []


def test_each_company_is_reported_once_not_once_per_application(tree):
    """SkillsCapital took four slots. Four identical lines would bury the other gaps."""
    rows = [_row("SkillsCapital", "SRE"), _row("SkillsCapital", "DevOps"),
            _row("SkillsCapital", "Cloud")]
    assert len(coverage.gaps(rows)) == 1


def test_oldest_gap_comes_first(tree):
    rows = [_row("New Co", when="2026-08-10"), _row("Old Co", when="2026-07-29")]
    assert [g.company for g in coverage.gaps(rows)] == ["Old Co", "New Co"]


def test_an_unreadable_invites_file_does_not_fabricate_coverage(tree):
    """Failing toward 'covered' would hide gaps. Fail toward reporting them."""
    _, invites = tree
    invites.write_text("{ not json", encoding="utf-8")
    assert [g.company for g in coverage.gaps([_row("Recro")])] == ["Recro"]
