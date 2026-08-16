"""The message a recruiter actually reads.

`watch-accepts` sends the exact 2b text and is forbidden from inventing one. When D48 made
connecting automatic, 8 of 14 outstanding invites had no pitch file at all — so the first person to
accept would have been met with silence. Getting an accept and having nothing to say is worse than
never asking, because the other person has now done something and been ignored.

The style rules below are not preferences. Each one is a tell that has already reached, or nearly
reached, a real recruiter from this repo.
"""

from __future__ import annotations

import re

from apps.autopilot import families, pitch

EM_DASH = "—"
RELATIVE_TIME = re.compile(
    r"\b(yesterday|today|tomorrow|this morning|earlier|just now|last week|recently)\b", re.I)

ROLES = [
    ("DevOps Engineer", families.DEVOPS),
    ("Site Reliability Engineer", families.DEVOPS),
    ("AI/ML Developer", families.AI_ML),
    ("LLMOps Engineer", families.AI_ML),
    ("Software Engineer", families.GENERAL),
]


def _msg(role="AI/ML Developer", person="Asha Rao", company="Acme"):
    return pitch.message(person, company, role)


# --- the tells ---------------------------------------------------------------------------------
def test_no_em_dash_in_any_generated_message():
    """The single most recognisable AI tell in this project's own style rules. Two templates
    carried one undetected for weeks because no message had ever been rendered from real data."""
    for role, _family in ROLES:
        assert EM_DASH not in _msg(role=role), f"em-dash leaked into the {role} pitch"


def test_no_em_dash_in_the_templates_themselves():
    for table in (pitch.OPENERS, pitch.SECOND_LINE):
        for family, text in table.items():
            assert EM_DASH not in text, f"em-dash in the {family} template"


def test_no_relative_time_words():
    """D22: written now, sent hours later on a randomised delay. "Yesterday" rots in between."""
    for role, _family in ROLES:
        found = RELATIVE_TIME.search(_msg(role=role))
        assert not found, f"relative time word {found and found.group(0)!r} in the {role} pitch"


def test_no_invented_company_flattery():
    """A detail is either researched or absent. This generator researches nothing."""
    text = _msg().lower()
    for tell in ("love what you", "excited about your", "impressed by", "your mission",
                 "big fan of", "admire"):
        assert tell not in text, f"invented company flattery: {tell!r}"


def test_open_source_is_framed_at_project_level():
    """The highlight-reel guardrail: 140K stars belong to the project, never to him."""
    text = _msg(role="AI/ML Developer")
    if "140K" in text:
        assert "contribute to" in text


# --- the substance -----------------------------------------------------------------------------
def test_the_role_and_company_appear_verbatim():
    text = pitch.message("Asha Rao", "Hyper Lychee Labs", "LLMOps Engineer")
    assert "Hyper Lychee Labs" in text and "LLMOps Engineer" in text


def test_each_family_gets_its_own_opener():
    devops = _msg(role="DevOps Engineer")
    aiml = _msg(role="LLMOps Engineer")
    assert devops != aiml
    assert "Ansible" in devops
    assert "RAG" in aiml


def test_every_message_carries_the_cv_and_github():
    for role, _family in ROLES:
        text = _msg(role=role)
        assert pitch.CV_URL in text
        assert pitch.GITHUB_URL in text


def test_the_message_is_deterministic():
    """Same inputs, same message — so what was reviewed is what gets sent."""
    assert _msg() == _msg()


# --- the greeting ------------------------------------------------------------------------------
def test_a_shouted_name_is_not_shouted_back():
    """LinkedIn stores plenty of names in caps. "Hi SHALE" reads as a mail merge."""
    assert pitch.message("SHALE FRANCIS", "Acme", "SRE").startswith("Hi Shale,")


def test_only_the_first_name_is_used():
    assert pitch.message("Asha Rao", "Acme", "SRE").startswith("Hi Asha,")


def test_a_parenthetical_nickname_is_dropped():
    assert pitch.message("Manoj Jain (MJ)", "Acme", "SRE").startswith("Hi Manoj,")


def test_a_missing_name_degrades_to_something_sendable():
    assert pitch.message("", "Acme", "SRE").startswith("Hi there,")


# --- writing -----------------------------------------------------------------------------------
def test_it_never_clobbers_a_researched_pitch(tmp_path):
    """A hand-written pitch with a real hook is strictly better and must survive a backfill."""
    folder = tmp_path / "acme"
    folder.mkdir()
    (folder / "touch-2-linkedin.md").write_text("hand written, researched", encoding="utf-8")
    path, written = pitch.write("acme", "Asha", "Acme", "SRE", outreach_dir=tmp_path)
    assert written is False
    assert path.read_text(encoding="utf-8") == "hand written, researched"


def test_overwrite_is_possible_when_asked(tmp_path):
    folder = tmp_path / "acme"
    folder.mkdir()
    (folder / "touch-2-linkedin.md").write_text("old", encoding="utf-8")
    _path, written = pitch.write("acme", "Asha", "Acme", "SRE",
                                 outreach_dir=tmp_path, overwrite=True)
    assert written is True


def test_the_document_marks_that_no_research_was_done(tmp_path):
    path, _ = pitch.write("acme", "Asha", "Acme", "SRE", outreach_dir=tmp_path)
    body = path.read_text(encoding="utf-8")
    assert "NO verified company-specific hook" in body
    assert "## 2b" in body, "watch-accepts extracts the 2b block by this heading"
