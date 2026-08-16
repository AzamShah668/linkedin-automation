"""The loader that makes configuration exist in a scheduled task.

`llm.py` reads `os.getenv` and NOTHING in this project ever loaded `.env` — `python-dotenv` is not
installed either. It only ever worked in a shell where the variables happened to be exported by
hand, so `freetext.py` (the one place an LLM writes to a real employer's form) raised
"LLM_BASE_URL is not set" in every unattended run. Nothing errored visibly, because that code path
is only reached when a form asks a motivation question.

The end-to-end proof lives outside these unit tests and is worth repeating by hand: run
`llm.ask()` in a subprocess whose environment has every LLM_* variable stripped. Before the fix it
raised; after it answers.
"""

from __future__ import annotations

import os

import pytest

from apps.autopilot import env


# --- parsing ------------------------------------------------------------------------------------
def test_a_plain_pair():
    assert env.parse("LLM_MODEL=gemini/flash") == {"LLM_MODEL": "gemini/flash"}


def test_comments_and_blank_lines_are_ignored():
    assert env.parse("# a comment\n\nA=1\n   \n# B=2\n") == {"A": "1"}


def test_surrounding_quotes_are_stripped():
    assert env.parse("A='x'\nB=\"y\"") == {"A": "x", "B": "y"}


def test_an_apostrophe_inside_a_value_survives():
    """Only ONE matching surrounding pair comes off."""
    assert env.parse("A=it's fine") == {"A": "it's fine"}


def test_a_value_containing_equals_is_kept_whole():
    """API keys and base64 secrets routinely contain '='."""
    assert env.parse("KEY=abc=def==") == {"KEY": "abc=def=="}


def test_a_url_with_a_colon_and_port_survives():
    assert env.parse("LLM_BASE_URL=http://localhost:20128/v1") == {
        "LLM_BASE_URL": "http://localhost:20128/v1"}


def test_lines_without_an_equals_are_skipped():
    assert env.parse("just some prose\nA=1") == {"A": "1"}


def test_an_empty_key_is_skipped():
    assert env.parse("=orphan\nA=1") == {"A": "1"}


def test_an_empty_value_is_kept():
    """An explicitly blank setting is a statement, not an absence."""
    assert env.parse("A=") == {"A": ""}


# --- loading ------------------------------------------------------------------------------------
def test_load_adds_missing_values(tmp_path, monkeypatch):
    path = tmp_path / ".env"
    path.write_text("TEST_ADDED_VAR=hello", encoding="utf-8")
    monkeypatch.delenv("TEST_ADDED_VAR", raising=False)
    env.load(path, force=True)
    assert os.environ["TEST_ADDED_VAR"] == "hello"


def test_a_real_environment_variable_always_wins(tmp_path, monkeypatch):
    """setdefault, never assignment. Exporting a var for one run must not be overruled by a file."""
    path = tmp_path / ".env"
    path.write_text("TEST_PRIORITY_VAR=from-file", encoding="utf-8")
    monkeypatch.setenv("TEST_PRIORITY_VAR", "from-shell")
    env.load(path, force=True)
    assert os.environ["TEST_PRIORITY_VAR"] == "from-shell"


def test_a_missing_env_file_is_not_an_error(tmp_path):
    assert env.load(tmp_path / "nope.env", force=True) == 0


def test_values_does_not_touch_the_process(tmp_path, monkeypatch):
    path = tmp_path / ".env"
    path.write_text("TEST_READONLY_VAR=x", encoding="utf-8")
    monkeypatch.delenv("TEST_READONLY_VAR", raising=False)
    assert env.values(path) == {"TEST_READONLY_VAR": "x"}
    assert "TEST_READONLY_VAR" not in os.environ


def test_require_names_the_file_so_the_error_says_what_to_do(monkeypatch):
    monkeypatch.delenv("TEST_ABSENT_VAR", raising=False)
    with pytest.raises(KeyError) as excinfo:
        env.require("TEST_ABSENT_VAR")
    assert ".env" in str(excinfo.value)


def test_the_real_env_file_supplies_the_llm_settings():
    """Guards the actual failure: these four are what llm.py needs and could not see."""
    loaded = env.values()
    if not env.ENV_PATH.exists():
        pytest.skip("no .env in this checkout")
    for key in ("LLM_PROVIDER", "LLM_BASE_URL", "LLM_MODEL"):
        assert key in loaded, f"{key} missing from .env; llm.py cannot run unattended without it"


def test_no_real_secret_is_pinned_in_this_file():
    """A test that asserts a key's VALUE would leak it into a public repo on the next commit.

    The prefixes are assembled rather than written out, or this test matches its own source and
    fails on itself — which is exactly what it did the first time it ran.
    """
    source = (env.REPO / "tests" / "test_env.py").read_text(encoding="utf-8")
    prefixes = ["sk" + "-", "AIz" + "a", "gsk" + "_", "xox" + "b-"]
    found = [p for p in prefixes if p in source]
    assert not found, f"possible secret prefix committed in a test: {found}"
