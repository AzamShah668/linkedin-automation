"""The gate between a free model and a document a recruiter reads.

Asked for a CV summary with no prompting, the free model produced:

    "Results-driven DevOps Engineer with extensive expertise in architecting resilient
     infrastructure..."

Two banned phrases in eleven words. So this validator is not belt-and-braces; it is the reason a
free model is allowed near the CV at all.

⚠️ **Both directions are tested on purpose.** The first version rejected Azam's REAL CV — he is a
student, so his document has "Projects" rather than "Experience", and it uses em-dashes as title
separators. A validator calibrated only on bad input blocks the good input too, and nobody notices
until it refuses real work.
"""

from __future__ import annotations

import pathlib

import pytest

from apps.autopilot.free import cv_validate as V

REAL_CV = V.REPO / "output" / "cv" / "azam-shah-devops-cv.md"

BAD = """Results-driven DevOps Engineer with extensive expertise in architecting resilient
infrastructure. Passionate about cutting-edge, seamless, robust solutions, leveraged across
various teams to spearhead synergy. Experience: things. Skills: stuff."""

# A minimal well-formed CV: no tells, has the sections, long enough, numbers all supported.
CLEAN = ("# Azam Shah\n\n## Summary\nDevOps Engineer who builds and ships production systems.\n\n"
         "## Technical Skills\nDocker, Kubernetes, Ansible, Jenkins, Python.\n\n"
         "## Projects\nBuilt a private cloud on Proxmox and ran GPU Kubernetes in production. "
         "Wrote the deployment pipeline and the tests that gate it. "
         ) + ("Shipped it, ran it, fixed it when it broke. " * 30)


# --- it must reject what the free model actually produced ---------------------------------------
def test_the_measured_bad_prose_is_rejected():
    report = V.validate(BAD, company="Acme", role="DevOps Engineer", corpus="")
    assert not report.ok
    assert any("results-driven" in v for v in report.violations)
    assert any("extensive expertise" in v or "passionate about" in v for v in report.violations)


@pytest.mark.parametrize("phrase", ["leveraged", "spearheaded", "passionate about",
                                    "cutting-edge", "synergy", "robust solutions"])
def test_each_banned_phrase_is_caught(phrase):
    report = V.Report()
    V.check_tells(f"A sentence that says {phrase} in it.", report)
    assert any(phrase in v for v in report.violations)


def test_a_vague_scale_word_is_caught():
    report = V.Report()
    V.check_tells("Worked on various systems.", report)
    assert any("various" in v for v in report.violations)


# --- and it must ACCEPT the real thing ----------------------------------------------------------
@pytest.mark.skipif(not REAL_CV.exists(), reason="no generated CV in this checkout")
def test_the_real_cv_passes():
    """The calibration that matters. This failed twice before the rules were corrected."""
    report = V.validate(REAL_CV.read_text(encoding="utf-8"), role="DevOps Engineer")
    assert report.ok, report.summary()


def test_a_clean_cv_passes():
    # A non-empty corpus: an EMPTY one legitimately fails closed, which is a different test.
    report = V.validate(CLEAN, company="", role="DevOps Engineer",
                        corpus="Proxmox private cloud, GPU Kubernetes, Jenkins, 18 projects.")
    assert report.ok, report.summary()


def test_projects_satisfies_the_work_section_requirement():
    """A student CV has Projects, not Experience. Demanding Experience failed every real one."""
    report = V.Report()
    V.check_structure("## Skills\nx\n## Projects\ny" + "z" * 1000, report)
    assert not any("none of" in v for v in report.violations)


def test_a_cv_with_no_work_section_at_all_is_rejected():
    report = V.Report()
    V.check_structure("## Skills\nPython" + "z" * 1000, report)
    assert any("none of" in v for v in report.violations)


# --- em-dash: overuse, not presence -------------------------------------------------------------
def test_a_few_em_dashes_are_fine():
    """The real CV uses 10 in 6,009 chars, mostly as title separators, and reads human."""
    report = V.Report()
    V.check_tells("word " * 1200 + "a — b — c", report)
    assert not any("em-dash" in v for v in report.violations)


def test_em_dash_spam_is_caught():
    report = V.Report()
    V.check_tells("a — b — c — d — e — f — g — h", report)
    assert any("em-dash" in v for v in report.violations)


# --- fabrication --------------------------------------------------------------------------------
def test_a_number_absent_from_the_dossier_is_flagged():
    report = V.Report()
    V.check_fabrication("Shipped 4242 projects.", report, corpus="He shipped 18 projects.")
    assert any("4242" in v for v in report.violations)


def test_a_supported_number_is_not_flagged():
    report = V.Report()
    V.check_fabrication("Shipped 18 projects.", report, corpus="He shipped 18 projects.")
    assert not report.violations


def test_a_year_is_never_treated_as_fabrication():
    report = V.Report()
    V.check_fabrication("Graduated 2026.", report, corpus="no numbers here")
    assert not report.violations


def test_an_unreadable_dossier_fails_closed(monkeypatch):
    """'We could not check' must never read the same as 'we checked and it was fine'."""
    monkeypatch.setattr(V, "EVIDENCE_FILES", (pathlib.Path("does-not-exist.md"),))
    report = V.Report()
    V.check_fabrication("Shipped 18 projects.", report)
    assert any("cannot verify" in v for v in report.violations)


# --- structure and grounding ---------------------------------------------------------------------
def test_a_truncated_generation_is_caught():
    """Short output is the silent-truncation failure one layer up (MIN_SAFE_MAX_TOKENS)."""
    report = V.Report()
    V.check_structure("## Skills\n## Projects\ntiny", report)
    assert any("fragment" in v for v in report.violations)


def test_an_untailored_cv_is_caught():
    report = V.Report()
    V.check_grounding("Generic CV about Kubernetes.", "Energy Exemplar", "DevOps Engineer", report)
    assert any("Energy Exemplar" in v for v in report.violations)


def test_invented_sentiment_about_the_company_is_caught():
    report = V.Report()
    V.check_grounding("I love what you are building at Acme. devops", "Acme", "DevOps", report)
    assert any("invented sentiment" in v for v in report.violations)


def test_an_empty_generation_is_rejected():
    assert not V.validate("", company="Acme", role="SRE").ok


# --- the blocklist must not drift from the skill --------------------------------------------------
def test_every_banned_phrase_still_appears_in_the_skill():
    """humanization.md is the single source of truth; this file only mirrors it.

    If someone edits the skill and drops a phrase, this fails rather than letting the two versions
    quietly disagree about what an AI tell is.
    """
    if not V.HUMANIZATION.exists():
        pytest.skip("cv-architect skill not present in this checkout")
    skill = V.HUMANIZATION.read_text(encoding="utf-8").lower()
    # The skill writes inflections compactly - "spearhead(ed)", "utilize(d)", "seamless(ly)" - so
    # compare on a PREFIX. (`rstrip` was the first attempt and is wrong: it strips characters, not
    # suffixes, so "seamlessly" became "seamlessl".)
    stems = {p.split()[0][:6] for p in V.BANNED_PHRASES}
    missing = [stem for stem in stems if stem and stem not in skill]
    assert not missing, f"in cv_validate but no longer in humanization.md: {missing}"


def test_the_feedback_is_specific_enough_to_retry_on():
    report = V.validate(BAD, company="Acme", role="SRE", corpus="")
    feedback = report.feedback()
    assert "Fix every one" in feedback
    assert "results-driven" in feedback


# --- number extraction: formatting is not fabrication --------------------------------------------
def test_a_thousands_separator_is_not_two_numbers():
    """"10,000" became {"10","000"} and a real generated CV was rejected for inventing "000"."""
    report = V.Report()
    V.check_fabrication("Served 10,000 requests.", report, corpus="peak was 10,000 requests")
    assert not report.violations


def test_a_thousands_separator_in_only_one_side_still_matches():
    report = V.Report()
    V.check_fabrication("Served 10,000 requests.", report, corpus="peak was 10000 requests")
    assert not report.violations


def test_leading_zeros_are_the_same_claim():
    report = V.Report()
    V.check_fabrication("Ran 007 jobs.", report, corpus="ran 7 jobs")
    assert not report.violations


def test_a_genuinely_invented_number_still_fails_after_normalisation():
    report = V.Report()
    V.check_fabrication("Served 25,000 requests.", report, corpus="peak was 10,000 requests")
    assert any("25000" in v for v in report.violations)


def test_a_trailing_full_stop_is_not_part_of_the_number():
    report = V.Report()
    V.check_fabrication("Shipped 18.", report, corpus="shipped 18 projects")
    assert not report.violations
