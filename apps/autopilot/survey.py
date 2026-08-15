"""Read Easy Apply forms and write down every question. Submit nothing.

WHY THIS EXISTS
---------------
`apply-all` reports only the questions the bank FAILED to answer, and only for the steps it
managed to reach. So a run that ends `stalled-validation` tells you one blocker and hides
the four questions behind it. Three consecutive runs on 2026-08-15 produced
`stalled-validation`, `reached-review`, `error` and zero submissions, and each one taught us
exactly one thing before burning an application slot.

Azam's instruction was the right one: read all the forms first, collect the questions, put
the answers in the bank once, and only then apply.

This module walks the SAME wizard `fill.py` walks, using the same scanner, and records
EVERY control on EVERY step - answered or not - with its options. Then it discards the
draft. `submit` is not a parameter here; there is no code path in this file that can send
an application.

    py -3 -m apps.autopilot.survey --limit 30
    py -3 -m apps.autopilot.survey --limit 5 --headless

Output: output/apply-log/form-survey-<date>.json  (machine)
        output/apply-log/form-survey-<date>.md    (what to hand a human)
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

from playwright.sync_api import sync_playwright

from apps.autopilot import fill
from apps.autopilot.answers import NUMERIC, load_bank, located_in_answer, match_field, resolve

REPO = Path(__file__).resolve().parents[2]
BOARD_DB = REPO / "database" / "board.sqlite3"
OUT_DIR = REPO / "output" / "apply-log"


@dataclass
class Question:
    label: str
    tag: str
    required: bool
    numeric: bool
    options: list[str] = field(default_factory=list)
    current: str = ""
    bank_key: str | None = None
    bank_value: str | None = None
    company: str = ""
    role: str = ""
    step: int = 0

    @property
    def answered(self) -> bool:
        return self.bank_value is not None


def _scan_step(bank: dict, modal, step: int, company: str, role: str) -> list[Question]:
    """Record every control on this step. Reuses fill.py's scanner, so what we see here is
    exactly what the filler sees - a survey against a different scanner would certify the
    wrong thing."""
    found: list[Question] = []
    for control in fill._scan(modal):
        label = (control.label or "").strip()
        if label and fill.IGNORE_RE.search(label):
            continue
        options: list[str] = []
        if control.tag in ("group", "select"):
            try:
                options = fill._group_options(control)
            except Exception:
                options = []
        try:
            current = fill._current_value(control)
        except Exception:
            current = ""

        key = value = None
        if label:
            matched = match_field(label)
            if matched:
                key, spec = matched
                try:
                    if key == "located_in_city":
                        value = located_in_answer(bank, label)
                    else:
                        value = resolve(
                            bank, spec,
                            numeric_control=control.numeric or spec.kind == NUMERIC,
                        )
                except Exception:
                    value = None

        found.append(Question(
            label=label or f"(unlabelled {control.tag})",
            tag=control.tag,
            required=bool(control.required),
            numeric=bool(control.numeric),
            options=options,
            current=current,
            bank_key=key,
            bank_value=value,
            company=company, role=role, step=step,
        ))
    return found


def survey_job(page, url: str, bank: dict, company: str = "", role: str = "") -> dict:
    """Walk one wizard, recording questions. Always discards. Never submits."""
    started = time.perf_counter()
    out = {"url": url, "company": company, "role": role,
           "status": "error", "steps": 0, "questions": [], "note": ""}
    try:
        fill.check_logged_in(page)
        ok, why = fill.has_easy_apply(page, url)
        if not ok:
            out["status"] = why or "external-or-none"
            return out

        # Detecting the button is not opening the dialog. Skipping this click made the first
        # survey report `no-next-button, 0 questions` on three jobs that all have real forms -
        # a clean-looking zero produced by never opening anything (D30, and Phase 0's original
        # "the dialog is visible before its contents render" bug).
        page.get_by_role("button", name=re.compile(r"easy apply", re.I)).first.click()
        modal = page.get_by_role("dialog").first
        modal.wait_for(state="visible", timeout=15_000)
        if not fill._wait_for_step_content(modal):
            out["status"] = "modal-never-rendered"
            out["note"] = "dialog shell appeared but the form never streamed in"
            fill._close_modal(page, modal,
                              fill.FillResult(url=url, slug=fill.slug_for(url), status="survey"))
            return out

        seen_labels: set[str] = set()
        stalled = 0

        for step in range(1, fill.MAX_WIZARD_STEPS + 1):
            out["steps"] = step
            fill._wait_for_step_content(modal)
            before = fill._fingerprint(modal)

            for q in _scan_step(bank, modal, step, company, role):
                if q.label in seen_labels:
                    continue
                seen_labels.add(q.label)
                out["questions"].append(asdict(q))

            # Fill what the bank CAN answer, purely to reach the next step. Without this the
            # survey never sees past step 1, which is the blindness it exists to remove.
            result = fill.FillResult(url=url, slug=fill.slug_for(url), status="survey")
            fill._fill_step(bank, modal, result, set())

            button, kind = fill._primary_button(modal)
            if kind in ("review", "submit"):
                out["status"] = f"reached-{kind}"
                break
            if button is None:
                out["status"] = "no-next-button"
                break

            button.click()
            page.wait_for_timeout(fill.SETTLE_MS)
            if fill._fingerprint(modal) == before:
                stalled += 1
                if stalled > fill.MAX_STALLED_ROUNDS:
                    out["status"] = "stalled-validation"
                    break
            else:
                stalled = 0
        else:
            out["status"] = "step-cap-reached"

        # Always discard. This is a read-only pass; leaving drafts behind would be a side
        # effect nobody asked for, and LinkedIn offers to save one on 100% of jobs tested.
        fill._close_modal(page, modal, fill.FillResult(url=url, slug=fill.slug_for(url),
                                                       status="survey"))
    except fill.LinkedInLoggedOut:
        raise
    except Exception as exc:
        out["status"] = "error"
        out["note"] = f"{type(exc).__name__}: {exc}"
    finally:
        out["seconds"] = round(time.perf_counter() - started, 1)
    return out


def board_rows(limit: int) -> list[dict]:
    conn = sqlite3.connect(BOARD_DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT company, job, url FROM jobs WHERE status='New' AND url IS NOT NULL "
        "ORDER BY fit DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def write_report(results: list[dict], stamp: str) -> tuple[Path, Path]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUT_DIR / f"form-survey-{stamp}.json"
    json_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    # Group identical questions across jobs: the same question asked by nine employers is
    # ONE answer to write, and the count is what says which to write first.
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in results:
        for q in r["questions"]:
            groups[q["label"]].append(q)

    unanswered = {k: v for k, v in groups.items() if not any(x["bank_value"] for x in v)}
    answered = {k: v for k, v in groups.items() if any(x["bank_value"] for x in v)}

    lines = [
        f"# Easy Apply form survey - {stamp}",
        "",
        f"Surveyed **{len(results)} job(s)**. Nothing was submitted; every draft was discarded.",
        "",
        f"- distinct questions seen: **{len(groups)}**",
        f"- already answerable from the bank: **{len(answered)}**",
        f"- **NEEDING AN ANSWER: {len(unanswered)}**",
        "",
        "## Outcome per job", "",
        "| status | n |", "|---|---|",
    ]
    for status, n in Counter(r["status"] for r in results).most_common():
        lines.append(f"| {status} | {n} |")

    lines += ["", "## ❓ Questions with no bank answer", "",
              "Ordered by how many employers asked. Answer the top ones first.", ""]
    for label, qs in sorted(unanswered.items(), key=lambda kv: -len(kv[1])):
        q = qs[0]
        req = "**required**" if any(x["required"] for x in qs) else "optional"
        kind = q["tag"] + (", numeric" if q["numeric"] else "")
        lines.append(f"### ({len(qs)}x) {label}")
        lines.append(f"- type: `{kind}` - {req}")
        if q["options"]:
            lines.append(f"- options: {q['options']}")
        askers = sorted({f"{x['company']}" for x in qs})
        lines.append(f"- asked by: {', '.join(askers[:8])}{' ...' if len(askers) > 8 else ''}")
        lines.append("- **ANSWER:** _______")
        lines.append("")

    lines += ["## ✅ Already answered by the bank", ""]
    for label, qs in sorted(answered.items(), key=lambda kv: -len(kv[1])):
        val = next(x["bank_value"] for x in qs if x["bank_value"])
        lines.append(f"- ({len(qs)}x) {label} -> `{val}`")

    md_path = OUT_DIR / f"form-survey-{stamp}.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=30)
    ap.add_argument("--headless", action="store_true")
    args = ap.parse_args(argv)

    rows = board_rows(args.limit)
    if not rows:
        print("no New rows with a URL on the board")
        return 1

    bank = load_bank()
    stamp = date.today().isoformat()
    print(f"Surveying {len(rows)} form(s). NOTHING WILL BE SUBMITTED.\n")

    results = []
    with sync_playwright() as pw:
        context = fill.open_browser(pw, fill.DEFAULT_USER_DATA_DIR, headless=args.headless)
        page = context.pages[0] if context.pages else context.new_page()
        try:
            for i, row in enumerate(rows, 1):
                print(f"[{i}/{len(rows)}] {row['company']} - {row['job'][:52]}")
                res = survey_job(page, row["url"], bank, row["company"], row["job"])
                n_new = sum(1 for q in res["questions"] if not q["bank_value"])
                flag = ""
                # A job we believed had Easy Apply, that yielded no questions at all, is a
                # BLIND READ, not an easy form. Saying so out loud is the whole lesson of the
                # first survey run, which reported three clean zeroes while opening nothing.
                if not res["questions"] and res["status"] not in (
                        "external-or-none", "closed", "removed", "already-applied", "no-buttons"):
                    flag = "   <-- ZERO QUESTIONS SEEN: treat as blind, not as easy"
                print(f"  -> {res['status']}, {len(res['questions'])} question(s), "
                      f"{n_new} unanswered, {res.get('seconds', 0)}s{flag}")
                results.append(res)
        finally:
            context.close()

    json_path, md_path = write_report(results, stamp)
    print(f"\nwrote {json_path.relative_to(REPO)}")
    print(f"wrote {md_path.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
