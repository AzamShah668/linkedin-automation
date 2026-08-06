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
