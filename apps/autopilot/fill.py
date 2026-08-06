"""Open a LinkedIn Easy Apply job, fill the form from the answer bank, STOP BEFORE SUBMIT.

Playwright LIBRARY, sync API — not the Playwright MCP. No screenshots-as-input, no vision.
The browser finds elements itself via the DOM; nothing is sent to a model.

PHASE 0 MAKES ZERO LLM CALLS. A field we cannot answer is logged and left blank, and the run
KEEPS GOING — the point of Phase 0 is the timing number and the consolidated list of missing
bank keys. The runbook's "unknown-required -> abort the job" rule is a SUBMIT-path rule;
nothing here submits.

Never calls page.evaluate() or any JS injection against an employer's form (runbook §Failure
rules). Everything below is ordinary locator reads.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from pathlib import Path

from playwright.sync_api import Locator, Page, TimeoutError as PWTimeout, sync_playwright

from apps.autopilot.answers import NUMERIC, REPO, load_bank, lookup, match_field, resolve

# The LinkedIn-logged-in profile is the SUBDIRECTORY, not .pw_browser itself.
# .pw_browser/ was opened by the owner's real Chrome 150 on 2026-08-01; Chromium refuses to
# open a profile written by a newer build and exits instantly (code 21). linkedin_user_data/
# is on 145, older than Playwright's build, which upgrades forward cleanly. Override with
# PW_USER_DATA_DIR.
DEFAULT_USER_DATA_DIR = REPO / ".pw_browser" / "linkedin_user_data"
SHOT_DIR = REPO / "output" / "apply-log" / "phase0"

MAX_WIZARD_STEPS = 10
MAX_STALLED_ROUNDS = 2
SETTLE_MS = 450  # brief settle after Next; every real wait is Playwright auto-wait.

NEXT_LABELS = re.compile(r"continue to next step|^next$|^continue$", re.I)
REVIEW_LABELS = re.compile(r"review your application|^review$", re.I)
SUBMIT_LABELS = re.compile(r"submit application|^submit$", re.I)
FILE_RE = re.compile(r"[\w\-. ()]+\.(?:pdf|docx?)", re.I)


class LinkedInLoggedOut(RuntimeError):
    """The persistent profile is not signed in. Abort the WHOLE run; never attempt a login."""


@dataclass
class Filled:
    label: str
    key: str
    value: str


@dataclass
class FillResult:
    url: str
    slug: str
    status: str
    seconds: float = 0.0
    steps: int = 0
    filled: list[Filled] = field(default_factory=list)
    unanswered: list[str] = field(default_factory=list)
    resume_filename: str | None = None
    draft_offered: bool | None = None
    note: str = ""


# ---------------------------------------------------------------------------------------
# small DOM helpers — read-only, no JS
# ---------------------------------------------------------------------------------------
def _attr_q(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _text_of(loc: Locator) -> str:
    try:
        return " ".join(loc.inner_text(timeout=2000).split())
    except Exception:
        return ""


def _label_for(scope: Locator, control: Locator) -> str:
    aria = control.get_attribute("aria-label")
    if aria and aria.strip():
        return " ".join(aria.split())

    labelled_by = control.get_attribute("aria-labelledby")
    if labelled_by:
        parts = [
            _text_of(scope.locator(f'[id="{_attr_q(i)}"]').first)
            for i in labelled_by.split()
        ]
        joined = " ".join(p for p in parts if p)
        if joined:
            return joined

    control_id = control.get_attribute("id")
    if control_id:
        lab = scope.locator(f'label[for="{_attr_q(control_id)}"]').first
        if lab.count():
            text = _text_of(lab)
            if text:
                return text

    container = control.locator(
        "xpath=ancestor::div[@data-test-form-element or contains(@class,'form-component')][1]"
    )
    if container.count():
        return _text_of(container.first).splitlines()[0] if _text_of(container.first) else ""
    return ""


def _is_required(control: Locator) -> bool:
    return (
        control.get_attribute("aria-required") == "true"
        or control.get_attribute("required") is not None
    )


def _is_numeric(control: Locator) -> bool:
    if control.get_attribute("type") == "number":
        return True
    return (control.get_attribute("inputmode") or "").lower() in ("numeric", "decimal")


@dataclass
class Control:
    loc: Locator
    label: str
    tag: str          # input | select | textarea | group
    numeric: bool
    required: bool


def _scan(modal: Locator) -> list[Control]:
    """Enumerate every answerable control on the current wizard step."""
    controls: list[Control] = []

    groups = modal.locator("fieldset")
    for i in range(groups.count()):
        group = groups.nth(i)
        if group.locator("input[type=radio], input[type=checkbox]").count() == 0:
            continue
        legend = _text_of(group.locator("legend").first) if group.locator("legend").count() else ""
        controls.append(Control(group, legend, "group", False, False))

    singles = modal.locator(
        "input:not([type=hidden]):not([type=radio]):not([type=checkbox])"
        ":not([type=file]):not([type=submit]):not([type=button]), select, textarea"
    )
    for i in range(singles.count()):
        ctl = singles.nth(i)
        try:
            if not ctl.is_visible():
                continue
        except Exception:
            continue
        # Identify a <select> by structure, without JS: only selects have <option> children.
        tag_name = "select" if ctl.locator("option").count() else "input"
        controls.append(
            Control(ctl, _label_for(modal, ctl), tag_name, _is_numeric(ctl), _is_required(ctl))
        )
    return controls


def _current_value(control: Control) -> str:
    try:
        return (control.loc.input_value(timeout=1500) or "").strip()
    except Exception:
        return ""


# ---------------------------------------------------------------------------------------
# filling
# ---------------------------------------------------------------------------------------
def _fill_select(control: Control, value: str) -> bool:
    options = control.loc.locator("option")
    texts = [(_text_of(options.nth(i)), options.nth(i).get_attribute("value") or "")
             for i in range(options.count())]
    wanted = value.strip().lower()

    for text, val in texts:
        if text.strip().lower() == wanted:
            control.loc.select_option(label=text)
            return True
    for text, val in texts:
        if wanted and (wanted in text.lower() or wanted in val.lower()):
            control.loc.select_option(label=text)
            return True
    return False


def _fill_group(control: Control, value: str) -> bool:
    wanted = value.strip().lower()
    inputs = control.loc.locator("input[type=radio], input[type=checkbox]")
    for i in range(inputs.count()):
        radio = inputs.nth(i)
        label_text = _label_for(control.loc, radio).strip().lower()
        if label_text == wanted or (wanted and wanted in label_text):
            rid = radio.get_attribute("id")
            target = control.loc.locator(f'label[for="{_attr_q(rid)}"]').first if rid else radio
            (target if target.count() else radio).click()
            return True
    return False


def _apply(control: Control, value: str) -> bool:
    if control.tag == "group":
        return _fill_group(control, value)
    if control.tag == "select":
        return _fill_select(control, value)
    if _current_value(control) == value:
        return True  # already correct — don't retype, it costs time
    control.loc.fill(value)
    return True


def _fill_step(bank: dict, modal: Locator, result: FillResult, seen: set[str]) -> int:
    """Map the WHOLE step first, then fill. Returns how many fields were newly filled."""
    controls = _scan(modal)
    plan: list[tuple[Control, str, str]] = []

    for control in controls:
        label = control.label
        if not label:
            continue
        matched = match_field(label)
        if matched is None:
            if label not in seen:
                seen.add(label)
                result.unanswered.append(label)
            continue

        key, spec = matched
        value = resolve(bank, spec, numeric_control=control.numeric or spec.kind == NUMERIC)

        # Bank rule: the LPA form is legal only when the label says LPA and the field takes text.
        if key == "expected_ctc" and not control.numeric and "lpa" in label.lower():
            value = lookup(bank, "compensation.expected_ctc_india_lpa") or value

        if value is None:
            if label not in seen:
                seen.add(label)
                result.unanswered.append(label)
            continue
        plan.append((control, key, value))

    filled_now = 0
    for control, key, value in plan:
        try:
            if _apply(control, value):
                result.filled.append(Filled(control.label, key, value))
                filled_now += 1
            elif control.label not in seen:
                seen.add(control.label)
                result.unanswered.append(f"{control.label}  (no option matched {value!r})")
        except Exception as exc:
            if control.label not in seen:
                seen.add(control.label)
                result.unanswered.append(f"{control.label}  (fill failed: {type(exc).__name__})")
    return filled_now


# ---------------------------------------------------------------------------------------
# wizard navigation
# ---------------------------------------------------------------------------------------
def _primary_button(modal: Locator) -> tuple[Locator | None, str]:
    buttons = modal.locator("button")
    for i in range(buttons.count()):
        btn = buttons.nth(i)
        name = (btn.get_attribute("aria-label") or _text_of(btn) or "").strip()
        if not name or not btn.is_visible():
            continue
        if SUBMIT_LABELS.search(name):
            return btn, "submit"
        if REVIEW_LABELS.search(name):
            return btn, "review"
        if NEXT_LABELS.search(name):
            return btn, "next"
    return None, ""


def _fingerprint(modal: Locator) -> str:
    progress = modal.locator("progress").first
    value = progress.get_attribute("value") if progress.count() else ""
    labels = [c.label for c in _scan(modal)]
    return f"{value}|{'§'.join(labels)}"


def _capture_resume(modal: Locator, result: FillResult) -> None:
    if result.resume_filename:
        return
    match = FILE_RE.search(_text_of(modal))
    if match:
        result.resume_filename = match.group(0).strip()


def _close_modal(page: Page, modal: Locator, result: FillResult) -> None:
    """Dismiss and DISCARD, so no half-filled application is left sitting in LinkedIn's UI."""
    try:
        dismiss = modal.locator('button[aria-label*="Dismiss" i]').first
        if dismiss.count():
            dismiss.click()
        else:
            page.keyboard.press("Escape")
        page.wait_for_timeout(SETTLE_MS)

        discard = page.get_by_role("button", name=re.compile(r"discard", re.I)).first
        save = page.get_by_role("button", name=re.compile(r"^save$", re.I)).first
        result.draft_offered = bool(save.count())
        if discard.count():
            discard.click()
            page.wait_for_timeout(SETTLE_MS)
    except Exception as exc:
        result.note = (result.note + f" close-modal: {type(exc).__name__}").strip()


def slug_for(url: str) -> str:
    match = re.search(r"/jobs/view/(\d+)", url)
    return match.group(1) if match else re.sub(r"\W+", "-", url)[-40:]


def check_logged_in(page: Page) -> None:
    page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=60_000)
    url = page.url
    if "/login" in url or "/signup" in url or "/checkpoint" in url:
        raise LinkedInLoggedOut(f"linkedin-logged-out (landed on {url})")
    if page.locator("input#username").count() and page.locator("input#username").first.is_visible():
        raise LinkedInLoggedOut("linkedin-logged-out (sign-in form on /feed/)")


def has_easy_apply(page: Page, url: str, timeout_ms: int = 20_000) -> tuple[bool, str]:
    """Open a posting and report whether a real Easy Apply button is there."""
    page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
    try:
        page.wait_for_selector("button", timeout=8_000)
    except PWTimeout:
        return False, "no-buttons"
    body = _text_of(page.locator("body"))
    if re.search(r"no longer accepting applications", body, re.I):
        return False, "closed"
    if page.get_by_role("button", name=re.compile(r"easy apply", re.I)).count():
        return True, "easy-apply"
    if re.search(r"\bApplied\b", body):
        return False, "already-applied"
    return False, "external-or-none"


def fill_job(page: Page, url: str, bank: dict) -> FillResult:
    """Fill one Easy Apply wizard and stop at Review/Submit. Never clicks Submit."""
    result = FillResult(url=url, slug=slug_for(url), status="error")
    started = time.perf_counter()
    try:
        ok, why = has_easy_apply(page, url)
        if not ok:
            result.status = why
            return result

        page.get_by_role("button", name=re.compile(r"easy apply", re.I)).first.click()
        modal = page.get_by_role("dialog").first
        modal.wait_for(state="visible", timeout=15_000)

        seen: set[str] = set()
        stalled = 0

        for step in range(1, MAX_WIZARD_STEPS + 1):
            result.steps = step
            before = _fingerprint(modal)
            _fill_step(bank, modal, result, seen)
            _capture_resume(modal, result)

            button, kind = _primary_button(modal)
            if kind in ("review", "submit"):
                result.status = f"reached-{kind}"
                break
            if button is None:
                result.status = "no-next-button"
                break

            button.click()
            page.wait_for_timeout(SETTLE_MS)

            # Runbook: LinkedIn REVEALS questions hidden behind a field that failed validation.
            # A non-advancing step therefore means re-scan, not retry — the loop does that.
            if _fingerprint(modal) == before:
                stalled += 1
                if stalled > MAX_STALLED_ROUNDS:
                    result.status = "stalled-validation"
                    break
            else:
                stalled = 0
        else:
            result.status = "step-cap-reached"

        SHOT_DIR.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(SHOT_DIR / f"{result.slug}.png"))
        _capture_resume(modal, result)
        _close_modal(page, modal, result)

    except LinkedInLoggedOut:
        raise
    except Exception as exc:
        result.status = "error"
        result.note = f"{type(exc).__name__}: {exc}"
    finally:
        result.seconds = time.perf_counter() - started
    return result


def open_browser(playwright, user_data_dir: Path, headless: bool = False):
    user_data_dir.mkdir(parents=True, exist_ok=True)
    return playwright.chromium.launch_persistent_context(
        user_data_dir=str(user_data_dir),
        headless=headless,
        viewport={"width": 1360, "height": 940},
        args=["--disable-blink-features=AutomationControlled"],
    )


__all__ = [
    "FillResult",
    "LinkedInLoggedOut",
    "check_logged_in",
    "fill_job",
    "has_easy_apply",
    "load_bank",
    "open_browser",
    "slug_for",
    "sync_playwright",
]
