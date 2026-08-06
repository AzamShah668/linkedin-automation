# 04 — Roadmap

Back to [[00-INDEX]]. Architecture: [[02-architecture]]. Sources: [[03-data-sources]].
**Live status of each phase: [[07-current-state]].**

> **Reality note (2026-07-25):** the phases below describe the *coded* build. In practice Phases 1–2 are
> already being run **manually via MCP + skills** (LinkedIn MCP discovery → Notion store → cv-architect →
> recruiter-outreach), see [[05-decisions]] D7. The Python code path is deferred; the near-term work is not
> "build Phase 0 code" but "process the 7 remaining jobs already in Notion." Phase markers below annotated ✅/◑.

Estimates assume focused build sessions. Each phase ends with something *usable*.

## Phase 0 — Foundation (Day 1, ~half day)

- `git init` ✅, `.gitignore` ✅, `.env.example` ✅
- Python project (`pyproject.toml` or `requirements.txt`), virtualenv
- `core/`: config loader, Claude client wrapper, logging, throttle helper
- `store/`: DB schema + migrations (SQLite), repositories
- `profile/`: ingest owner's master CV → structured profile (skills, achievements, preferences)
- Run `/graphify` now that code exists (Brain 3 online)
- **Deliverable:** `python -m src.cli status` prints an empty but wired pipeline.

## Phase 1 — Discovery + Store (Days 1–2)  ◑ DONE-via-MCP (code path deferred)

- **Already achieved manually:** LinkedIn MCP `search_jobs` → 10 scored jobs in the **Notion store**
  ("Job Hunt — Autopilot"), ranked by Fit Score, with a Warm-Intro flag. See [[07-current-state]].
- Still-coded version (later): Adapters (Greenhouse/Lever + Adzuna/Remotive + Gmail LinkedIn-alert parser),
  company watchlist, dedupe, `scoring/` module, `.env` threshold, and a scheduled daily run.
- **Deliverable (manual):** ✅ fresh jobs sit in Notion ranked by fit. **Deliverable (coded, pending):**
  `cli discover` refreshes them automatically.

## Phase 2 — Research + Tailor (Days 2–3)  ◑ DONE-via-skills for 3 jobs (7 pending)

- **Already achieved via skills:** `cv-architect` produces tailored CV + Highlight Reel; `recruiter-outreach`
  does per-company research + dual-touch drafts. Done for Infosys/Innova ESI/GoodSpace (see [[07-current-state]]).
- Still-coded version (later): `research/` + `tailor/` modules so it's one CLI command, PDF export automated.
- **Deliverable (manual):** ✅ purpose-built packet per processed job in `output/`. Pending: the other 7 jobs.

## Phase 3 — Outreach + Slack + Tracking (Day 3)

- `outreach/`: draft queue + `gmail_sender` (throttled, capped, approval-gated)
- `notify/`: Slack messages — new match / draft ready / sent / reply / follow-up due
- `track/`: status transitions; log every event
- **Deliverable:** end-to-end run — discover → tailor → Slack review → approve → send → tracked.

## Phase 4 — Follow-up + Dashboard + Learning (Day 4+)

- Follow-up cadence (Day 3 + Day 7 nudges if no reply)
- FastAPI review dashboard (approve/edit/reject in browser)
- Analytics: response rate by source / template / timing; A/B message variants
- **Deliverable:** a self-improving loop that shows what's actually landing interviews.

## Speed tactics — "interview in days" (the ideas, baked into the design)

1. **Freshness wins.** Prioritize roles posted <48h; apply within hours — be in the first wave the
   recruiter reads.
2. **Dual-touch.** Formal application **plus** a direct, personalized email to the recruiter/hiring
   manager leading with the Highlight Reel.
3. **Proof-of-effort.** Every message references a specific, researched detail about the company —
   the single strongest anti-spam signal and reply-rate booster.
4. **Front-load quantified wins.** Numbers first ("cut X by Y%"), matched to the job's stated needs.
5. **Target fast movers.** ATS-public startups/scaleups (Tier 1) tend to reply and interview faster
   than big corporates.
6. **Smart follow-up.** Automated, polite nudges on Day 3 and Day 7 measurably lift responses.
7. **Volume with quality.** 5–10 *excellent* tailored applications/day beats 200 spam messages — and
   keeps the accounts safe.
8. **Measure and double down.** Track response rate; pour effort into the sources/messages that convert.
