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


# --- the duplicate-send guard ---------------------------------------------------------------
# mark_sent() failing is WORSE than the send failing: the message has already reached a real
# person, and an unrecorded delivery means they get the identical pitch again next run. The path
# that used to be silent was a non-zero exit code from the tracker, which is also the likeliest.

class _Proc:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


def test_a_tracker_refusal_is_loud_and_says_how_to_fix_it(monkeypatch, capsys):
    monkeypatch.setattr(dm.subprocess, "run",
                        lambda *a, **k: _Proc(1, "", "no invite with that username"))
    assert dm.mark_sent("someone-123") is False
    out = capsys.readouterr().out
    assert "sent twice" in out, "the consequence must be stated, not just the error"
    assert "invite_tracker.py mark-sent" in out, "a warning with no remedy is half a warning"
    assert "someone-123" in out


def test_a_crashed_tracker_is_also_loud(monkeypatch, capsys):
    def boom(*_a, **_k):
        raise OSError("tracker is gone")
    monkeypatch.setattr(dm.subprocess, "run", boom)
    assert dm.mark_sent("someone-123") is False
    assert "re-sent next run" in capsys.readouterr().out


def test_a_clean_exit_records_the_delivery(monkeypatch):
    monkeypatch.setattr(dm.subprocess, "run", lambda *a, **k: _Proc(0))
    assert dm.mark_sent("someone-123") is True


def test_an_unverified_send_is_not_a_send():
    """PAID FOR LIVE, 2026-08-17. An earlier version reported `sent, but could not read it back`,
    counted it SENT and marked the tracker. The inbox ten minutes later: six conversations, newest
    a week old, no thread with him at all. The pitch was recorded as delivered to a man who never
    got it and would never be sent one."""
    assert dm.Delivery("s", "p", "u", dm.UNVERIFIED, "not in the thread").ok is False


def test_a_confirmed_delivery_carries_the_marker():
    assert dm.CONFIRMED in dm.Delivery("s", "p", "u", dm.SENT,
                                       f"{dm.CONFIRMED}: the message is in the thread").detail


# --- the probe used to recognise our own message ------------------------------------------------

def test_the_probe_skips_the_greeting():
    """'Hi Shale, thanks for connecting!' is also LinkedIn's own canned suggestion, so finding it
    in a thread proves nothing about whether OUR pitch landed."""
    probe = dm._probe("Hi Shale, thanks for connecting!\n\n"
                      "I applied for the AI Systems Lab Developer role and it lines up closely.")
    assert probe
    assert "thanks for connecting" not in probe


def test_the_probe_survives_a_one_line_pitch():
    assert dm._probe("A single substantial line of pitch text that is well over thirty chars")


def test_an_empty_pitch_has_no_probe():
    """An empty probe must never be treated as 'found', or every send confirms itself."""
    assert dm._probe("") == ""
    assert dm._probe("short") == ""


# --- finding the Message control ---------------------------------------------------------------
# Taken from a real profile dump, 2026-08-17. dm.py looked for a BUTTON named /message/ and found
# nothing, so someone who had accepted 15 hours earlier was reported "not connected" and would
# never have been pitched. The control is an <a>. Loosening the match is how you then message a
# stranger from the sidebar, so the fix is anchored, not widened.

OWNER_URN = "ACoAABtyRzkBTk1wyC4CwfoeEmVasI1SmY0T_Ig"
STRANGER_URN = "ACoAADl3N7gBxUebgQFSQvHdAx-yZU1Z7_xHoe0"


class _Loc:
    """Minimal Playwright locator stand-in: a list of (name, href)."""

    def __init__(self, items):
        self._items = list(items)

    def count(self):
        return len(self._items)

    @property
    def first(self):
        return _Loc(self._items[:1])

    def nth(self, i):
        return _Loc([self._items[i]])

    def get_attribute(self, attr):
        return self._items[0][1] if attr == "href" and self._items else None


class _Page:
    """Serves get_by_role('link'|'button', name=<regex>) out of a fixed control list."""

    def __init__(self, links=(), buttons=()):
        self._by_role = {"link": list(links), "button": list(buttons)}

    def get_by_role(self, role, name=None):
        return _Loc([(n, h) for n, h in self._by_role.get(role, [])
                     if name is None or name.search(n)])


def compose(urn):
    return f"/messaging/compose/?profileUrn=urn%3Ali%3Afsd_profile%3A{urn}&recipient={urn}"


def test_the_message_control_is_found_even_though_it_is_a_link():
    page = _Page(links=[("Message", compose(OWNER_URN))])
    control, urn, why = dm.message_control(page)
    assert control is not None and why == ""
    assert urn == OWNER_URN


def test_a_button_named_message_still_works():
    """LinkedIn A/B tests this control; matching only the link would swap one blindness for another."""
    page = _Page(buttons=[("Message", "")])
    control, _urn, why = dm.message_control(page)
    assert control is not None and why == ""


def test_sidebar_message_links_are_not_mistaken_for_the_profile_owner():
    """'Message Anjum Latif' is a suggested profile in the sidebar. Clicking it opens a composer
    addressed to a stranger - D50 through a different door."""
    page = _Page(links=[("Message Anjum Latif", compose(STRANGER_URN)),
                        ("Message Dhruv Gupta", compose("ACoAABJVYgsBc1SNHLEVGjvKUWuM5s2ooCflYGQ"))])
    control, _urn, why = dm.message_control(page)
    assert control is None
    assert "no Message control" in why


def test_the_owners_control_is_picked_out_of_a_page_full_of_sidebar_links():
    page = _Page(links=[
        ("Message", compose(OWNER_URN)),
        ("Message", compose(OWNER_URN)),               # LinkedIn renders it twice
        ("Message with Premium", compose(OWNER_URN)),  # InMail; different name, ignored
        ("Message Anjum Latif", compose(STRANGER_URN)),
        ("Message Saket Kumar", compose("ACoAAAMXCfIBY-ul4U0QaXKQEkN9N01zUzzvvJs")),
    ])
    control, urn, why = dm.message_control(page)
    assert control is not None and why == ""
    assert urn == OWNER_URN, "the recipient must be the profile owner, never a sidebar suggestion"


def test_disagreeing_recipients_are_refused_rather_than_guessed():
    """If two controls both called exactly 'Message' point at different people, the page is not
    what we think it is. Guessing here sends a real message to the wrong human."""
    page = _Page(links=[("Message", compose(OWNER_URN)), ("Message", compose(STRANGER_URN))])
    control, _urn, why = dm.message_control(page)
    assert control is None
    assert "refusing to guess" in why


def test_no_controls_at_all_reports_why():
    control, _urn, why = dm.message_control(_Page())
    assert control is None and why


def test_message_with_premium_alone_is_not_a_send_path():
    """InMail is not a 1st-degree message and spends a paid credit."""
    control, _urn, why = dm.message_control(_Page(links=[("Message with Premium", compose(OWNER_URN))]))
    assert control is None and "no Message control" in why


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
