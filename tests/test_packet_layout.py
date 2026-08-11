"""Tests for role-scoped packets (D34).

The deadlock being fixed: the runbook writes ONE packet per company and refuses to overwrite it,
while `find_packet` looks up by JOB ID. For a company's second role neither could ever be
satisfied, so the build reported FAIL forever. It cost Infosys AI/ML Engineer (2026-08-09) and
Junior AI Engineer — fit 90, the best row on the board (2026-08-10).

The property that must hold: **outreach stays per company (D8 — never message the same recruiter
twice), but a CV is per role and must never be attached to a different req.**
"""

from __future__ import annotations

import json

import pytest

from apps.autopilot import cv


@pytest.fixture
def out(tmp_path):
    d = tmp_path / "outreach"
    d.mkdir()
    return d


def _packet(out, folder, company, role, stem, job_id="row-1"):
    p = out / folder
    p.mkdir(parents=True, exist_ok=True)
    (p / "packet.json").write_text(json.dumps({
        "slug": folder, "company": company, "role": role,
        "cv_stem": stem, "ats": 90, "job_id": job_id,
    }), encoding="utf-8")
    return p


def test_the_first_role_keeps_the_plain_company_folder(out):
    """Nothing must move. Eight packets already exist at output/outreach/<company>/."""
    assert cv.packet_dir_for("Infosys", "AI Application Engineer", out).name == "infosys"


def test_a_second_role_gets_its_own_folder(out):
    _packet(out, "infosys", "Infosys", "AI Application Engineer", "2-Infosys-AI-App")
    target = cv.packet_dir_for("Infosys", "Junior AI Engineer", out)
    assert target.name == "infosys--junior-ai-engineer"
    assert target.name != "infosys", "the second role must not overwrite the first"


def test_the_second_role_folder_is_stable(out):
    """Same role asked twice must resolve to the same place, or builds duplicate forever."""
    _packet(out, "infosys", "Infosys", "AI Application Engineer", "2-Infosys-AI-App")
    a = cv.packet_dir_for("Infosys", "Junior AI Engineer", out)
    b = cv.packet_dir_for("Infosys", "Junior AI Engineer", out)
    assert a == b


def test_find_role_packet_matches_company_and_role_not_job_id(out):
    """The board row id and the packet's job_id need not agree; company+role is the real key."""
    _packet(out, "infosys--junior-ai-engineer", "Infosys", "Junior AI Engineer",
            "9-Infosys-Junior-AI", job_id="something-else")
    found = cv.find_role_packet("Infosys", "Junior AI Engineer", out)
    assert found is not None and found.cv_stem == "9-Infosys-Junior-AI"


def test_a_different_role_at_the_same_company_is_NOT_a_match(out):
    """THE safety property. A CV tailored to one req must never be served for another."""
    _packet(out, "infosys", "Infosys", "AI Application Engineer", "2-Infosys-AI-App")
    assert cv.find_role_packet("Infosys", "Junior AI Engineer", out) is None


def test_matching_survives_case_and_punctuation_differences(out):
    _packet(out, "skillscapital", "SkillsCapital", "Site Reliability Engineer (Fully Remote)",
            "5-SC-SRE")
    assert cv.find_role_packet("skills capital",
                               "Site Reliability Engineer (Fully  Remote)", out) is not None


def test_the_company_packet_is_still_discoverable_for_contact_reuse(out):
    """The second role must reuse the first's contact.md, so the sibling has to be findable."""
    _packet(out, "infosys", "Infosys", "AI Application Engineer", "2-Infosys-AI-App")
    sibling = cv.find_company_packet("Infosys", out)
    assert sibling is not None and sibling.role == "AI Application Engineer"


def test_a_company_with_no_packet_has_no_sibling(out):
    assert cv.find_company_packet("Celigo", out) is None


def test_the_role_already_in_the_company_folder_resolves_to_that_folder(out):
    """Otherwise one role gets split across two folders and the first is orphaned."""
    _packet(out, "infosys", "Infosys", "AI Application Engineer", "2-Infosys-AI-App")
    assert cv.packet_dir_for("Infosys", "AI Application Engineer", out).name == "infosys"


def test_an_unreadable_company_packet_does_not_cause_an_overwrite(out):
    """Fail toward a separate folder. Guessing 'same role' on corrupt JSON would destroy work."""
    p = out / "infosys"
    p.mkdir()
    (p / "packet.json").write_text("{ not json", encoding="utf-8")
    assert cv.packet_dir_for("Infosys", "Junior AI Engineer", out).name != "infosys"
