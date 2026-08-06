# 09 — Daily Discovery Runbook (the automatic robot)

Back to [[00-INDEX]]. This is the exact recipe the **scheduled Claude routine** runs every morning
(completion-plan [[08-completion-plan]] step 5, decision D10 / D7). It must be followable cold — a scheduled
agent starts with no memory of prior sessions. **Read [[07-current-state]] first**, then do this.

## Guardrails (non-negotiable)
- **Read-only discovery.** LinkedIn MCP `search_jobs` / `search_people` only. No connect, no DM, no apply.
- **No sends.** This routine only *finds, scores, stores, and pings*. Outreach/sending stays human-gated.
- **Ban-safe volume.** A handful of targeted searches, not scraping-at-scale. Stop if MCP errors (recovery:
  `uvx mcp-server-linkedin@latest --status` once, then retry — see [[07-current-state]]).
- **Zero fabrication** in scores/notes — ground every fit call in the profile evidence.

## Inputs
- **Target roles:** DevOps / Platform · MLOps / AI Engineer · Backend · SRE · Forward Deployed Engineer.
- **Locations:** India (esp. Bengaluru, Hyderabad, Remote) + Remote.
- **Profile / scoring source of truth:** `profile/master-profile.md`, `output/cv/positioning-selector.md`,
  `output/cv/achievement-bank.md`.
- **Store:** Notion "Job Hunt — Autopilot" — data source `collection://2902aad8-1dbd-4bdc-b5e3-6cc4fa494be2`.

## Steps

### 1. Search (LinkedIn MCP, read-only)
Run `search_jobs` for the target roles × locations, e.g. keywords: "DevOps Engineer", "Platform Engineer",
"MLOps Engineer", "AI Engineer", "Site Reliability Engineer", "Forward Deployed Engineer" — location "India"
and "Remote". Prefer roles **posted < 7 days** (freshness wins). Collect: title, company, location, work
type, url.

### 2. Dedupe against Notion
Query the store for existing rows and **skip anything already present**:
```sql
SELECT "Job","Company","userDefined:URL" FROM "collection://2902aad8-1dbd-4bdc-b5e3-6cc4fa494be2"
```
Match on URL when available, else on (Company + normalized Job title). Only *new* jobs proceed.

### 3. Score fit (0–100)
Score each new job against the profile using the positioning-selector signals. Rough bands:
90+ = bullseye (DevOps/Platform/MLOps with the exact stack); 80–89 = strong; 70–79 = plausible stretch;
< 70 = drop (below `FIT_SCORE_THRESHOLD` in `.env`). Note the 1-line reason.

### 4. Warm-intro check (the D8 move — every promising job)
For each job scoring ≥ 80, run one `search_people` for a **shared-roots insider** at that company
(mutual connection → Central University of Kashmir → Kashmir/Srinagar/J&K region → past employer). If found,
set **Warm Intro = ✓** and record the person + tie in Notes. See [[05-decisions]] D8; only claim a verified tie.

### 5. Insert into Notion
For each new job ≥ threshold, create a page with: `Job`, `Company`, `Fit Score`, `Location`, `Work Type`
(Remote/Hybrid/On-site), `Source = LinkedIn`, `Status = New`, `Found = today`, `Warm Intro`, `URL`, and a
short `Notes` (fit reason + warm tie if any). Do **not** touch existing rows.

### 5b. Auto-build packets for anything scoring 85+ (decision D13)
Every new job at **fit ≥ 85** gets the FULL packet built immediately, with no human decision: tailored CV
(+PDF, ATS-checked ≥85%), recruiter via the D8 warm-insider check, Touch 1 email, Touch 2 LinkedIn note,
Slack action card + `slack_upload.py` of the CV. Jobs at **0–84** are stored and reported only.
**Batch by company first** — several roles at one employer share a recruiter search and often a CV variant.

### 6. Notify (Slack digest)
Fire one digest with the day's finds (highest fit first), flagging warm-intro ones:
```
py -3 tools/slack_notify.py --event new_match --title "N new jobs (M warm)" --text "<top jobs, fit-sorted>"
```
If nothing new cleared the threshold, send a short "no new matches today" `info` (or skip — owner's choice).

### 7. Log
Append a line to this project's session log / update [[07-current-state]]'s job table counts if materially
changed. Never send outreach — hand off to the owner via the Notion board + Slack.

## Success = every morning, new fresh-and-scored jobs appear in Notion (warm-intro flagged), and the owner
gets one Slack digest — with zero sends and zero ban risk.
