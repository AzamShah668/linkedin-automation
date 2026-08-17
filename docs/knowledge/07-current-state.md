# 07 — Current state

> **A SNAPSHOT, NOT A LOG. Hard cap: 150 lines.**
> Read this second each session, after [[00-INDEX]]. It answers *"what is true right now"* and
> nothing else. History lives in [[36-state-archive]] (3,308 lines) and [[34-changelog]].
>
> **When you add to this file, replace — do not append.** It previously grew to 2,566 lines by
> accumulating scheduled-agent run notes, at which point "read it each session" became impossible
> and got skipped. Run notes go to [[36-state-archive]]; decisions go to [[05-decisions]].

*Last replaced: 2026-08-17 22:30 IST*

## The one-line version

Two parallel pipelines both work. 41 applications are out, 28 reached a named human, 1 warm reply
ever received — and that reply is still unanswered by the owner after 22 days.

## What runs

| Entry point | Stack | Schedule |
|---|---|---|
| `pipeline.cmd` → `tools/run-pipeline.ps1` | **Claude** — 6 steps wake a headless `claude.exe` | **daily 10:30** + catch-up on resume |
| `pipeline-free.cmd` → `tools/run-pipeline-free.ps1` | **OmniRoute** — no Claude anywhere | **unscheduled, by hand** (owner's call pending) |

Both take the same lock (`tools/pipeline-lock.ps1`), so they cannot collide over the single Chromium
profile. Proven live 2026-08-17 10:25. Five per-step scheduled tasks also exist and run
independently — see [[35-knowledge-system-audit]] §8 for the gating question.

Order in both: `accepts → dm/flush → replies → gmail → nudge → discovery → apply → outreach → cv`.
**Sends first**, because only those steps have a deadline.

## Numbers, 2026-08-17

| | |
|---|---|
| Applications submitted | **41** across 37 companies |
| …that reached a named human | **28** |
| …that reached **nobody** | **9** (6 are from the 08-17 00:08 batch, awaiting outreach) |
| Invites: pending / pitched / failed | **12 / 4 / 1** |
| Real replies, ever | **1** — a warm insider, on the first try |
| Tests | **405** |
| Branch | `rewrite/omniroute-native` (Claude stack lives on `rewrite/phase-0`, byte-identical) |

## Where data actually lives

- **The board is `database/board.sqlite3`.** Gitignored — the `notes` column holds real recruiter
  names and this repo is public. **`NOTION_TOKEN` is not set**, so nothing pushes to Notion and
  `sync-board` is the only inbound path.
- **The send record is `output/apply-log/submitted.jsonl`** — append-only, fsync'd. Never infer sends
  from board status; the board has been both stale and wrong.
- **Invites: `output/outreach/pending-invites.json`**, via `tools/invite_tracker.py`.
- **Packets: `output/outreach/<company>--<role>/`** — outreach per company, CV per role.

## Channels being read

| Channel | By what | Status |
|---|---|---|
| LinkedIn inbox | `apps/autopilot/replies.py` (plain Playwright) | ✅ needs no credentials |
| Gmail | `apps/autopilot/free/gmail.py` | ✅ **live since 2026-08-17 10:48**, `gmail.readonly`, GCP project `569148103391` (shared with `Desktop\my assistant`) |
| LinkedIn accepts | `apps/autopilot/accepts.py` | ✅ asks LinkedIn, not the tracker |

Gmail filters bulk on `List-Unsubscribe`, prints what it filtered, and never conflates
"needs-setup" with "no replies". Live: 3 worth a look, 12 bulk, 25 auto-ack.

## 🔴 Open, owner-only

1. **Answer Recruiter-A.** He replied 2026-07-26 with his personal number asking for the CV.
   **22 days unanswered.** The project's only reply, at the company holding the board's best
   unworked row. WhatsApp is deliberately not automated.
2. **Talent500 assessment** — *Software Engineer, Data and AI Platform*. Link expires ~03:42 on
   08-18. A verification code arrived 15:15 on 08-17, which is **consistent with it being started
   but is not evidence of that** — the 20th reply check found that OTP sitting inside a cluster of
   unrelated sync-tooling signups the same morning (Ideogram, Autosync, Obsidian ×2, Dropbox +
   `remotely-save`), where an account OTP is unremarkable. **All five Talent500 mails are still
   unread** and no channel we can read shows the questionnaire's state. Treat as NOT done.

## 🟡 Open, automatable

3. **9 applications reached nobody.** `apps/autopilot/outreach.py` works these; it runs after
   `apply` each cycle. Watch the ratio — applying is outrunning contacting (D32's shape).
4. **Decide whether to schedule the free stack.** Built, tested, 9/9 green unattended.

## Traps that are still live

- **`f_AL=true` is the Easy Apply filter**, not `f_EA`, which LinkedIn silently ignores (D45).
- **`tools/board_db.py` and `tools/serve_dashboard.py` are SHIMS**, not dead files — 16 callers,
  three of them scheduled PowerShell. They must load the real module **by file path**.
- **A pitch must exist before an accept lands.** `watch-accepts` sends the exact `touch-2-linkedin.md`
  and cannot invent one; `berribot`'s is deliberately renamed `.WITHHELD.md` (D50).
- **`output/` and `profile/` are gitignored** because they hold real third-party names. Never commit
  a real person's name, email or LinkedIn URL to this public repo.
- **Never reply to Showkat** (owner's instruction).

## Read next

[[35-knowledge-system-audit]] before adding to any knowledge store ·
[[32-the-complete-loop]] for the pipeline · [[33-omniroute-stack]] for the free stack ·
[[31-apply-batch-runbook]] before "find jobs and apply" · [[05-decisions]] for why anything is
the way it is · [[36-state-archive]] for how it got here.
