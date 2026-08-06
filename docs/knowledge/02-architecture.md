# 02 — Architecture

Back to [[00-INDEX]]. Data sources detailed in [[03-data-sources]]. Build order in [[04-roadmap]].
**What actually runs today (vs this target design): [[07-current-state]].**

> **Planned vs actual (2026-07-25):** everything below is the *target coded system*. Today the pipeline runs
> **MCP-first** — LinkedIn MCP does discovery, a **Notion database is the store** (not the SQLite model
> below), and the `cv-architect` / `recruiter-outreach` skills do tailoring + outreach. The `src/` modules
> and SQLite schema here are the eventual automation, not what exists now. See [[05-decisions]] D7.

## The pipeline

```
Discover → Store → Prioritize → Research → Tailor → Draft → [HUMAN APPROVES] → Send → Track → Follow-up
   │         │         │           │         │        │            │              │       │        │
 sources   sqlite   fit score   Claude    Claude   queue      Slack review     Gmail   status  scheduler
```

Everything up to "Send" is automated. **Send is gated by human approval** via a Slack review queue.

## Module map (target)

```
job-hunt-autopilot/
├── src/
│   ├── core/         # config (.env), Claude client, logging, throttling/rate-limit helpers
│   ├── discovery/    # one adapter per source: greenhouse, lever, ashby, workable,
│   │                 #   adzuna, remotive, arbeitnow, gmail_alerts (LinkedIn), rss
│   ├── store/        # SQLModel/SQLite models + repositories (dedupe on source+source_id)
│   ├── scoring/      # fit score: job description vs owner profile (rules + Claude)
│   ├── research/     # company briefs via Claude (careers page, public info, news)
│   ├── tailor/       # cv_builder, cover_letter, highlight_reel generators → Markdown → PDF
│   ├── outreach/     # draft queue, gmail_sender, linkedin_manual_helper (copy-ready text)
│   ├── notify/       # slack notifications (new match / draft ready / sent / reply / follow-up)
│   ├── track/        # application status transitions + follow-up scheduler
│   ├── profile/      # owner's master CV + structured profile (skills, achievements, prefs)
│   └── cli/          # commands: discover, score, research, tailor, queue, review, send, status
├── data/             # sqlite db + generated PDFs (gitignored)
├── docs/knowledge/   # Brain 2 (this)
├── tests/
├── .env.example
└── CLAUDE.md
```

Later: `web/` FastAPI dashboard for the review queue (approve/edit/reject in a browser).

## Data model (SQLite → Postgres)

- **companies** — id, name, domain, ats_type, careers_url, description, research_json, created_at
- **jobs** — id, company_id, source, source_id (UNIQUE with source), title, location, remote,
  url, description, posted_at, fit_score, status, discovered_at
  - status: `new → researching → tailored → queued → applied → replied → interview → rejected/closed`
- **contacts** — id, company_id, name, role, email, linkedin_url, source, confidence
- **applications** — id, job_id, cv_path, cover_letter_path, highlight_reel_text, channel, sent_at, status
- **outreach_queue** — id, job_id, contact_id, channel, draft_subject, draft_body, attachments,
  status (`draft → approved → sent/failed/skipped`), approved_at, sent_at
- **events** — id, entity_type, entity_id, type, payload, created_at (audit trail + Slack feed source)
- **followups** — id, application_id, due_at, template, status

## Outreach: the dual-touch engine (`recruiter-outreach` skill)

Built 2026-07-25 as `.claude/skills/recruiter-outreach/` (skill-based, mirroring `cv-architect`). Per target
job it finds the recruiter, then drafts **two complementary messages** and stages them for approval:

- **Touch 1 — formal email** (Gmail): role-specific subject, one matched metric + 3 proof bullets, tailored
  CV attached, one ask. Grounded in `output/cv/achievement-bank.md`.
- **Touch 2 — personal LinkedIn message** (connect note ≤300 chars, or DM if 1st-degree): leads with the
  strongest quantified win from `output/outreach/highlight-reel.md` + **one researched company detail**
  (the anti-spam signal). Warm/alumni path preferred over cold.

Recruiter discovery ladder (ban-safe): posting/ATS email → LinkedIn MCP *read-only* lookup (no auto-connect,
no auto-DM) → inferred+verified company email → role inbox. LinkedIn MCP is used to **find + draft**, never
to send. Outputs land in `output/outreach/<slug>/` and `output/outreach/REVIEW-QUEUE.md`; nothing sends
without human approval. Throttle/caps in `.env` (`DAILY_OUTREACH_CAP`, `MIN_SECONDS_BETWEEN_SENDS`,
`OUTREACH_JITTER_SECONDS`, `LINKEDIN_CONNECTS_DAILY_CAP`). Follow-up cadence: Day 3 + Day 7, then stop.

## The human-in-the-loop review queue (the safety + quality gate)

1. AI generates the tailored CV, cover letter, highlight reel, and outreach draft.
2. It lands in `outreach_queue` as `draft`; Slack posts a summary + link.
3. Owner approves / edits / rejects.
4. Approved → `gmail_sender` sends (throttled, capped) → status `sent`, event logged, Slack confirms.

## Safeguards (baked in, not optional)

- Daily outreach cap + minimum delay between sends (config in `.env`).
- Randomized jitter on all timed actions.
- No headless LinkedIn scraping — ever. LinkedIn signal comes only from parsed email alerts + manual capture.
- Every generated document is grounded in the owner's real profile — no fabrication.
- All external input validated before it hits the DB.
