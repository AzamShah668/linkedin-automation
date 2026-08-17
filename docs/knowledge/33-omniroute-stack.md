# 33 — The OmniRoute stack (built beside the Claude one, not instead of it)

> **Read this before touching anything under `apps/autopilot/free/`.**
> Branch: **`rewrite/omniroute-native`**. The Claude stack lives on `rewrite/phase-0` and both
> branches are pushed. Started 2026-08-16.

---

## The constraint that shapes everything

Azam's instruction, verbatim:

> *"I don't want you to replace all this. I just want you to build it … the previous one with the
> cloud agents should be there. It should not get deleted or anything else. We are just building
> this separately now."*

So this is **additive**. Two stacks, both runnable, neither disturbing the other:

```
pipeline.cmd       -> tools/run-pipeline.ps1        Claude stack     UNCHANGED, still scheduled
pipeline-free.cmd  -> tools/run-pipeline-free.ps1   OmniRoute stack  NEW, opt-in, unscheduled
```

**Nothing existing is deleted.** `auto-apply.ps1`, `build-packet.ps1`, `sweep-packets.ps1`,
`apps/autopilot/cv.py` all stay exactly as they are. If the free stack disappoints, the Claude one
is still there and still works.

---

## Why bother

Six pipeline steps are not programs, they are **Claude Code agent sessions** — a headless
`claude.exe` reading a Markdown runbook and making ~20 MCP calls. That single choice is behind most
of this project's outages: **D24** (fails three process layers deep), **D25** (the usage wall), and
the sweeper that reported exit 1 for weeks because it never parsed. [[22-rewrite-architecture]]
(D26) set out to remove exactly this.

**Thirteen modules already need no Claude at all** — `fill` · `answers` · `families` · `ledger` ·
`sourcing` · `coverage` · `intake` · `replies` · `nudge` · `outreach` · `connect` · `accepts` ·
`pitch`. They are **shared by both stacks**. So this is *finishing* the D26 rewrite, not starting a
new one, and two of the six agent runners (`flush-approved`, `auto-apply`) are already dead weight
superseded by `connect.py` (D48) and `fill.py`.

---

## What was verified before any code was written

| Check | Result |
|---|---|
| Gateway live on `:20128` | ✅ catalog served |
| Free model exact-echo | ✅ `PIPELINE ALPHA BRAVO 12345` verbatim, **6.3s** |
| Free model long-form | ✅ 519 chars in **8.6s** |
| Quality of that long-form | ⚠️ *"Results-driven … extensive expertise in architecting resilient…"* |
| `llm.py` loads `.env` | 🔴 **No. Nothing does.** |

### 🔴 The bug that blocked everything

`llm.py` reads `os.getenv` and **nothing in the project ever loaded `.env`** — `python-dotenv` is
not even installed. It only ever worked in shells where the vars happened to be exported by hand.
Under Task Scheduler it raises `LLM_BASE_URL is not set`, which means **`freetext.py` — the one
place an LLM already writes to a real employer's form — was dead in every unattended run.**

`apps/autopilot/env.py` fixes it for both stacks. It is the **only shared file this work touches**.

### ⚠️ The quality problem, stated honestly

The free model produced two banned AI-tells *unprompted* in a single test paragraph. That is the
whole risk of moving the CV, and it is why `free/cv_validate.py` exists: **nothing ships unless it
passes**. The validators guarantee a **floor** (no lies, no tells), not Claude's ceiling. Because
the Claude builder still exists, the same packet can be built both ways and compared.

---

## Model configuration

```
LLM_MODEL        fast tier   — routing, classification, short text
LLM_CV_MODEL     heavy tier  — the CV and cover letter
LLM_FALLBACK_*   Groq direct — a genuinely different road (D43)
```

**OmniRoute rotates the keys itself.** That is what the gateway is for and what Azam asked for.

⚠️ **Never pin `auto/*`.** That swaps the *model* per call, not the key, and D43 records different
providers giving different correctness. Keys rotate under a **fixed** model.

⚠️ **Keep the Groq-direct fallback.** OmniRoute is a **local process** — when it dies, every model
it lists dies with it, so an OmniRoute "fallback" is not a fallback at all.

⚠️ **Certify, never trust the catalog.** It listed **1019 models and three answered** (D43), and
`testStatus: "active"` answers the wrong question — `groq` and `opencode` both reported active while
403-ing every completion. `tools/omniroute_canary.py --certify` echo-tests each tier.

---

## Layout

| Module | Free-stack replacement for | Model needed? |
|---|---|---|
| `free/discover.py` | `daily-discovery.ps1` | **no** — `f_AL=true` Playwright scrape → `intake.py` |
| `free/dm.py` | the send half of `watch-accepts.ps1` | **no** — text comes from `pitch.py` |
| `free/gmail.py` | the Gmail half of `check-replies.ps1` | yes, classification only |
| `free/cv.py` + `free/cv_validate.py` | `build-packet.ps1` / `sweep-packets.ps1` | yes, heavy tier |

`dm.py` reuses `connect.py`'s hard-won browser lessons: `_click_through_sticky_nav` (the sticky nav
eats clicks and `force=True` does not help) and read-back verification (the Pending badge has no
accessible name).

Both stacks reuse `pipeline-lock.ps1` and `Release-BrowserProfile`, so they **cannot collide over
the single Chromium profile** even if both are triggered at once.

---

## How we will know it worked

| Check | Pass |
|---|---|
| `git diff rewrite/phase-0 -- tools/run-pipeline.ps1 apps/autopilot/cv.py` | **empty** |
| `pipeline.cmd -WhatIf` | old stack still lists 8/8 |
| scrubbed-env subprocess calls `llm.ask` | answers |
| `omniroute_canary.py --certify` | exact echo per tier |
| validator fed *"Results-driven… leveraged synergies"* | **rejects** |
| validator fed the real Energy Exemplar packet | accepts |
| `pipeline-free.cmd` full run | 8/8, `claude.exe` never launched |
| `py -3 -m pytest -q` | **251 passing stay green** |

---

Related: [[05-decisions]] **D50** (one source is not enough for an irreversible action) · D48
(the approval gate removed) · D47 · D43 (the fallback must be a different road) · D42 · D26-D28 ·
[[29-omniroute-gateway]] · [[32-the-complete-loop]] · [[22-rewrite-architecture]]

---

## 8. BUILT — 2026-08-16/17. What exists and what was measured

| Module | Replaces | Verified live |
|---|---|---|
| `env.py` | nothing (new) | a subprocess with every `LLM_*` var stripped answers |
| `free/discover.py` | `daily-discovery.ps1` | **64 postings, 63 Easy Apply**, → `intake.py` → **36 rows on the board** |
| `free/cv.py` + `cv_validate.py` | `build-packet.ps1` | **PASS in 2 attempts**; attempt 1 correctly rejected for a fabricated `140,000` |
| `free/dm.py` | send half of `watch-accepts.ps1` | 2b extraction verified on the real pitch; the **withheld** one stays unreachable |
| `free/gmail.py` | Gmail half of `check-replies.ps1` | reports `needs-setup` and the pipeline carries on |
| `run-pipeline-free.ps1` | `run-pipeline.ps1` (as a *second* entry point) | accepts / gmail / nudge / discovery / intake / outreach all run |

**349 tests.** The Claude stack is provably untouched: `git diff rewrite/phase-0` against
`run-pipeline.ps1`, `cv.py` and all six agent runners is **empty**, and no `free/` module mentions
`claude.exe`.

### Config, certified

```
LLM_MODEL      gemini/gemini-3.5-flash-lite   fast tier
LLM_CV_MODEL   gemini/gemini-3.6-flash        heavy tier (the CV)
LLM_FALLBACK   groq llama-3.3-70b-versatile   direct, not through the gateway
```

All three pass an exact multi-token echo in both transports (`omniroute_canary.py --certify`).

---

## 9. ⚠️ Five findings that cost real time

### The budget floor: silent truncation
Asked to echo four exact strings through the gateway:

| `max_tokens` | exact |
|---|---|
| 128 | **0/4** — `ALPHA 12345 OMEGA` → `ALPHA 12` |
| 512 | 4/4 |

HTTP 200, well-formed, plausible, cut off at the **end**. The hidden thinking pass spends the same
budget. `llm.ask()` now **raises** any budget below `MIN_SAFE_MAX_TOKENS`; free tokens are cheaper
than a truncated answer.

### The fallback must fit in the fallback
The CV prompt carried 24,000 chars of dossier. Groq's free tier refused it: **413, 14,463 tokens
against a 12,000 limit**. *A prompt only the primary can accept makes the fallback useless exactly
when the gateway is down.* Capped at 12,000 chars.

### The virtualised pane, not the window
The first live scrape returned **7 postings** — the exact number runbook 31 cites as the
virtualisation symptom. The results list lives in **its own scrollable pane**; scrolling the window
moves nothing. Scrolling the pane structurally, *until the link count stops growing*, took it to 40.
A fixed number of scrolls is a guess; "until it stops producing rows" is the finishing condition.

### The duplicated title is not always identical
LinkedIn emits the title twice, and the copies differ: `Lead Java Developer` then
`Lead Java Developer with verification`. Exact-match dedup left the second in place **and it became
the company name**. Prefix matching now collapses them, keeping the shorter form.

### 🔴 A missing UTF-8 guard loaded zero of 36 rows
`intake.py` had no console guard. An en-dash in a job title raised `UnicodeEncodeError` **while
printing the plan** — before the insert — so discovery found 36 rows and none landed. The only
symptom was a quiet `exit 1`, inside a step the runner had been told was "informational".

Writing the regression test found **six more** modules with the same hole, including `run.py`, the
apply runner. They survive only because the PowerShell runners call `chcp 65001` first.
`tests/test_console_encoding.py` now requires the guard in every module with a `__main__`.

> Two mistakes compounded there: a missing guard, and a step whose failures I had told the runner to
> ignore. **"Informational" must mean "this failing is genuinely fine", not "this fails a lot".**

---

## 10. Still needs a human, once

**Gmail OAuth.** Google Cloud project → enable Gmail API → OAuth client (Desktop app) → save at
`~/.credentials/gmail-client.json` → `py -3 -m apps.autopilot.free.gmail --authorize`. Scope is
`gmail.readonly`: it cannot send or delete. Until then the step says `needs-setup` and the pipeline
continues, because LinkedIn is the channel that has ever produced a reply.

**Nothing is scheduled.** `pipeline-free.cmd` runs by hand until you decide otherwise. The Claude
stack keeps its 10:30 task.

---

## 11. First full unattended run — 2026-08-17 00:08 → 00:35 (27 minutes)

**9 of 9 steps, and `claude.exe` was never launched.** The only occurrence of the word "claude" in
the entire log is the runner's own banner line.

| Step | Time | Result |
|---|---|---|
| accepts | 133s | 12 invites checked against LinkedIn; 0 accepted |
| dm | 0s | nothing due |
| replies (LinkedIn) | 11s | 6 conversations scanned, 2 flagged as waiting |
| gmail | 1s | `needs-setup`, pipeline continued |
| nudge | 0s | nothing newly due |
| discovery | 65s | fresh `f_AL=true` scrape |
| intake | 0s | scored and loaded |
| **apply** | **20 min** | **6 SUBMITTED (confirmed)**, 20 not submitted of 41 walked |
| outreach | 150s | 4 companies researched, **0 sent** |

Submitted: Zetheta Algorithms · Data Eminence · QuietSpark · HCLTech · ColigoMed · GC Technologies.
All six are in the ledger, all `linkedin-easy-apply`, all with a family CV.

### Outreach sent nothing, and that was correct
All four companies came back **"none confirmed"** — no candidate could be shown to work there, so
every one was escalated rather than contacted. The run was also at 00:30, outside the 09:00-21:00
window, so the send guard would have held them anyway.

⚠️ **Four out of four is a high escalation rate** and worth watching. Earlier runs found real
recruiters at Talentgigs, Hyper Lychee Labs, slice, IndiGo and Synthires, so the search is not
broken; these four are small firms with little LinkedIn presence. **Do not loosen the person
filter to reduce this number** — loosening exactly that is what produced the Berribot invite
(D50). If it needs improving, widen the *query*, never the *acceptance criteria*.

### Verified after the run
- `git diff rewrite/phase-0` for `run-pipeline.ps1`, `cv.py` and all six agent runners: **empty**
- `pipeline.cmd -WhatIf`: still lists **8/8** Claude steps
- **349 tests** green · 12 PowerShell scripts parse · **16/16** CLI modules start

---

## 12. Second day, 2026-08-17 — the two bugs the first run could not have found

The 00:08 run exercised nine of ten steps. The tenth, `free/dm.py`, had nothing due, so it ran
green while never opening a message composer. **A step with no work is not a tested step**, and
when a real accept finally landed both of its remaining defects surfaced inside twenty minutes.

### 12a. `free/dm.py` — "not connected" for someone who had accepted

SHALE FRANCIS accepted at 2026-08-16 19:49; his pitch was due 09:12. The step reported
`not-connected: no Message button`. The tracker said otherwise, so the page was dumped rather than
believed — and the Message control turned out to be an `<a>`, never a `<button>`. Full reasoning in
**D52**; the short version is that the selector could not have matched on any profile ever, and the
failure presented as a calm, plausible sentence.

The repair is *narrower*, not wider: an exact accessible name of `Message`, plus agreement on the
`recipient` URN across every matching control, because the sidebar offers one `Message <Name>` link
per suggested profile and a loosened regex messages a stranger.

Also hardened in the same pass: `mark_sent()` was silent on a non-zero exit — the path that means
**the pitch was delivered and not recorded**, so the next run sends it again.

### 12b. `free/gmail.py` — the setup asked for work that was already done

`--authorize` said *"no OAuth client JSON"* and pointed at the Google Cloud console. Five
Desktop-app clients were already in `~/Downloads`. Worse, the Gmail API is enabled **per Google
Cloud project**, so any of them would have consented cleanly and then 403'd every call, leaving a
token on disk and a channel that reports zero replies forever. `--authorize` now ends with a real
`getProfile` call and deletes the token if it fails. **D53.**

### 12c. What the lock proved, for free

At 10:25 the free stack asked for the pipeline lock while the Claude stack's Reply Check held it
(pid 12928, taken 10:24:24) and stood down with a plain sentence. The two stacks **cannot** collide
over the single Chromium profile, and that was observed rather than argued.

### 12d. Standing numbers, 2026-08-17 10:24

From `coverage.py` inside the scheduled reply check:

| | |
|---|---|
| applications | **41** across 37 companies |
| reached a named human | **28** |
| reached **nobody** | **9** |

Six of those nine are last night's free-stack submissions, which is expected — `outreach.py` runs
after `apply` and works a limited batch per cycle. It is worth watching rather than fixing: if the
"reached nobody" column grows faster than outreach clears it, the apply step is outrunning the half
of the pipeline that turns an application into a conversation, which is exactly the imbalance
**D32** was about.

**397 tests.**
