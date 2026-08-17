"""Gmail setup: finding a client that already exists, and refusing to call consent 'done'.

2026-08-17: `--authorize` dead-ended at "no OAuth client JSON", while **five** Desktop-app clients
sat in ~/Downloads from other projects. The instruction was to go build one in the Google Cloud
console - work that was already done, twice over, and invisible.

The sharper rule is the second half. The Gmail API is enabled **per Google Cloud project**, so a
client borrowed from another project completes consent perfectly and then 403s every call. A token
on disk therefore proves a human clicked yes and *nothing at all* about whether mail can be read -
which is D35's shape exactly: a channel that reports quiet because it was never readable.
"""

from __future__ import annotations

import json

import pytest

from apps.autopilot.free import gmail

DESKTOP = {"installed": {"client_id": "252077903101-abc.apps.googleusercontent.com",
                         "client_secret": "not-a-real-secret", "redirect_uris": ["http://localhost"]}}
WEB_APP = {"web": {"client_id": "999-xyz.apps.googleusercontent.com",
                   "client_secret": "not-a-real-secret"}}


def write(path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


# =================================================================================================
# Telling a usable client from an unusable one
# =================================================================================================

def test_a_desktop_client_is_usable(tmp_path):
    assert gmail.is_desktop_client(write(tmp_path / "c.json", DESKTOP)) is True


def test_a_web_client_is_rejected(tmp_path):
    """It authorises against registered redirect URIs and dies on a random loopback port with an
    error that blames the port, not the client type."""
    assert gmail.is_desktop_client(write(tmp_path / "c.json", WEB_APP)) is False


def test_unparseable_and_missing_files_are_rejected_not_raised(tmp_path):
    (tmp_path / "junk.json").write_text("{not json", encoding="utf-8")
    assert gmail.is_desktop_client(tmp_path / "junk.json") is False
    assert gmail.is_desktop_client(tmp_path / "nope.json") is False


def test_a_json_array_is_rejected(tmp_path):
    (tmp_path / "arr.json").write_text("[1, 2]", encoding="utf-8")
    assert gmail.is_desktop_client(tmp_path / "arr.json") is False


# =================================================================================================
# Discovery: list them, never choose one
# =================================================================================================

def test_discovery_finds_a_downloaded_client(tmp_path):
    write(tmp_path / "client_secret_252077903101-abc.apps.googleusercontent.com.json", DESKTOP)
    assert gmail.discover_clients((tmp_path,)) != []


def test_discovery_skips_web_clients(tmp_path):
    write(tmp_path / "client_secret_web.json", WEB_APP)
    assert gmail.discover_clients((tmp_path,)) == []


def test_discovery_ignores_unrelated_json(tmp_path):
    write(tmp_path / "package.json", DESKTOP)
    assert gmail.discover_clients((tmp_path,)) == []


def test_a_missing_directory_is_not_a_crash(tmp_path):
    assert gmail.discover_clients((tmp_path / "nope",)) == []


def test_the_installed_credentials_dir_is_searched_before_downloads(tmp_path):
    """Otherwise re-running --authorize could silently switch Google Cloud projects."""
    creds, downloads = tmp_path / "creds", tmp_path / "dl"
    creds.mkdir(); downloads.mkdir()
    write(creds / "gmail-client.json", DESKTOP)
    write(downloads / "client_secret_other.json", DESKTOP)
    found = gmail.discover_clients((creds, downloads))
    assert found[0].parent == creds


def test_newer_downloads_are_offered_first(tmp_path):
    import os, time
    old = write(tmp_path / "client_secret_old.json", DESKTOP)
    new = write(tmp_path / "client_secret_new.json", DESKTOP)
    os.utime(old, (time.time() - 9000, time.time() - 9000))
    assert gmail.discover_clients((tmp_path,))[0] == new


def test_the_same_file_is_never_listed_twice(tmp_path):
    """It matches both globs; a duplicated candidate list makes the count a lie."""
    write(tmp_path / "gmail-client.json", DESKTOP)
    assert len(gmail.discover_clients((tmp_path,))) == 1


# =================================================================================================
# The enable URL, which is useless without the project number
# =================================================================================================

def test_the_project_number_comes_from_the_client_id_prefix(tmp_path):
    assert gmail.project_number(write(tmp_path / "c.json", DESKTOP)) == "252077903101"


def test_a_client_without_a_numeric_prefix_yields_no_project(tmp_path):
    odd = {"installed": {"client_id": "not-a-number.apps.googleusercontent.com"}}
    assert gmail.project_number(write(tmp_path / "c.json", odd)) == ""


def test_a_web_client_yields_no_project(tmp_path):
    assert gmail.project_number(write(tmp_path / "c.json", WEB_APP)) == ""


def test_the_enable_url_targets_the_project():
    assert "project=252077903101" in gmail.enable_url("252077903101")
    assert "gmail.googleapis.com" in gmail.enable_url("")


# =================================================================================================
# Telling 'the API is off' apart from 'the credential is wrong' - both arrive as a 403
# =================================================================================================

REAL_403 = ("<HttpError 403 when requesting https://gmail.googleapis.com/gmail/v1/users/me/profile "
            "returned \"Gmail API has not been used in project 252077903101 before or it is "
            "disabled.\". Details: \"[{'reason': 'SERVICE_DISABLED'}]\">")


def test_a_disabled_api_is_recognised():
    assert gmail.is_api_disabled(REAL_403) is True
    assert gmail.is_api_disabled("accessNotConfigured") is True


def test_an_unrelated_failure_is_not_blamed_on_the_api():
    """Saying 'go enable the API' when the token is simply invalid sends someone to a page that
    already says Enabled, and they conclude the tool is broken."""
    assert gmail.is_api_disabled("invalid_grant: Token has been expired or revoked") is False
    assert gmail.is_api_disabled("") is False


# =================================================================================================
# Installing a chosen client
# =================================================================================================

def test_installing_copies_rather_than_references(tmp_path, monkeypatch):
    """A file left in Downloads is one tidy-up away from breaking every unattended run."""
    dest = tmp_path / "creds"
    monkeypatch.setattr(gmail, "CREDENTIALS_DIR", dest)
    monkeypatch.setattr(gmail, "CLIENT_SECRET", dest / "gmail-client.json")
    source = write(tmp_path / "client_secret_x.json", DESKTOP)
    installed = gmail.install_client(source)
    assert installed.is_file()
    source.unlink()
    assert installed.is_file(), "the installed copy must survive the original being deleted"


# =================================================================================================
# authorize(): the refusals, without ever opening a browser
# =================================================================================================

def test_a_named_client_that_does_not_exist_is_refused(tmp_path, capsys):
    assert gmail.authorize(tmp_path / "nope.json") == 1
    assert "no such file" in capsys.readouterr().out


def test_a_named_web_client_is_refused_before_the_browser_opens(tmp_path, capsys):
    assert gmail.authorize(write(tmp_path / "web.json", WEB_APP)) == 1
    assert "Desktop" in capsys.readouterr().out


def test_with_no_client_the_candidates_are_printed(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(gmail, "CLIENT_SECRET", tmp_path / "absent.json")
    monkeypatch.setattr(gmail, "discover_clients",
                        lambda *a, **k: [tmp_path / "client_secret_found.json"])
    assert gmail.authorize(None) == 1
    out = capsys.readouterr().out
    assert "client_secret_found.json" in out
    assert "--client" in out, "listing candidates without the command to use one is half a message"


def test_with_no_client_and_none_found_it_says_how_to_make_one(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(gmail, "CLIENT_SECRET", tmp_path / "absent.json")
    monkeypatch.setattr(gmail, "discover_clients", lambda *a, **k: [])
    assert gmail.authorize(None) == 1
    assert "Google Cloud console" in capsys.readouterr().out


# =================================================================================================
# The rule this file exists for: consent is not access
# =================================================================================================

def test_verify_access_reports_the_failure_instead_of_raising(monkeypatch):
    class Boom:
        def __getattr__(self, _name):
            raise RuntimeError(REAL_403)
    ok, detail = gmail.verify_access(Boom())
    assert ok is False and detail


def test_a_dead_credential_leaves_no_token_behind(tmp_path, monkeypatch, capsys):
    """The whole point. A stored-but-dead token turns every later run into a 403 that reads like
    an outage, while the fix sits on a page nobody would think to visit."""
    token = tmp_path / "gmail-token.json"
    token.write_text("{}", encoding="utf-8")
    client = write(tmp_path / "gmail-client.json", DESKTOP)

    monkeypatch.setattr(gmail, "TOKEN_PATH", token)
    monkeypatch.setattr(gmail, "CLIENT_SECRET", client)
    monkeypatch.setattr(gmail, "CREDENTIALS_DIR", tmp_path)

    class Flow:
        @staticmethod
        def from_client_secrets_file(*_a, **_k):
            return Flow()

        def run_local_server(self, **_k):
            return object()

    monkeypatch.setitem(__import__("sys").modules, "google_auth_oauthlib.flow",
                        type("M", (), {"InstalledAppFlow": Flow}))
    monkeypatch.setattr(gmail, "verify_access", lambda _c: (False, REAL_403))

    assert gmail.authorize(None) == 1
    assert not token.exists(), "a token that cannot read mail must not be left on disk"
    out = capsys.readouterr().out
    assert "could NOT be read" in out
    assert "console.developers.google.com" in out, "the fix URL is the only useful part"


def test_a_working_credential_stores_the_token_and_says_which_mailbox(tmp_path, monkeypatch, capsys):
    token = tmp_path / "gmail-token.json"
    client = write(tmp_path / "gmail-client.json", DESKTOP)
    monkeypatch.setattr(gmail, "TOKEN_PATH", token)
    monkeypatch.setattr(gmail, "CLIENT_SECRET", client)
    monkeypatch.setattr(gmail, "CREDENTIALS_DIR", tmp_path)

    class Creds:
        @staticmethod
        def to_json():
            return '{"token": "x"}'

    class Flow:
        @staticmethod
        def from_client_secrets_file(*_a, **_k):
            return Flow()

        def run_local_server(self, **_k):
            return Creds()

    monkeypatch.setitem(__import__("sys").modules, "google_auth_oauthlib.flow",
                        type("M", (), {"InstalledAppFlow": Flow}))
    monkeypatch.setattr(gmail, "verify_access", lambda _c: (True, "someone@example.com"))

    assert gmail.authorize(None) == 0
    assert token.is_file()
    out = capsys.readouterr().out
    assert "someone@example.com" in out, "authorising the wrong account is silent otherwise"
    assert "VERIFIED" in out


# =================================================================================================
# The scope stays read-only
# =================================================================================================

def test_the_only_scope_is_readonly():
    """A token that could send is a token that could send the wrong thing unattended."""
    assert gmail.SCOPES == ["https://www.googleapis.com/auth/gmail.readonly"]
    for scope in gmail.SCOPES:
        assert "readonly" in scope
        for verb in (".send", ".modify", ".compose", "mail.google.com"):
            assert verb not in scope


def test_needs_setup_never_reads_as_zero_replies(tmp_path, monkeypatch, capsys):
    """D35 in one assertion."""
    monkeypatch.setattr(gmail, "scan", lambda **_k: gmail.InboxReport(gmail.NEEDS_SETUP, "no client"))
    assert gmail.main([]) == 0
    assert "NOT a report of zero replies" in capsys.readouterr().out


def test_an_unreadable_inbox_exits_two(monkeypatch, capsys):
    monkeypatch.setattr(gmail, "scan", lambda **_k: gmail.InboxReport(gmail.UNREADABLE, "403"))
    assert gmail.main([]) == 2
    assert "NOT 'no replies'" in capsys.readouterr().out
