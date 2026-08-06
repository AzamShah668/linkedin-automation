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
FILE_RE = re.compile(r"[\w\-.()]+\.(?:pdf|docx?)", re.I)  # no space in the class, or it eats the label

# The primary footer button is the render sentinel: every wizard step has exactly one, and its
# absence is precisely what broke the 2026-08-06 run.
PRIMARY_BUTTON_RE = re.compile(
    r"continue to next step|review your application|submit application|^next$|^review$|^submit$",
    re.I,
)

# Controls that are real, answerable, and none of our business. Left exactly as LinkedIn set
# them, and kept OUT of the unanswered report so that list stays all-signal.
IGNORE_RE = re.compile(
    r"follow \S+ to stay up to date|stay up to date with their page"
    r"|\.(?:pdf|docx?)",  # the resume chooser group; Phase 0 reports the filename, never swaps it
    re.I,
)

# Answer options are not a question. A fieldset's own text is often just its choices — "Yes",
# or "YesNo" for a two-option radio group — and the real question sits in an ancestor.
ANSWER_TOKEN_RE = re.compile(r"\b(yes|no|true|false|male|female|other|prefer not to say)\b", re.I)


def _looks_like_a_question(text: str) -> bool:
    """True if `text` carries content beyond the answer options themselves."""
    if not text:
        return False
    return len(ANSWER_TOKEN_RE.sub("", text).strip(" *.,:?-")) >= 8


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
    prefilled: list[str] = field(default_factory=list)  # LinkedIn's own value, left untouched
    resume_filename: str | None = None
    resume_expected: str | None = None
    resume_verified: bool | None = None  # None = no packet supplied, so nothing to verify
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


def _deep_text(loc: Locator) -> str:
    """text_content(), which unlike inner_text() also returns visually-hidden text.

    LinkedIn puts a fieldset's question in an accessible-only <legend>. inner_text() returns
    '' for it, which is why every grouped question (Yes/No radios AND consent checkboxes) was
    silently skipped on 2026-08-06 — no label meant `continue`, so it was never filled and
    never reported. Proven by DOM dump, not guessed.
    """
    try:
        return " ".join((loc.text_content(timeout=2000) or "").split())
    except Exception:
        return ""


def _group_label(group: Locator) -> str:
    """The question a fieldset is asking, however LinkedIn chose to hide it.

    Three placements seen in production, in order of preference:
      1. a <legend> — sometimes accessible-only, so read text_content as well as inner_text
      2. inside the fieldset alongside the options
      3. OUTSIDE the fieldset entirely, as a sibling paragraph (Energy Exemplar's consent
         checkbox does this — the fieldset contains only the word "Yes")
    In every case the answer options must be subtracted, or the "question" comes back as "Yes".
    """
    labels = group.locator("label")
    options = [t for t in (_deep_text(labels.nth(i)) for i in range(labels.count())) if t]

    legend = group.locator("legend")
    if legend.count():
        for reader in (_text_of, _deep_text):
            text = reader(legend.first)
            if text and text not in options:
                return text

    def subtract(text: str) -> str:
        for option in options:
            if option in text:
                text = text.replace(option, " ")
        return " ".join(text.split())

    own = _deep_text(group)
    inside = subtract(own)
    # A fieldset whose whole text is "Yes" has NOT told us the question. Energy Exemplar's
    # consent box has no <label> element at all, so there is nothing to subtract and this
    # used to return "Yes" and stop before climbing.
    if _looks_like_a_question(inside):
        return inside

    for level in range(1, 5):
        ancestor = group.locator(f"xpath=ancestor::*[{level}]")
        if not ancestor.count():
            break
        question = " ".join(_deep_text(ancestor.first).replace(own, " ").split())
        if _looks_like_a_question(question):
            return question
    return inside or own


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

    control_id = control.get_attribute("id")
    if control_id:
        lab = scope.locator(f'label[for="{_attr_q(control_id)}"]').first
        if lab.count():
            deep = _deep_text(lab)
            if deep:
                return deep

    container = control.locator(
        "xpath=ancestor::div[@data-test-form-element or contains(@class,'form-component')][1]"
    )
    if container.count():
        text = _text_of(container.first) or _deep_text(container.first)
        return text.splitlines()[0] if text else ""
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
        controls.append(Control(group, _group_label(group), "group", False, _is_required(group)))

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

    # Standalone checkboxes — NOT inside a fieldset. Found 2026-08-06: these were excluded
    # entirely, so a REQUIRED consent checkbox was invisible to the scanner and would have
    # blocked a real submit while reporting nothing at all. Silent blindness, not a blank.
    boxes = modal.locator("input[type=checkbox]")
    for i in range(boxes.count()):
        box = boxes.nth(i)
        try:
            if not box.is_visible() or box.locator("xpath=ancestor::fieldset").count():
                continue
        except Exception:
            continue
        controls.append(Control(box, _label_for(modal, box), "checkbox", False, _is_required(box)))
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
    count = inputs.count()

    for i in range(count):
        radio = inputs.nth(i)
        label_text = _label_for(control.loc, radio).strip().lower()
        if label_text and (label_text == wanted or wanted in label_text):
            rid = radio.get_attribute("id")
            target = control.loc.locator(f'label[for="{_attr_q(rid)}"]').first if rid else radio
            (target if target.count() else radio).click()
            return radio.is_checked()

    # Single hidden checkbox with the visible box drawn in CSS and NO <label> element at all —
    # Energy Exemplar's consent field. Nothing above can match it, so click the visible text
    # and, failing that, force the input. Either way VERIFY with is_checked(): reporting a
    # tick that did not happen is the same class of lie as the PASS-on-a-no-op.
    if count == 1 and wanted in ("yes", "no", "true", "false"):
        box = inputs.first
        want_checked = wanted in ("yes", "true")
        attempts = (
            lambda: control.loc.get_by_text(
                re.compile(rf"^\s*{re.escape(value.strip())}\s*$", re.I)
            ).first.click(),
            lambda: box.set_checked(want_checked, force=True),
        )
        for attempt in attempts:
            try:
                attempt()
            except Exception:
                continue
            if box.is_checked() == want_checked:
                return True
    return False


def _apply(control: Control, value: str) -> bool:
    if control.tag == "group":
        return _fill_group(control, value)
    if control.tag == "checkbox":
        if value.strip().lower() in ("yes", "true", "1"):
            control.loc.check()
        else:
            control.loc.uncheck()
        return True
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
            # NEVER skip silently. An unlabelled control is the 2026-08-06 bug: `continue`
            # meant it was neither filled nor reported, so a required consent checkbox
            # vanished in both directions. Noisy beats invisible.
            marker = f"(unlabelled {control.tag}, required={control.required})"
            if marker not in seen:
                seen.add(marker)
                result.unanswered.append(marker)
            continue
        if IGNORE_RE.search(label):
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
            elif control.tag == "select" and _current_value(control):
                # LinkedIn pre-selected one of ITS OWN verified values and our bank value is not
                # among the options. Leaving it is correct — we must not blank a required field —
                # but it is not an "unanswered" field either. Report it as a mismatch to notice.
                if control.label not in seen:
                    seen.add(control.label)
                    result.prefilled.append(f"{control.label} = {_current_value(control)!r} (bank has {value!r})")
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
def _wait_for_step_content(modal: Locator, timeout: int = 15_000) -> bool:
    """Wait for the step's CONTENTS, not just the dialog element.

    Root cause of the 2026-08-06 run (3 of 5 jobs did nothing): LinkedIn makes the dialog
    visible immediately — title bar, close button — and streams the form in afterwards. The
    VARITE screenshot is a titled dialog wrapping a bare spinner. `modal.wait_for(visible)`
    was satisfied by that shell, so the scan found zero controls and zero buttons, and the
    job was written off in under four seconds.

    The primary footer button is the sentinel: every step has exactly one, and it is the very
    element whose absence caused the bug. This is an auto-wait, not a poll and not a sleep.
    """
    try:
        modal.get_by_role("button", name=PRIMARY_BUTTON_RE).first.wait_for(
            state="visible", timeout=timeout
        )
        return True
    except PWTimeout:
        return False


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
    match = FILE_RE.search(_text_of(modal) or _deep_text(modal))
    if match:
        result.resume_filename = match.group(0).strip()


def _attach_resume(page: Page, modal: Locator, pdf: Path, result: FillResult) -> bool | None:
    """Upload the TAILORED CV and read the filename back off the page to prove it landed.

    Runbook §5: LinkedIn pre-fills the résumé slot with whatever was uploaded last, which is
    almost always another company's CV. Confirmed in production on every job tested — the slot
    showed the generic `azam-shah-devops-cv.pdf` every time.

    The read-back is not optional. A wrong filename here means a company receives a CV written
    for a different company, and nothing downstream would ever notice.

    Returns True (verified), False (mismatch), or None (no résumé step on this page).
    """
    file_input = modal.locator("input[type=file]")
    upload_button = modal.get_by_role("button", name=re.compile(r"upload (resume|cv)", re.I))

    if not file_input.count() and not upload_button.count():
        return None  # not the resume step

    result.resume_expected = pdf.name
    if result.resume_filename == pdf.name:
        return True  # already the right one; re-uploading just costs time

    if file_input.count():
        file_input.first.set_input_files(str(pdf))
    else:
        # There is NO input[type=file] anywhere in the DOM — verified 2026-08-06 by counting it
        # on every step of a live form. "Upload resume" opens a NATIVE file chooser via JS, so
        # set_input_files has nothing to target and the upload silently never happens.
        with page.expect_file_chooser() as chooser_info:
            upload_button.first.click()
        chooser_info.value.set_files(str(pdf))

    try:
        modal.get_by_text(pdf.stem, exact=False).first.wait_for(state="visible", timeout=20_000)
    except PWTimeout:
        pass

    _capture_resume(modal, result)
    return result.resume_filename == pdf.name


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


def fill_job(page: Page, url: str, bank: dict, cv_pdf: Path | None = None) -> FillResult:
    """Fill one Easy Apply wizard and stop at Review/Submit. Never clicks Submit.

    `cv_pdf` is the TAILORED CV from a built packet. When supplied it is uploaded and the
    filename is read back; a mismatch aborts the job rather than leaving the wrong company's
    CV attached.
    """
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
        if not _wait_for_step_content(modal):
            result.status = "modal-never-rendered"
            result.note = "dialog shell appeared but the form never streamed in"
            SHOT_DIR.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(SHOT_DIR / f"{result.slug}.png"))
            _close_modal(page, modal, result)
            return result

        seen: set[str] = set()
        stalled = 0

        for step in range(1, MAX_WIZARD_STEPS + 1):
            result.steps = step
            _wait_for_step_content(modal)  # each new step streams in the same way
            before = _fingerprint(modal)
            _fill_step(bank, modal, result, seen)
            _capture_resume(modal, result)

            if cv_pdf is not None:
                verified = _attach_resume(page, modal, cv_pdf, result)
                if verified is False:
                    result.status = "resume-mismatch"
                    result.note = (
                        f"expected {cv_pdf.name!r}, page shows {result.resume_filename!r}. "
                        f"Refusing to continue — this is how a company receives another "
                        f"company's CV."
                    )
                    result.resume_verified = False
                    break
                if verified is True:
                    result.resume_verified = True

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
