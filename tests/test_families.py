"""Tests for role-family routing.

The risk being tested: a job silently getting the WRONG family's CV. A DevOps CV sent to an
AI Engineer req is not a small error, it is the application wasted.
"""

from __future__ import annotations

import pytest

from apps.autopilot import families


@pytest.mark.parametrize(
    "title,expected",
    [
        ("DevOps Engineer", families.DEVOPS),
        ("Site Reliability Engineer", families.DEVOPS),
        ("Platform Engineer, IAM, Authentication", families.DEVOPS),
        ("Cloud and Observability Engineer", families.DEVOPS),
        ("Build & Release / DevSecOps Engineer", families.DEVOPS),
        ("Multi-Cloud DevOps Administrator & Infrastructure Engineer", families.DEVOPS),
        ("Software Engineer - DevOps", families.DEVOPS),
        ("AI Engineer", families.AI_ML),
        ("AI/ML Engineer", families.AI_ML),
        ("Gen AI Engineer", families.AI_ML),
        ("Machine Learning Engineer (LLM+RAG+AI Modeling)", families.AI_ML),
        ("Prompt Engineer, Multi-Agent Systems", families.AI_ML),
        ("AI Deployment Engineer, Codex | India", families.AI_ML),
        ("Analyst, AI Engineer", families.AI_ML),
        ("Python Developer", families.GENERAL),
        # "Application Developer" is a general SWE role that merely mentions cloud. Routing it
        # to DevOps would send infrastructure evidence to a fullstack req.
        ("Application Developer - Cloud FullStack", families.GENERAL),
        ("Software Developer Engineer (Fresher)", families.GENERAL),
    ],
)
def test_family_routing(title, expected):
    assert families.family_for(title) == expected


def test_mlops_goes_to_ai_not_devops():
    """MLOps postings ask for model lifecycle work, not cluster work — even though the word
    looks like Ops and the DevOps pattern would otherwise claim it."""
    assert families.family_for("GenAI Engineer | LLMs, NLP & Cloud (MLOps)") == families.AI_ML
    assert families.family_for("AI Platform & DevOps Engineer") == families.DEVOPS


def test_ai_devops_hybrids_go_to_devops():
    """Both families fit; DevOps leads with the better-evidenced half of the portfolio."""
    assert families.family_for("AI DevOps Engineer") == families.DEVOPS
    assert families.family_for("Applied AI Site Reliability Engineer II") == families.DEVOPS


def test_every_family_has_a_cv_stem():
    for family in (families.DEVOPS, families.AI_ML, families.GENERAL):
        assert families.FAMILY_CV[family]


def test_a_tailored_packet_always_beats_the_family_cv(monkeypatch, tmp_path):
    from apps.autopilot import cv as cv_module

    pdf = tmp_path / "8-Energy-Exemplar-DevOps-Engineer.pdf"
    pdf.write_bytes(b"%PDF")
    packet = cv_module.Packet("energy-exemplar", "Energy Exemplar", "DevOps Engineer",
                              "8-Energy-Exemplar-DevOps-Engineer", 90, "row-1", tmp_path)
    monkeypatch.setattr(cv_module, "PDF_DIR", tmp_path)
    monkeypatch.setattr(cv_module, "find_packet", lambda rid: packet)

    choice = families.pick_cv("row-1", "Energy Exemplar", "DevOps Engineer")
    assert choice.kind == "tailored"


def test_missing_family_cv_is_reported_not_silently_skipped(monkeypatch, tmp_path):
    """No CV must never mean 'apply with whatever LinkedIn pre-filled'."""
    from apps.autopilot import cv as cv_module

    monkeypatch.setattr(cv_module, "find_packet", lambda rid: None)
    monkeypatch.setattr(families, "PDF_DIR", tmp_path)  # empty dir

    choice = families.pick_cv("row-9", "Acme", "DevOps Engineer")
    assert choice.kind == "none"
    assert choice.pdf is None
    assert "NO CV" in choice.label
