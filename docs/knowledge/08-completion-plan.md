# 08 — Completion Plan (pipeline → done)

Back to [[00-INDEX]]. Live status: [[07-current-state]]. Build order rationale: [[04-roadmap]].

The plan to take the pipeline from "recipes run by hand" to a **complete end-to-end system**. Confirmed with
owner **2026-07-25**. Approach = **Path A (MCP-first + light glue)**, decision [[05-decisions]] **D10** — keep
Notion + MCP that already work; add only the automation layer on top. Do **not** rebuild the planned coded
`src/` system (Path B) — it duplicates what Notion/MCP provide (YAGNI).

> Sending stays deferred: owner reviews **everything** first and sends the final batch at the end. We still
> BUILD the send machinery (step 4) so that final batch is one reviewed click, not manual copy-paste.

## The gaps (what "complete" requires)

| # | Gap | State | Priority |
|---|-----|-------|----------|
| 1 | **Automatic daily discovery** (scheduled LinkedIn-MCP refresh → dedupe → score → Notion; <48h freshness + ghost-job filter) | manual only | 🔴 |
| 2 | **Event-driven Slack** (new match / draft ready / sent / reply / follow-up due) | connected, not wired | 🟠 |
| 3 | **Tracking + follow-up engine** (auto status advance; Day-3 / Day-7 nudges) | manual status only | 🟠 |
| 4 | **Send machinery** (Gmail send + throttle/caps from `.env`) | not built | 🟠 |
| 5 | **Per-job packet completeness** (cover letters · deep company research brief · PDF export · email verification) | partial | 🟡 |
| 6 | **Backlog depth** (interview-prep gen · LinkedIn profile optimization · response analytics · calendar) — see [[06-feature-backlog]] | not built | 🟢 |
| 7 | **FastAPI review dashboard** (optional; browser approve/edit/reject) | not built | ⚪ optional |

## Sequence (each step ends with something usable)

1. **Content layer (step 5 fast wins)** — ✅ **DONE 2026-07-25.** Cover letters for the 3 processed jobs
   (`output/outreach/<slug>/cover-letter.md`); **PDF export automated** (`tools/html-to-pdf.sh`, headless
   Chrome/Edge, no installs → `output/pdf/`); recruiter **email domains MX-verified** (exact mailbox still
   needs a per-address verify — the remaining sub-gap, do at send time). Deep company-research brief =
   deferred (light per-outreach detail suffices for now).
2. **Wire Slack to events** (gap 2) → ✅ **DONE 2026-07-25.** Built `tools/slack_notify.py` (no deps, reads
   token from `.env`) with event types: `new_match` 🎯 · `draft_ready` 📝 · `sent` 📤 · `reply` 💬 ·
   `followup_due` ⏰ · `digest` 📋. Tested live to channel C0AN5ASHZB6. Wired into `recruiter-outreach`
   Step 4 (fires `draft_ready`). Remaining triggers get wired as their steps are built (sent→step 4/send,
   reply/followup→step 3, new_match→step 5).
3. **Follow-up + tracking engine** (gap 3) → ✅ **DONE (built + dry-run tested) 2026-07-25.** Added Notion
   tracking fields (`Applied Date`, `Reply`, `Follow-ups Sent`, `Next Action`); built `tools/followups.py`
   (Day-3/Day-7 cadence → draft nudge → optional Slack `followup_due`) — verified across all cases (due/
   too-early/replied/maxed/not-applied). Tracking convention + run loop documented in `tools/README.md`.
   *Live data pending: no follow-ups can fire until real sends happen (owner sends at the end).*
4. **Send machinery with caps** (gap 4) → ✅ **DONE (built + dry-run tested) 2026-07-25.** Added the caps to
   `.env` (were only in `.env.example`); built `tools/send_queue.py` — filters APPROVED items, enforces daily
   cap + min-delay + 0–jitter, and prints the throttled send order (email Touch 1 scheduled; LinkedIn Touch 2
   listed for manual in-app send). Dry-run verified. **Executes via Gmail MCP in that order at the final batch
   — the tool never sends; sending stays human-gated + deferred.**
5. **Automatic daily discovery** (gap 1) → ✅ **DONE 2026-07-25.** Runs as a **local Windows Scheduled Task**
   ("Job Hunt - Daily Discovery", daily 08:00 IST) → `tools/daily-discovery.ps1` runs Claude headless against
   [[09-discovery-runbook]] using the real LinkedIn MCP + Notion + Slack. Unattended perms allowlisted in
   `.claude/settings.local.json` (no bypass). **Local, not cloud** — decision [[05-decisions]] D11 (Composio
   can't do LinkedIn job/people search; cloud IPs raise ban risk). Logs → `output/discovery-log/`.
   *Validation 2026-07-25: task wiring confirmed (fired + launched Claude headless); full run blocked by a
   Claude session/usage limit that hour — revalidate on the 08:00 run or a manual re-trigger after reset.*
6. **Backlog depth features** (gap 6) — reconciled with [[10-advanced-ideas]]. Progress 2026-07-25:
   - ✅ **LinkedIn profile optimization** → `output/linkedin/profile-optimization.md` (paste-ready: headline,
     About, skills, featured, open-to-work). Fixes the weak/typo'd headline.
   - ✅ **ATS keyword auditor** (idea 2.2) → `tools/ats_audit.py`. Applied truthful fixes: **Infosys 81%→94%**,
     **GoodSpace 87%**, **Innova 72%→83%** (Innova's remaining gaps — AWS/Helm/Grafana — are real skill gaps,
     deliberately NOT faked). Also **fixed a latent PDF-export bug** (`html-to-pdf.sh` produced blank PDFs on
     relative paths — now uses `cygpath -m -a`; would have sent blank CVs otherwise). PDFs regenerated.
   - ✅ **Email pipeline, both halves (2026-07-25):** OUTBOUND — the 3 target emails created as real **Gmail
     drafts** (first actual Gmail use; owner attaches CV PDF + sends; recruiter mailboxes still [VERIFY]).
     INBOUND — **reply classifier (idea 1.1) built + scheduled**: `tools/check-replies.ps1` + Windows task
     "Job Hunt - Reply Check" (~4×/day) runs [[11-reply-classifier-runbook]] — reads Gmail (read-only) →
     classifies → updates Notion Reply/Status → Slack alert. Not yet validated live (needs a real reply +
     limit reset). Gmail is a cloud connector, so this checker could later move to a true cloud routine.
   - ⬜ **Still buildable now:** interview-prep dossier (2.1), conversion analytics (4.1, needs live data),
     HN "Who is Hiring" parser (3.2).
   - ⬜ **Needs owner setup:** Exa MCP (3.1, API key), Firecrawl (3.3, key), Slack interactive buttons (1.2,
     local listener). FastAPI review dashboard (gap 7) also optional here.
   - ⬜ **Needs live data first:** interview-prep + analytics + calendar only fire once sends/interviews exist.
7. *(optional)* review dashboard (gap 7).

## Definition of done (the whole pipeline)

A new matching job appears in Notion **on its own** → owner gets a Slack ping → opens a review-ready packet
(tailored CV + cover letter + Highlight Reel + verified recruiter + dual-touch drafts) → approves → it sends
within caps → status tracks itself → Day-3/7 follow-ups fire → replies/interviews flow to Slack + Calendar →
analytics show what's landing interviews. Human decisions remain: which jobs, and final approval to send.
