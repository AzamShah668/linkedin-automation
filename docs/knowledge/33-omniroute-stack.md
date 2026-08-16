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
