# 31 — Running an application batch (the whole loop, in order)

> **Read this FIRST when the ask is "find jobs and apply".** It exists because working that
> out from scratch on 2026-08-15 cost an entire session and three wasted apply runs. Following
> it costs about six commands. Every warning below was paid for once; do not re-derive them.
>
> Proven 2026-08-15: **0 submissions → 20 confirmed submissions** in one day.

---

## The loop

```
purge stale → discover (f_AL=true) → load → SURVEY → fill the bank → apply → diagnose the rest
```

**Never skip SURVEY.** It is the step that makes the whole thing cheap.

---

## 0. Is the board even worth applying to?

```bash
py -3 -c "
import sqlite3, datetime as dt
c=sqlite3.connect('database/board.sqlite3')
for s,n in c.execute(\"select status, count(*) n from jobs group by status order by n desc\"): print(n,s)
for a,n in c.execute(\"select found, count(*) n from jobs where status='New' group by found order by found\"): print(' found',a,n)
"
```

⚠️ **Discovery rots in about five days.** On 2026-08-15 every `New` row was 14-21 days old and
an `apply-all` over them submitted **0 of 32** — 9 postings were already closed and 13 were not
Easy Apply. **A row older than ~7 days is an archive entry, not a backlog item.**

Purge and re-discover instead of grinding old rows:

```bash
cp database/board.sqlite3 /tmp/board-backup.sqlite3     # always back up first
py -3 -c "
import sqlite3; c=sqlite3.connect('database/board.sqlite3')
c.execute(\"delete from jobs where status='New'\"); c.commit()
print('purged')"
```

Delete **only `New`**. `Applied` and `Invite sent` are the record; `Skipped` is the dedupe
memory that stops junk being re-added tomorrow.

---

## 1. Discover — the one parameter that matters

### ⚠️ `f_AL=true`, NOT `f_EA=true`

LinkedIn **silently ignores `f_EA`** and returns the unfiltered set. It is also what the
LinkedIn MCP's `search_jobs(easy_apply=True)` puts in the URL, so **that flag does nothing
either**. Same query, same minute:

| filter | Easy Apply hits |
|---|---|
| `f_EA=true` | **1 of 18** |
| `f_AL=true` | **17 of 17** |

This single wrong parameter is why 13 of 32 rows came back `external-or-none` (D45).

```
https://www.linkedin.com/jobs/search/?keywords=<KW>&location=India&f_TPR=r604800&f_AL=true&sortBy=DD
```

`f_TPR=r604800` = past week. `sortBy=DD` = newest first.

### Scraping the results

Navigate with the Playwright MCP, then one `browser_evaluate` per keyword that scrolls,
harvests, and clicks through pages. **Save to a file** with the `filename` parameter so the
job list never enters context.

Two traps:

- ⚠️ **Never select the results pane by class name.** LinkedIn ships obfuscated, rotating
  classes (`LwOMWkdcwjxyNbocfBZZNRTrZvgogtY`). The list virtualises, so without scrolling the
  right container you get **7 cards out of 121** and think that is the result set. Select it
  structurally: *the scrollable element that contains job cards*.
- **Paginate inside one call**: it is an SPA, so `button[aria-label="Page N"]` advances without
  a reload. 17 → 32 → 48 → 64 in a single evaluate.

Two keyword sweeps ("DevOps Engineer", "AI Engineer") yielded **115 unique Easy Apply roles**.

### Load them

Score from the title, dedupe on URL and company+title, drop anything under 70, insert as `New`
with `found` = today. Title-only scoring is a triage ORDERING signal, not a judgement — no JD
is fetched, and that is fine at this stage.

---

## 2. SURVEY — read every form, submit nothing

```bash
py -3 -u -m apps.autopilot.survey --limit 45
```

Writes `output/apply-log/form-survey-<date>.{json,md}`. The `.md` groups every question by how
many employers asked it, with options, split into *answerable* and *needs an answer*.

**Why this step exists.** `apply-all` reports only the questions the bank FAILED on, and only
for the steps it reached. A run that stalls on page 3 hides everything behind page 3, so each
failed application teaches exactly one thing and **spends a real application slot to learn it**.
The survey costs zero slots: 44 forms → **104 distinct questions** in one pass.

⚠️ **A job that yields ZERO questions is a blind read, not an easy form.** The first survey run
reported `no-next-button, 0 questions` on three jobs that all have real forms, because it
detected the Easy Apply button and never clicked it (`has_easy_apply()` only *detects*).
The survey now shouts `ZERO QUESTIONS SEEN` instead of printing a tidy `0`.

---

## 3. Fill the bank from the survey

Most "missing" answers are **not missing information** — they are phrasings `FIELD_MAP` does
not recognise for data the bank already holds ("expected **total annual** compensation" never
reached `expected (ctc|salary|compensation)`). Check that before asking the owner anything.

Check what is still unanswerable after each edit:

```bash
py -3 -c "
import json
from apps.autopilot.answers import load_bank, match_field, resolve, NUMERIC, located_in_answer, tech_years_answer
bank=load_bank(); d=json.load(open('output/apply-log/form-survey-<DATE>.json',encoding='utf-8'))
labels={}
for r in d:
    for q in r['questions']: labels.setdefault(q['label'], q)
miss=[]
for l,q in labels.items():
    m=match_field(l); v=None
    if m:
        k,s=m
        try:
            v = tech_years_answer(bank,l) if k=='years_technology' else (
                located_in_answer(bank,l) if k=='located_in_city' else
                resolve(bank,s,numeric_control=(s.kind==NUMERIC)))
        except Exception: v=None
    if v is None: miss.append(l)
print(f'answerable {len(labels)-len(miss)}/{len(labels)}')
for l in miss: print('  ', l[:90])
"
```

Target: **102 of 104**. The two that remain are *"Why do you want to join our company?"*
(handled by `freetext.py`) and an optional unlabelled input.

### FIELD_MAP rules that are not style preferences

- **Insertion order IS match priority.** Specific before generic, always. `education_*` must
  precede `degree`, whose bare `\bdegree\b` matched "Have you completed the following level of
  education: **Master's** Degree?" and would have answered **"B.Tech"** to a Yes/No — and given
  the *Bachelor's* answer to a *Master's* question.
- **Anchor every pattern to its own subject.** A bare `\blocation\b` once typed "Srinagar" into
  *"Have you appeared for an Interview at any Exl location…"* (D31). A pattern that can match a
  question about something else is as dangerous as inventing a value.
- **Employers typo their own questions.** A live form asked "Are you serv**ibg** your notice
  currently?", and another put an adverb in the middle ("Are you **currently** serving"). Both
  broke exact patterns.
- **`years_*` specs need `requires=QUANTITY_CUE`.** A skill name in a label does not make it a
  quantity question.

### The technology-years table

LinkedIn's standard screener is *"How many years of work experience do you have with `<X>`?"*
where X is unbounded. The bank knew 8 technologies; everything else came back blank, and these
fields are **required**, so **one unmapped technology stalls the entire wizard**.
`experience.technology_years` now holds **97** entries grounded in his CV, resolved dynamically
by `tech_years_answer()`, defaulting to **0**.

A truthful 0 loses only roles he would fail in the technical round. Never round up.

### The one place an LLM writes to a form

`freetext.py`, for motivation prose only. It refuses anything checkable (years, salary,
certifications, passport, CGPA), and every failure mode leaves the field blank.

⚠️ **`FREETEXT_MAX_TOKENS = 4096`, not 1024.** Gemini's hidden thinking pass shares the budget,
and at 1024 the answer came back as a fluent half-sentence ending on a comma. ⚠️ **Never put a
word COUNT in the prompt** — asking for "70 words or fewer" made the model number the words as
it wrote (`who (20) runs (21) production (22)`). Constrain by sentences; cap words in code.

---

## 4. Apply

```bash
py -3 -m apps.autopilot.run apply-all --dry-run --limit 30 --max-per-company 1   # check the plan
py -3 -u -m apps.autopilot.run apply-all --limit 30 --max-per-company 1
```

- **Keep the 40-180s throttle.** It is the ban-safety mechanism, not a slowness bug. ~30
  applications ≈ 75 minutes.
- **`--limit` caps SUBMISSIONS, not rows examined**, so a `--limit 2` run still walks the
  whole plan. Documented behaviour, surprising the first time.
- Always `py -3 **-u**` when redirecting to a log, or Python buffers and the file sits empty
  while you wonder whether the process died.
- The truth is the **ledger**, never the console: `ledger.load()`, filter on `submitted_at`.

---

## 5. Diagnose what did not submit — by hand, with the Playwright MCP

This is the loop the owner asked for: run, see what failed, open one by hand, find the missing
question, fix it, automate it.

⚠️ **The Easy Apply modal is a native `<dialog>` element.** It has an *implicit* ARIA role, so
`page.get_by_role("dialog")` finds it and a CSS `[role="dialog"]` selector returns **nothing**.
Two rounds were lost concluding "LinkedIn changed the DOM" when only the hand-written selector
was wrong.

Known failure modes and what they actually mean:

| Status | Real cause |
|---|---|
| `resume-mismatch` | The résumé step is a **radio list**. Reading the first filename in the text compares against the wrong CV while the right one sits further down, already uploaded. Read the **checked** radio; **select** before uploading; click the **label**, because `check(force=True)` raises *"Element is outside of the viewport"* on a scrolling list. |
| `stalled-validation` | Usually a **typeahead** (e.g. "Location (city)"). `fill()` sets the visible string but never fires the selection, so the form still considers it blank and shows "This field is required" **in red under visible text**. Type per keystroke, then pick a suggestion. |
| `reached-review` | Got to Review but the button did not lead to Submit — normally a required field still empty further up. |
| `external-or-none` | Not Easy Apply. If this is common, discovery used the wrong filter (see §1). |
| `closed` / `removed` | Stale row. See §0. |
| `modal-never-rendered` | The dialog shell appeared but the form never streamed in. Retry later. |

> **A field that displays your value has not necessarily accepted it.** Read the state the form
> keeps — the checked radio, the validation message — not the pixels.

---

## Environment traps that cost real time

- ⚠️ **Never call `navigator.clipboard.readText()` through the Playwright MCP.** It hung the
  server for **74 minutes** with no output and no error.
- **Regexes do not survive a bash heredoc.** `\b` became a literal backspace byte (0x08) inside
  `answers.py`, after which an exact-match `Edit` could not find its own target. Write a `.py`
  file and run it.
- **Truncating your own error message hides the evidence.** `{text[:60]!r}` made a complete
  answer and a truncated one look identical; two debugging rounds went into the error string
  rather than the bug.
- **Another session may be working in this repo.** Stage files by name. `git add -A tools/`
  once swept the content engine's WIP into a commit about form filling.
- Close the LinkedIn MCP session (`close_session`) before an apply run, and discard any modal
  you opened by hand, or you leave a half-filled draft on a real posting.

---

Related: [[05-decisions]] **D45** (stale board, `f_AL`) · **D46** (survey first, the three
"value never landed" bugs) · D31 (anchored patterns) · D42/D43 (token budget, the free model) ·
[[26-apply-at-volume]] · [[30-warm-insider-runbook]] (what to do AFTER a submission)
