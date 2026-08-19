# 07 — Current state

> **A SNAPSHOT, NOT A LOG. Hard cap: 150 lines.**
> Read this second each session, after [[00-INDEX]]. It answers *"what is true right now"* and
> nothing else. History lives in [[36-state-archive]] (3,308 lines) and [[34-changelog]].
>
> **When you add to this file, replace — do not append.** It previously grew to 2,566 lines by
> accumulating scheduled-agent run notes, at which point "read it each session" became impossible
> and got skipped. Run notes go to [[36-state-archive]]; decisions go to [[05-decisions]].
>
> 🔴 **NOTHING MAY EXIST ONLY HERE.** This file is a convenience copy of things recorded elsewhere.
> Before writing a line, ask: *does this expire?*
> **Perishable** (counts, queue depths, what is due) → fine here, it is the point.
> **Permanent** (a trap, a decision, a procedure, an instruction) → write it to
> [[05-decisions]], the relevant runbook, or `~/.claude/projects/*/memory/` **first**, and only then
> mention it here.
>
> Why this line exists: rewriting a snapshot means *judging* what is still current, and a wrong
> judgement does not delete a fact — it buries it in a 3,325-line archive nobody reads, which is
> indistinguishable from losing it. The archive protects the bytes; **this rule protects the
> knowledge.** Checked 2026-08-17: all five permanent items below also live in an uncapped store.

*Last replaced: 2026-08-19 (pipeline repair + OmniRoute switchover)*

## The one-line version

Two parallel pipelines both work. 41 applications are out, 28 reached a named human, 1 warm reply
ever received — still unanswered by the owner after 23 days. **9 of the 41 now have an employer
verdict and all 9 are rejections**; 8 of those landed in one morning and were found only because
this run swept `jobs-noreply@linkedin.com`, a channel no `contact.md` can ever list.

## What runs

| Entry point | Stack | Schedule |
|---|---|---|
| `pipeline.cmd` → `tools/run-pipeline.ps1` | **Claude** — 6 steps wake a headless `claude.exe` | ⛔ **task DISABLED 2026-08-19** (D55). Script and branch untouched; re-enable in one click |
| `pipeline-free.cmd` → `tools/run-pipeline-free.ps1` | **OmniRoute** — no Claude anywhere | ✅ **SCHEDULED daily 10:30** (D55). Starts the gateway itself; falls back to Groq if it will not start |

Both take the same lock (`tools/pipeline-lock.ps1`), so they cannot collide over the single Chromium
profile. Proven live 2026-08-17 10:25. Five per-step scheduled tasks also exist and run
independently — **and on 08-18/19 that starved the pipeline of every step for two days**: the
standalone Reply Check won the lock in the same second the pipeline started and held it ~13 min,
and each pipeline step then stood down and reported exit 0. `run-pipeline.ps1` now exports
`PIPELINE_LOCK_WAIT_SECONDS=1200` so its children **wait** instead. That answers the gating
question in [[35-knowledge-system-audit]] §8; the reasoning is [[05-decisions]] **D54**.

Order in both: `accepts → dm/flush → replies → gmail → nudge → discovery → apply → outreach → cv`.
**Sends first**, because only those steps have a deadline.

## Numbers, 2026-08-19

| | |
|---|---|
| Applications submitted | **51** across ~45 companies (**10 on 08-19**, after two days of zero) |
| …that reached a named human | **28** |
| …that reached **nobody** | **9** (6 are from the 08-17 00:08 batch, awaiting outreach) |
| Invites: pending / accepted / pitched / failed | **11 / 0 / 4 / 2** — re-checked **08-19 16:00 via MCP, 0 new accepts**; all 11 read `· 3rd` *and* `Pending` (two signals, both agreeing). The 1 accept became the held TCS row, now `failed`. Rest of this table is 08-17 |
| Real replies, ever | **1** — a warm insider, on the first try |
| Employer outcomes, ever | **9, all rejections** — Zetheta 08-17, then **8 on 08-18** (Talentgigs, slice, CloudLeap, TCS *Cloud Eng walk-in*, ShimentoX, Discovr AI, Armakuni, CDOps Tech), all from the 08-15 batch, 3 days after submit. Hyper Lychee Labs *viewed* 08-18 and is still live |
| Tests | **419** |
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
2. **Talent500 assessment — ⏱️ THE DEADLINE PASSED 2026-08-18 03:42 IST, UNACTIONED.**
   *Software Engineer, Data and AI Platform* (ANSR → Under Armour India). The 24h countdown from
   the 08-16 22:12Z mail has now expired. The 21st reply check (08-18) confirms **no further
   application mail arrived after it** — the only later Talent500 send is a marketing webinar blast
   — and **all Talent500 application mails are still unread**. The 08-17 OTP stays *consistent with*
   a start and was never evidence of completion. Treat the application as **lost unless the owner
   reopens it**; only he can test whether the link still works. Nothing here is automatable.

## 🟡 Open, automatable

3. **Himaja Madala (TCS) — pitch HELD 08-19, owner's call.** Came due 09:47 and was **not sent**:
   its opening line pitches the *Cloud Engineer walk-in* req that LinkedIn **rejected 08-18 09:20Z**,
   2h20m before she accepted. She is also `#OpenToWork` and leaving TCS. Tracker row is `failed`
   (= held; the reason string says so). Either regenerate via `pitch.py` or drop her. See
   [[13-accept-watch-runbook]] §Guardrails for the general trap.
4. **9 applications reached nobody.** `apps/autopilot/outreach.py` works these; it runs after
   `apply` each cycle. Watch the ratio — applying is outrunning contacting (D32's shape).
5. **Decide whether to schedule the free stack.** Built, tested, 9/9 green unattended.
6. **3 invites expire 2026-08-20** (sent 08-06, 14-day rule): Mayank Bhargava / SkillsCapital,
   Divya Reddy / Mirai Alpha, Shubham Bodkhe / Hired. The next `expire` run after that date
   flips them and the runbook's fallback is email, not more LinkedIn poking.
7. 🔴 **The 8 rejections are in Notion but nowhere else.** The 22nd reply check had no shell
   approval, so `tools/slack_notify.py` **never posted** (the owner has not been pinged) and
   **`database/board.sqlite3` still shows all 8 as live** — a board-driven step can still work a
   dead row. Both are one command each; see [[36-state-archive]] 2026-08-19.
8. **Add `from:jobs-noreply@linkedin.com` to the reply-check sweep permanently.** Twenty-one prior
   checks could not see the Easy Apply outcome channel because the runbook builds its `from:` list
   from `contact.md`, which by construction only lists humans we emailed. See [[11-reply-classifier-runbook]].

## Traps that are still live

- **`f_AL=true` is the Easy Apply filter**, not `f_EA`, which LinkedIn silently ignores (D45).
- **`tools/board_db.py` and `tools/serve_dashboard.py` are SHIMS**, not dead files — 16 callers,
  three of them scheduled PowerShell. They must load the real module **by file path**.
- **A pitch must exist before an accept lands.** `watch-accepts` sends the exact `touch-2-linkedin.md`
  and cannot invent one; `berribot`'s is deliberately renamed `.WITHHELD.md` (D50).
- **`output/` and `profile/` are gitignored** because they hold real third-party names. Never commit
  a real person's name, email or LinkedIn URL to this public repo.
- **Never reply to Showkat** (owner's instruction).
- **A LinkedIn rejection never says "rejected".** Subject *"Your application to X at Y"* (not
  *"was sent to"*) is a status update; the verdict lives in the template key
  `email_jobs_application_rejected_01`, and `PLAIN_TEXT` returns footer-only. Zetheta's body then
  pitched an unpaid "internship programme" — status from the key, intent from the body, never one
  alone. Memory: `rejection-can-hide-in-a-tracking-token`.

## Read next

[[35-knowledge-system-audit]] before adding to any knowledge store ·
[[32-the-complete-loop]] for the pipeline · [[33-omniroute-stack]] for the free stack ·
[[31-apply-batch-runbook]] before "find jobs and apply" · [[05-decisions]] for why anything is
the way it is · [[36-state-archive]] for how it got here.
