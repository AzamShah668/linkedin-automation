"""The OmniRoute stack's pure logic: pitch extraction, discovery parsing, CV plumbing.

Everything here runs without a browser and without a model. The browser halves are exercised live;
these are the rules that must not drift.
"""

from __future__ import annotations

import json

import pytest

from apps.autopilot.free import cv as freecv
from apps.autopilot.free import discover, dm

# =================================================================================================
# discover.py — the one parameter that matters
# =================================================================================================


def test_the_search_url_uses_the_filter_that_works():
    """f_AL, never f_EA. LinkedIn silently ignores f_EA and returns the unfiltered set (D45):
    same query, same minute, 1-of-18 became 17-of-17. The MCP still emits the broken one."""
    url = discover.search_url("DevOps Engineer")
    assert "f_AL=true" in url
    assert "f_EA" not in url


def test_the_search_url_is_scoped_and_sorted():
    url = discover.search_url("AI Engineer", location="India", days=7)
    assert "AI%20Engineer" in url
    assert "India" in url
    assert "f_TPR=r604800" in url          # 7 days
    assert "sortBy=DD" in url


def test_a_normal_card_parses():
    row = discover.parse_card("123", [
        "DevOps Engineer", "DevOps Engineer", "Acme Corp", "Bengaluru, India", "Easy Apply",
    ])
    assert row == {"id": "123", "title": "DevOps Engineer", "company": "Acme Corp",
                   "location": "Bengaluru, India", "easyApply": True, "posted": "", "alumni": ""}


def test_the_duplicated_title_is_collapsed():
    """LinkedIn emits the title twice: once as the anchor text, once as the heading."""
    row = discover.parse_card("1", ["SRE", "SRE", "Acme", "Remote"])
    assert row["title"] == "SRE" and row["company"] == "Acme"


def test_chrome_lines_are_dropped():
    row = discover.parse_card("1", ["Promoted", "SRE", "Acme", "Remote", "Actively reviewing"])
    assert row["title"] == "SRE" and row["company"] == "Acme"


def test_a_card_without_easy_apply_is_recorded_as_such():
    """Recorded from the PAGE, never assumed from the query - a silently ignored filter is D45."""
    row = discover.parse_card("1", ["SRE", "Acme", "Remote"])
    assert row["easyApply"] is False


def test_an_unusable_card_is_dropped_not_guessed():
    assert discover.parse_card("1", ["just one line"]) is None
    assert discover.parse_card("1", []) is None


def test_the_scrape_file_matches_what_intake_reads(tmp_path):
    rows = [discover.parse_card("9", ["SRE", "Acme", "Remote", "Easy Apply"])]
    path = discover.write_scrape(rows, tmp_path / "jobs-test.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert "jobs" in payload
    assert payload["jobs"][0]["id"] == "9"
    # intake.collect() keys on exactly these two.
    assert payload["jobs"][0]["easyApply"] is True


# =================================================================================================
# dm.py — the text is never generated, and a withheld pitch stays withheld
# =================================================================================================

PITCH_FILE = """# Touch 2 — LinkedIn · Acme · SRE

- status:   READY TO SEND
- research: nothing verified

---

## 2b — Direct message (1st degree / after they accept)

> Hi Asha, thanks for connecting!
>
> I applied for the SRE role at Acme.
>
> Cheers, Azam

---
**Generated, not hand-written.** No em-dashes.
"""


def test_the_2b_block_is_extracted_without_its_wrapper():
    text = dm.extract_2b(PITCH_FILE)
    assert text.startswith("Hi Asha, thanks for connecting!")
    assert text.endswith("Cheers, Azam")


def test_no_document_furniture_reaches_the_recipient():
    text = dm.extract_2b(PITCH_FILE)
    for junk in ("status:", "research:", "Touch 2", "Generated, not hand-written", "---"):
        assert junk not in text


def test_blank_lines_inside_the_message_survive():
    assert "\n\n" in dm.extract_2b(PITCH_FILE)


def test_a_file_with_no_2b_block_yields_nothing():
    assert dm.extract_2b("# Touch 2\n\n## 2a — Connection note\n\n> hi") == ""


def test_empty_input_yields_nothing():
    assert dm.extract_2b("") == ""


def test_a_missing_pitch_is_a_refusal_not_an_improvisation(tmp_path):
    text, why = dm.pitch_for("nobody", outreach_dir=tmp_path)
    assert text == ""
    assert "withheld" in why or "no touch-2" in why


def test_a_withheld_pitch_is_not_found_by_globbing(tmp_path):
    """The Berribot pitch was RENAMED so no sender could reach it (D50). A glob would undo that."""
    folder = tmp_path / "berribot"
    folder.mkdir()
    (folder / "touch-2-linkedin.WITHHELD.md").write_text(PITCH_FILE, encoding="utf-8")
    text, why = dm.pitch_for("berribot", outreach_dir=tmp_path)
    assert text == "", "a withheld pitch must never be picked up"
    assert "withheld" in why


def test_a_present_pitch_is_found(tmp_path):
    folder = tmp_path / "acme"
    folder.mkdir()
    (folder / "touch-2-linkedin.md").write_text(PITCH_FILE, encoding="utf-8")
    text, why = dm.pitch_for("acme", outreach_dir=tmp_path)
    assert why == ""
    assert text.startswith("Hi Asha")


def test_a_pitch_file_with_an_empty_2b_is_refused(tmp_path):
    folder = tmp_path / "acme"
    folder.mkdir()
    (folder / "touch-2-linkedin.md").write_text("# Touch 2\n\nno block here", encoding="utf-8")
    text, why = dm.pitch_for("acme", outreach_dir=tmp_path)
    assert text == "" and "2b" in why


def test_only_a_send_counts_as_ok():
    assert dm.Delivery("s", "p", "u", dm.SENT).ok is True
    for outcome in (dm.NO_PITCH, dm.NOT_CONNECTED, dm.ERROR):
        assert dm.Delivery("s", "p", "u", outcome).ok is False


# --- the real files on disk ------------------------------------------------------------------
def test_the_real_withheld_berribot_pitch_is_unreachable():
    """Live guard: this one was withheld by a human decision and must stay that way."""
    text, _why = dm.pitch_for("berribot")
    assert text == ""


def test_a_real_generated_pitch_extracts_cleanly():
    text, why = dm.pitch_for("ansr")
    if not text:
        pytest.skip(f"no ansr pitch in this checkout ({why})")
    assert text.startswith("Hi ")
    assert "status:" not in text


# =================================================================================================
# free/cv.py — plumbing that does not need a model
# =================================================================================================


def test_the_prompt_tells_the_model_the_same_rules_it_is_graded_on():
    """Grading against a different rulebook than the one you handed over never converges."""
    prompt = freecv.build_prompt("Acme", "SRE", "", "some dossier")
    for phrase in ("results-driven", "cutting-edge", "synergy"):
        assert phrase in prompt


def test_the_prompt_carries_the_dossier_and_forbids_inventing():
    prompt = freecv.build_prompt("Acme", "SRE", "", "HE SHIPPED 18 PROJECTS")
    assert "HE SHIPPED 18 PROJECTS" in prompt
    assert "did not happen" in prompt


def test_the_dossier_is_capped_so_the_fallback_can_accept_it():
    """Groq's free tier refused 14,463 tokens against a 12,000 limit. A prompt only the primary
    can take makes the fallback useless exactly when the gateway is down."""
    prompt = freecv.build_prompt("Acme", "SRE", "", "x" * 100_000)
    assert len(prompt) < 20_000


def test_retry_feedback_is_included_when_present():
    prompt = freecv.build_prompt("Acme", "SRE", "", "d", feedback="- banned phrase 'synergy'")
    assert "REJECTED" in prompt and "synergy" in prompt


def test_code_fences_are_stripped():
    assert freecv._strip_fences("```markdown\n# CV\ntext\n```") == "# CV\ntext"
    assert freecv._strip_fences("# CV\ntext") == "# CV\ntext"


def test_success_does_not_require_a_written_file():
    """--dry-run reported FAILED while printing 'attempt 1: PASS' because ok required a path."""
    passing = freecv.cv_validate.Report()
    assert freecv.BuildResult("A", "R", None, 1, passing, text="# CV").ok is True


def test_an_empty_generation_is_never_ok():
    passing = freecv.cv_validate.Report()
    assert freecv.BuildResult("A", "R", None, 1, passing, text="").ok is False


def test_a_failing_report_is_never_ok():
    failing = freecv.cv_validate.Report()
    failing.fail("banned phrase")
    assert freecv.BuildResult("A", "R", None, 1, failing, text="# CV").ok is False


def test_the_free_cv_never_overwrites_the_claude_packet():
    """Both engines must be comparable side by side; that is why the Claude one is kept."""
    import inspect
    source = inspect.getsource(freecv.build)
    assert "cv-free.md" in source


# --- the CV sweep: the free stack's sweep-packets.ps1 ---------------------------------------------
def test_the_sweep_only_considers_applied_rows(tmp_path):
    """A tailored CV for a job nobody applied to is work in the wrong order."""
    import sqlite3
    db = tmp_path / "board.sqlite3"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE jobs (id TEXT, job TEXT, company TEXT, fit INT, status TEXT)")
    conn.executemany("INSERT INTO jobs VALUES (?,?,?,?,?)", [
        ("1", "SRE", "Applied Co", 90, "Applied"),
        ("2", "SRE", "New Co", 95, "New"),
        ("3", "SRE", "Skipped Co", 99, "Skipped"),
    ])
    conn.commit(); conn.close()
    rows = freecv.rows_needing_a_cv(limit=5, db=db)
    assert [r[0] for r in rows] == ["Applied Co"]


def test_the_sweep_orders_by_fit(tmp_path):
    import sqlite3
    db = tmp_path / "board.sqlite3"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE jobs (id TEXT, job TEXT, company TEXT, fit INT, status TEXT)")
    conn.executemany("INSERT INTO jobs VALUES (?,?,?,?,?)", [
        ("1", "SRE", "Low", 70, "Applied"),
        ("2", "SRE", "High", 95, "Applied"),
    ])
    conn.commit(); conn.close()
    assert [r[0] for r in freecv.rows_needing_a_cv(limit=5, db=db)] == ["High", "Low"]


def test_the_sweep_respects_its_limit(tmp_path):
    import sqlite3
    db = tmp_path / "board.sqlite3"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE jobs (id TEXT, job TEXT, company TEXT, fit INT, status TEXT)")
    conn.executemany("INSERT INTO jobs VALUES (?,?,?,?,?)",
                     [(str(i), "SRE", f"Co{i}", 90, "Applied") for i in range(6)])
    conn.commit(); conn.close()
    assert len(freecv.rows_needing_a_cv(limit=2, db=db)) == 2


def test_a_missing_board_is_not_a_crash(tmp_path):
    assert freecv.rows_needing_a_cv(limit=2, db=tmp_path / "nope.sqlite3") == []


def test_a_row_that_already_has_a_free_cv_is_skipped(tmp_path, monkeypatch):
    """Otherwise every sweep rebuilds the same top row forever and never reaches the rest."""
    import sqlite3
    db = tmp_path / "board.sqlite3"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE jobs (id TEXT, job TEXT, company TEXT, fit INT, status TEXT)")
    conn.executemany("INSERT INTO jobs VALUES (?,?,?,?,?)", [
        ("1", "SRE", "Done Co", 95, "Applied"),
        ("2", "SRE", "Todo Co", 90, "Applied"),
    ])
    conn.commit(); conn.close()

    outreach = tmp_path / "outreach"
    (outreach / "done-co--sre").mkdir(parents=True)
    (outreach / "done-co--sre" / "cv-free.md").write_text("already built", encoding="utf-8")
    monkeypatch.setattr(freecv, "OUTREACH_DIR", outreach)

    assert [r[0] for r in freecv.rows_needing_a_cv(limit=5, db=db)] == ["Todo Co"]
