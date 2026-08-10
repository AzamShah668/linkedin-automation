"""Tests for the never-resubmit ledger.

The load-bearing one is test_second_attempt_on_a_seeded_row_is_blocked: a duplicate application
is irreversible and reads as spam, so this guard failing open is the worst outcome in the app.
"""

from __future__ import annotations

import pytest

from apps.autopilot import ledger


@pytest.fixture
def book(tmp_path):
    return tmp_path / "submitted.jsonl"


def test_second_attempt_on_a_seeded_row_is_blocked(book):
    """THE test. Recro was submitted 2026-07-29 and must never be attempted again."""
    added, _ = ledger.seed(book)
    assert added == len(ledger.SEED)

    reason = ledger.already_applied(
        "Recro", "Generative AI Engineer", "https://www.linkedin.com/jobs/view/4444013362/", book
    )
    assert reason is not None
    assert "2026-07-29" in reason


def test_an_untouched_company_is_not_blocked(book):
    ledger.seed(book)
    assert ledger.already_applied("Energy Exemplar", "DevOps Engineer", "", book) is None


def test_blocks_the_same_role_reposted_under_a_new_job_id(book):
    """Aggregators on this board repost the same req under fresh ids constantly."""
    ledger.seed(book)
    reason = ledger.already_applied(
        "Recro", "Generative AI Engineer", "https://www.linkedin.com/jobs/view/9999999999/", book
    )
    assert reason is not None


def test_blocks_the_same_posting_even_if_the_company_name_is_written_differently(book):
    """The linkedin id is exact; company spelling is not."""
    ledger.seed(book)
    reason = ledger.already_applied(
        "RECRO Technologies", "GenAI Engineer",
        "https://www.linkedin.com/jobs/view/4444013362/", book,
    )
    assert reason is not None
    assert "this exact posting" in reason


def test_company_and_role_matching_ignores_case_and_punctuation(book):
    ledger.record(
        ledger.Entry("CodeRound AI", "AI Engineer (LLMs & Agents)", "2026-07-30", "email"), book
    )
    assert ledger.already_applied("coderound ai", "ai engineer llms agents", "", book) is not None


def test_seed_is_idempotent(book):
    first_added, _ = ledger.seed(book)
    second_added, skipped = ledger.seed(book)
    assert second_added == 0
    assert skipped == first_added
    assert len(ledger.load(book)) == first_added


def test_ledger_imports_nothing_that_could_reach_a_board_status():
    """D29 — a guard must not depend on a field that has already been proven wrong.

    Asserted on the AST's imports, not on the text: the docstring legitimately *discusses*
    Notion and the mirror while explaining why it refuses to read them.
    """
    import ast
    import inspect

    import apps.autopilot.ledger as module

    imported: set[str] = set()
    for node in ast.walk(ast.parse(inspect.getsource(module))):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
            if node.module.startswith("apps.autopilot"):
                imported.add(node.module)

    for forbidden in ("sqlite3", "board_db", "requests", "httpx"):
        assert forbidden not in imported, f"ledger must not import {forbidden}"
    assert not any("board" in name for name in imported)


def test_a_corrupt_line_is_reported_and_skipped_not_silently_dropped(book, capsys):
    ledger.record(ledger.Entry("Acme", "Engineer", "2026-01-01", "email"), book)
    with open(book, "a", encoding="utf-8") as handle:
        handle.write("{not json\n")

    rows = ledger.load(book)
    assert len(rows) == 1
    assert "IGNORED" in capsys.readouterr().out


def test_record_survives_reload(book):
    ledger.record(
        ledger.Entry("Energy Exemplar", "DevOps Engineer", "2026-08-06", "linkedin-easy-apply",
                     linkedin_id="4436200537"),
        book,
    )
    assert ledger.already_applied("Energy Exemplar", "DevOps Engineer", "", book) is not None


# ---------------------------------------------------------------------------------------
# D33 — the company cap must be scoped to channel and recency, not lifetime.
#
# The bug these lock down: counting EVERY ledger row for a company meant one linkedin-dm from
# 2026-07-26 permanently blocked all four Infosys rows, including Junior AI Engineer (fit 90),
# the highest-value row on the board. A cap exists to stop a recruiter seeing the same name
# three times in a morning — not to stop applying to a company you once messaged.
# ---------------------------------------------------------------------------------------

from datetime import date


def _write(book, rows):
    book.write_text("\n".join(
        ledger.Entry(company=c, role=r, submitted_at=when, channel=ch).to_json()
        for c, r, when, ch in rows
    ), encoding="utf-8")


def test_an_old_dm_does_not_block_a_fresh_easy_apply():
    """THE D33 test. Infosys: one linkedin-dm, weeks old, different role."""
    import tempfile, pathlib
    with tempfile.TemporaryDirectory() as d:
        book = pathlib.Path(d) / "l.jsonl"
        _write(book, [("Infosys", "AI Application Engineer", "2026-07-26", "linkedin-dm")])
        hits = ledger.recent_company_submissions(
            "Infosys", path=book, today=date(2026, 8, 10))
        assert hits == [], "an old DM about another role must not block Junior AI Engineer (90)"


def test_a_recent_easy_apply_to_the_same_company_still_blocks(book):
    """The cap's actual job: Crossing Hurdles got two on consecutive days."""
    _write(book, [("Crossing Hurdles", "DevOps Engineer", "2026-08-09", "linkedin-easy-apply")])
    hits = ledger.recent_company_submissions(
        "Crossing Hurdles", path=book, today=date(2026, 8, 10))
    assert len(hits) == 1


def test_an_easy_apply_older_than_the_window_stops_blocking(book):
    _write(book, [("Acme", "DevOps Engineer", "2026-07-01", "linkedin-easy-apply")])
    assert ledger.recent_company_submissions("Acme", path=book, today=date(2026, 8, 10)) == []


def test_an_email_application_does_not_block_an_easy_apply(book):
    """Different channel = a different recruiter surface, and often a different team."""
    _write(book, [("Innova ESI", "DevOps Engineer", "2026-08-09", "email")])
    assert ledger.recent_company_submissions(
        "Innova ESI", path=book, today=date(2026, 8, 10)) == []


def test_an_undateable_row_is_counted_not_ignored(book):
    """Asymmetric failure: over-counting costs a skip, under-counting costs a duplicate."""
    _write(book, [("Acme", "DevOps Engineer", "", "linkedin-easy-apply")])
    assert len(ledger.recent_company_submissions("Acme", path=book, today=date(2026, 8, 10))) == 1


def test_company_matching_ignores_case_and_punctuation(book):
    _write(book, [("Neurones IT Asia", "DevOps Engineer", "2026-08-10", "linkedin-easy-apply")])
    assert len(ledger.recent_company_submissions(
        "neurones-it  asia", path=book, today=date(2026, 8, 10))) == 1


def test_the_exact_posting_guard_is_untouched_by_the_window(book):
    """already_applied() must stay LIFETIME. Recency scoping applies to the CAP only —
    the same posting must never be submitted twice, however long ago it was."""
    _write(book, [("Recro", "Generative AI Engineer", "2026-01-01", "linkedin-easy-apply")])
    assert ledger.already_applied("Recro", "Generative AI Engineer", path=book) is not None
