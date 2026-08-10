"""Tests for pre-application sourcing screens.

The asymmetry under test is the whole point, and it is the OPPOSITE of replies.py:

  * blocking a real company costs a job opportunity — unrecoverable
  * letting a shell through costs one application slot — about fifteen seconds

So heuristics may only DEPRIORITIZE. Only recorded evidence may BLOCK. Several tests below exist
purely to stop a future change from promoting a suspicion into a block.
"""

from __future__ import annotations

import json

import pytest

from apps.autopilot import sourcing


@pytest.fixture
def book(tmp_path):
    return tmp_path / "unreachable.json"


def test_a_company_with_recorded_evidence_is_blocked(book):
    """THE test. Crossing Hurdles took two application slots and could never be followed up."""
    sourcing.record_unreachable("Crossing Hurdles", "zero employees findable on LinkedIn", path=book)
    v = sourcing.screen("Crossing Hurdles", "DevOps Engineer ($60/hr Remote)", path=book)
    assert v.blocks
    assert "no findable human" in v.reason


def test_an_ordinary_company_is_applied_to(book):
    assert sourcing.screen("Celigo", "AI Integration Engineer", path=book).action == sourcing.APPLY


# ---------------------------------------------------------------------------------------
# Heuristics DEPRIORITIZE. They must never block.
# ---------------------------------------------------------------------------------------

@pytest.mark.parametrize("role", [
    "DevOps Engineer ($60/hr Remote)",
    "AWS Cloud Engineer ($60/hr Remote)",
    "Cloud Engineer (Fully Remote) - Top US MNC",
    "Urgently hiring DevOps Engineer",
])
def test_agency_tells_deprioritize_but_never_block(book, role):
    v = sourcing.screen("Some Agency", role, path=book)
    assert v.action == sourcing.DEPRIORITIZE
    assert not v.blocks, "a title pattern is a suspicion, not evidence — it must not cost an opportunity"


def test_a_legitimate_contract_role_is_not_lost(book):
    """A real employer CAN post an hourly rate. Deprioritized is fine; dropped is not."""
    v = sourcing.screen("Real Employer", "Senior SRE ($95/hr, 12-month contract)", path=book)
    assert v.action == sourcing.DEPRIORITIZE
    assert not v.blocks


def test_evidence_beats_heuristics_but_both_are_reported(book):
    sourcing.record_unreachable("Shell Co", "no employees on LinkedIn", path=book)
    assert sourcing.screen("Shell Co", "DevOps Engineer ($60/hr Remote)", path=book).blocks


# ---------------------------------------------------------------------------------------
# Recording evidence
# ---------------------------------------------------------------------------------------

def test_recording_requires_actual_evidence(book):
    """A bare assertion must not be able to block a company."""
    with pytest.raises(ValueError):
        sourcing.record_unreachable("Someone", "", path=book)
    with pytest.raises(ValueError):
        sourcing.record_unreachable("Someone", "   ", path=book)


def test_company_matching_ignores_case_and_punctuation(book):
    sourcing.record_unreachable("Crossing  Hurdles", "none found", path=book)
    assert sourcing.screen("crossing-hurdles", "DevOps Engineer", path=book).blocks


def test_recording_is_idempotent_and_keeps_the_evidence(book):
    sourcing.record_unreachable("A Co", "first finding", path=book)
    sourcing.record_unreachable("A Co", "second, better finding", path=book)
    data = json.loads(book.read_text(encoding="utf-8"))
    assert len(data["companies"]) == 1
    assert data["companies"]["A Co"]["evidence"] == "second, better finding"


def test_a_missing_evidence_file_blocks_nobody(book):
    assert sourcing.load_unreachable(book) == {}
    assert sourcing.screen("Anyone", "DevOps Engineer", path=book).action == sourcing.APPLY


def test_a_corrupt_evidence_file_is_reported_and_blocks_nobody(book, capsys):
    """Fail toward applying. An unreadable list must not silently block every company."""
    book.write_text("{ not json", encoding="utf-8")
    assert sourcing.load_unreachable(book) == {}
    assert "NOTHING is being blocked" in capsys.readouterr().out
