"""Tests for the Claude Code bridge — specifically the two rules that cost real days.

D17: exit 0 proves nothing; the artifact is the verdict.
D25: a usage limit is not a job failure and must stop the batch without libelling good rows.

These run offline. subprocess.run is stubbed, so no Claude session is consumed.
"""

from __future__ import annotations

import subprocess
from types import SimpleNamespace

import pytest

from apps.autopilot import cv


def _fake_run(stdout: str = "", stderr: str = "", returncode: int = 0):
    def run(*_args, **_kwargs):
        return SimpleNamespace(stdout=stdout, stderr=stderr, returncode=returncode)
    return run


@pytest.fixture
def no_packet(monkeypatch):
    """find_packet always returns None — i.e. Claude wrote no artifact."""
    monkeypatch.setattr(cv, "find_packet", lambda job_id: None)


def test_completed_packet_wins_over_a_usage_limit_message(monkeypatch, tmp_path):
    """Regression, 2026-08-06 first real run.

    The Energy Exemplar packet built completely and Claude hit its session limit immediately
    after. Checking the limit string before the artifact made cv.py disown finished work.
    The artifact on disk outranks any message in the log (D30).
    """
    pdf = tmp_path / "8-Energy-Exemplar-DevOps-Engineer.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")
    monkeypatch.setattr(cv, "PDF_DIR", tmp_path)

    # Matches the real sequence: no packet before the build, a complete one after.
    calls = {"n": 0}

    def find(job_id):
        calls["n"] += 1
        if calls["n"] == 1:
            return None
        return cv.Packet("energy-exemplar", "Energy Exemplar", "DevOps Engineer",
                         "8-Energy-Exemplar-DevOps-Engineer", 92, job_id, tmp_path)

    monkeypatch.setattr(cv, "find_packet", find)
    monkeypatch.setattr(
        subprocess, "run",
        _fake_run(stdout="done\nYou've hit your session limit - resets 9:10pm (Asia/Calcutta)\n"),
    )

    packet = cv.build_packet("job-1")           # must NOT raise
    assert packet.slug == "energy-exemplar"
    assert packet.limit_notice is not None      # but the limit is still surfaced
    assert "9:10pm" in packet.limit_notice


def test_batch_keeps_the_finished_packet_then_stops(monkeypatch, tmp_path):
    """A late limit stops the batch without throwing away the job that completed."""
    good = cv.Packet("a", "A", "R", "stem", 90, "a", tmp_path)
    late = cv.Packet("b", "B", "R", "stem", 90, "b", tmp_path, limit_notice="limit at 9:10pm")

    monkeypatch.setattr(cv, "build_packet", lambda job_id, timeout=None: {"a": good, "b": late}[job_id])
    built, failed, limit = cv.build_many(["a", "b", "c"])

    assert [p.slug for p in built] == ["a", "b"]   # 'b' is kept, not discarded
    assert failed == []
    assert limit is not None and "b completed" in limit


def test_usage_limit_raises_its_own_error_not_a_job_failure(monkeypatch, no_packet):
    monkeypatch.setattr(
        subprocess, "run",
        _fake_run(stdout="working...\nYou've hit your session limit - resets 3:30pm (Asia/Calcutta)\n"),
    )
    with pytest.raises(cv.UsageLimitHit) as exc:
        cv.build_packet("job-1")
    assert "NOT a problem with job job-1" in str(exc.value)
    assert "resets 3:30pm" in str(exc.value)


def test_usage_limit_detected_even_when_exit_code_is_nonzero(monkeypatch, no_packet):
    """The limit must win over the returncode, or it gets filed as a per-job failure (D25)."""
    monkeypatch.setattr(
        subprocess, "run",
        _fake_run(stdout="You've hit your usage limit", returncode=1),
    )
    with pytest.raises(cv.UsageLimitHit):
        cv.build_packet("job-1")


def test_exit_zero_with_no_artifact_is_a_failure(monkeypatch, no_packet):
    """D17 — the whole point. A clean exit that wrote nothing is not a success."""
    monkeypatch.setattr(subprocess, "run", _fake_run(stdout="all done!", returncode=0))
    with pytest.raises(cv.PacketBuildFailed, match="exited 0 but wrote no packet"):
        cv.build_packet("job-1")


def test_failure_reports_stdout_because_claude_prints_errors_there(monkeypatch, no_packet):
    monkeypatch.setattr(
        subprocess, "run",
        _fake_run(stdout="the real error is here", stderr="", returncode=2),
    )
    with pytest.raises(cv.PacketBuildFailed, match="the real error is here"):
        cv.build_packet("job-1")


def test_missing_cli_is_a_clear_message_not_a_filenotfound(monkeypatch, no_packet):
    def boom(*_a, **_k):
        raise FileNotFoundError("claude")
    monkeypatch.setattr(subprocess, "run", boom)
    with pytest.raises(cv.PacketBuildFailed, match="not on PATH"):
        cv.build_packet("job-1")


def test_existing_packet_is_reused_and_claude_is_never_invoked(monkeypatch, tmp_path):
    """Runbook §2 — rebuilding silently overwrites drafts the owner may have approved."""
    def explode(*_a, **_k):
        raise AssertionError("claude must not be invoked when a packet already exists")
    monkeypatch.setattr(subprocess, "run", explode)

    packet = cv.Packet("acme", "Acme", "Engineer", "1-Acme-Engineer", 95, "job-1", tmp_path)
    monkeypatch.setattr(cv, "find_packet", lambda job_id: packet)
    assert cv.build_packet("job-1") is packet


def test_batch_stops_on_usage_limit_and_leaves_the_rest_untouched(monkeypatch):
    """The remaining jobs must NOT appear in `failed` — that is the D25 mistake."""
    calls = []

    def build(job_id, timeout=None):
        calls.append(job_id)
        if job_id == "b":
            raise cv.UsageLimitHit("limit reached")
        return cv.Packet(job_id, "C", "R", "stem", 90, job_id, cv.OUTREACH_DIR)

    monkeypatch.setattr(cv, "build_packet", build)
    built, failed, limit = cv.build_many(["a", "b", "c"])

    assert [p.slug for p in built] == ["a"]
    assert failed == []          # 'b' and 'c' are not failures
    assert calls == ["a", "b"]   # 'c' was never attempted
    assert limit == "limit reached"


def test_batch_records_a_real_failure_against_its_own_job(monkeypatch):
    def build(job_id, timeout=None):
        if job_id == "b":
            raise cv.PacketBuildFailed("genuinely broken")
        return cv.Packet(job_id, "C", "R", "stem", 90, job_id, cv.OUTREACH_DIR)

    monkeypatch.setattr(cv, "build_packet", build)
    built, failed, limit = cv.build_many(["a", "b", "c"])

    assert [p.slug for p in built] == ["a", "c"]   # 'c' still attempted
    assert failed == [("b", "genuinely broken")]
    assert limit is None
