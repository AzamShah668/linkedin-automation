# Knowledge Base — Job Hunt Autopilot (Brain 2)

Map-of-content for the *why* behind this project. Read this file first each session, then open the
relevant topic file. Cross-link with `[[file]]`. Keep it distilled — skip cosmetic changes.

## Retrieval protocol (token-saving)

1. This INDEX + **[[07-current-state]]** (what actually exists right now) — read these two first, every session
2. Then **[[22-rewrite-architecture]]** — where the project is going, and why the code looks the way it does
3. Then the one relevant topic file below (~500 tokens each)
4. `graphify query "<task>" --budget 2000` for code structure
5. Raw source files only if the above don't fully answer it

> **New here (human or AI)?** Start at the repo root `README.md`, then read this INDEX →
> [[07-current-state]] → [[22-rewrite-architecture]]. That is the whole orientation, in ~15 minutes.

## Contents

- [[07-current-state]] — **⭐ live snapshot: what's really built, the Notion job store, per-job status.** Read 2nd.
- [[22-rewrite-architecture]] — **⭐ the plan as of 2026-08-06: agent-as-tool, not agent-as-runtime.** Read 3rd.
- [[23-phase-0-results]] — **the rewrite's first real run.** Playwright + a dict filled forms ~16.7s each with zero invented values, but the tool printed PASS while 3 of 5 jobs did nothing. Draft persistence confirmed; ~63% of the board found dead.
- [[24-cv-bridge]] — **Claude Code as a subprocess.** The tailored CV is now attached and its filename verified before anything proceeds. Includes the day's third instance of D30: a usage-limit string outranked a finished PDF on disk.
  Why an IDE was the wrong runtime, the free-model / Claude-Code split, the target module layout, phases 0-5.
- [[01-vision-and-goals]] — what we're building, the owner's 6 steps, success metrics, non-goals
- [[02-architecture]] — modules, data model, tech stack, the human-in-the-loop review queue
- [[03-data-sources]] — the legitimate, ban-safe places we get jobs + recruiter contacts
- [[04-roadmap]] — phased plan (day-by-day to the first interview) + speed tactics
- [[05-decisions]] — key decisions and the reasoning behind them
- [[06-feature-backlog]] — confirmed feature additions (build after the setup phase)
- [[08-completion-plan]] — **the plan to finish the pipeline** (Path A, sequenced gaps, definition of done)
- [[09-discovery-runbook]] — the exact daily discovery recipe the scheduled robot follows (LinkedIn→Notion→Slack)
- [[11-reply-classifier-runbook]] — the reply-checker recipe: Gmail→classify→Notion+Slack alert (inbound)
- [[12-approved-send-runbook]] — **stage 1:** approve on the phone, a bare connection request goes out when the laptop wakes
- [[13-accept-watch-runbook]] — **stage 2:** detect the accept, wait a believable few hours, then auto-send the CV + pitch
- [[15-build-packet-runbook]] — **one board row → a ready packet**: the recipe the dashboard's Build button runs (CV + contact + messages, sends nothing)
- [[14-send-board-dashboard]] — the owner-facing **live** dashboard: how it reads Notion, the two-names connector trap, the four stages
- [[16-gui-automation-investigation]] — **⚠️ read before touching the screen-control agent.** Why free models score 0/8 on GUI tasks, why UIA grounding fixes it, the answer bank rule, and the CLI-cannot-reach-API blocker
- [[17-auto-apply-runbook]] — the recipe for filling AND submitting a **LinkedIn Easy Apply** form (answer-bank-only rule, blank beats wrong, skip beats invent, numeric fields reject words)
- [[18-headless-trust-and-send-capability]] — **⚠️ read before touching the scheduled tasks or attaching a file to an email.** Why three robots were silently dead (one boolean), why a task exiting 0 proves nothing, and why cloud email tools cannot attach a local file
- [[19-post-creator-and-image-studio]] — isolated daily LinkedIn post creation & FLUX.1 / Imagen 3 high-res image studio MCP server (`tools/post_creator/`)
- [[20-first-email-batch-and-task-verification]] — the first 3 tailored CVs actually delivered (MX decides the Drive sharing mode), and the night Daily Discovery + Watch Accepts were finally **proven by log**
- [[23-phase-0-results]] — Phase 0 of the rewrite: what worked, the metric that lied, and the environment traps
- [[26-apply-at-volume]] — **⚠️ read before running `apply-all`.** Family CVs, the never-resubmit ledger, the four bugs the owner caught by watching, the wrong answer that passed every guard (D31), and the research half the batch left out (D32)
- [[21-linkedin-content-strategy-and-research-engine]] — Deep research strategy & 4-slide storytelling copywriting framework.
- [[27-linkedin-content-engine]] — **7-Day Content Engine**: Content Hub SQLite DB, experience logger, trend finder, dispatch engine, image prompt templates, fallback cache. Decisions D37-D40.
- [[25-linkedin-profile-reframe]] — **the complete profile rewrite**: headline, about, 3-role Verventech experience, ECC open-source entry, skills, education (B.Tech completed), ready-to-paste copy in `output/linkedin/profile-ready-to-paste.md`
- [[10-advanced-ideas]] — advanced enhancements (email classifier, interview prep, ATS auditor, Exa AI, HN parser, Slack buttons)

## North star

Get interviews in **days** through tailored, timely, human-approved outreach —
not ban-inviting mass spam. See [[05-decisions]] for why this framing is non-negotiable.

## The one rule the rewrite turns on

> **Anything that is the same every time → code.**
> **Anything that is different every time → AI.**

A LinkedIn Easy Apply form is 19 fields of dictionary lookup and **one** question that needs a model.
Today an agent does all twenty, for sixteen minutes. [[22-rewrite-architecture]] explains the fix and
[[05-decisions]] D26-D28 records the reasoning.
