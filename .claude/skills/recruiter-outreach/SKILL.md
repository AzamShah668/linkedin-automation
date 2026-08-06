---
name: recruiter-outreach
description: >
  Build ban-safe, human-approved dual-touch recruiter outreach for a target job — find the
  recruiter/hiring contact, then draft Touch 1 (formal email + tailored CV) and Touch 2 (a personal
  recruiter message leading with the Highlight Reel + one researched proof-of-effort detail).
  Use when a job is dragged to "To Apply", or to generate/review outreach for one or more target roles.
  Never sends without human approval.
---

# Recruiter Outreach — the dual-touch engine

The outreach half of the Job Hunt Autopilot. It turns a tailored application into a **timely, personal,
two-channel touch** that actually gets replies — without mass-spamming or risking the LinkedIn account.

Read the project rule first: **quality + human-approved outreach beats mass automation.** Everything here
is automated up to the send; the **send is always a human decision.** See `../cv-architect/SKILL.md` for
the CV/Highlight-Reel it builds on, and `docs/knowledge/02-architecture.md` for where this plugs in.

## What "dual-touch" means

For one target job, produce **two complementary messages** to two channels — never a copy-paste of each other:

| | Touch 1 — Formal email | Touch 2 — Personal recruiter message |
|---|---|---|
| **Channel** | Gmail (connected) | LinkedIn (connect note ≤300 chars, or DM if 1st-degree) |
| **Tone** | Professional, structured | Warm, first-person, human |
| **Leads with** | Role + one matched metric | The single strongest quantified win (Highlight Reel) |
| **Carries** | Tailored CV (PDF) + GitHub links | One *researched* detail about the company |
| **Ask** | "Open to a quick call this week?" | "Would love to connect / send my CV" |
| **Attachment** | Yes (tailored CV) | No (offer it) |

Why two: the email delivers the full proof (CV + links); the LinkedIn note is the human, in-feed nudge
that makes the recruiter actually open the email. Together they beat either one alone.

## The flow (per job)

```
job → find recruiter → draft Touch 1 (email) → draft Touch 2 (LinkedIn) → REVIEW QUEUE
        │                                                                      │
   references/find-recruiter.md                                    [HUMAN approves/edits/rejects]
                                                                               │
                                                              approved → send (throttled, capped, logged)
                                                                               │
                                                              schedule follow-ups (Day 3 + Day 7)
```

### Step 1 — Find the recruiter (`references/find-recruiter.md`)
Resolve a real hiring contact for the company, ban-safe. Order of preference:
1. **Email already in the posting / ATS payload** (best — explicit, no guessing).
2. **LinkedIn MCP** — `search_people` / `get_company_employees` filtered to `recruiter | talent | technical recruiter | hiring | <role> hiring manager`. Read-only: capture name, role, profile URL. **No auto-connect, no auto-DM.**
3. **Inferred company email** — apply the company's known pattern (`first.last@domain`, `first@domain`, …) and **verify** before use; otherwise fall back to the role/careers inbox.
Record confidence. If no named human is found, address Touch 1 to the role inbox and hold Touch 2.

### Step 2 — Draft Touch 1, the formal email (`references/dual-touch-templates.md`)
Subject names the exact role. Body = 1 hook line (who + role + one metric matched to their stated need) →
2–3 proof bullets pulled from `output/cv/achievement-bank.md` → tailored-CV + GitHub links → one clear ask.
Attach the matching tailored CV from `output/cv/tailored/`.

### Step 3 — Draft Touch 2, the personal LinkedIn message
Lead with the strongest single quantified win from `output/outreach/highlight-reel.md`, add **one specific
researched detail** about the company (proof-of-effort — the biggest anti-spam signal), and a light ask.
Keep a connection note ≤ **300 characters**; a DM (1st-degree) may be a touch longer.

### Step 4 — Stage in the review queue, never auto-send
Write every draft to `output/outreach/<company-slug>/` and add a row to `output/outreach/REVIEW-QUEUE.md`
with `status: draft`. **Post the full phone-ready action card to Slack** so the owner can act from their
phone without opening any file (recruiter, tappable LinkedIn link, the exact message to copy, email + CV):

```
py -3 tools/slack_action_card.py --company <slug>
py -3 tools/slack_upload.py --file output/pdf/<tailored-cv>.pdf --title "<Company> - <Role> CV"
```

**Always send the tailored CV PDF with the card** (second command) so the owner has it on their phone.
Slack files stay inside the workspace, so this does not breach D12 (never publish tailored variants
publicly). Requires the `files:write` scope on the bot token.

**The human moves it to `approved`**, then and only then does anything send. Log every state change as an
event. (Slack event layer + all event types: `tools/slack_notify.py`; see `docs/knowledge/08-completion-plan.md`.)

### Step 5 — Follow-up cadence
On no reply: polite nudge **Day 3** and **Day 7**, then stop. Each nudge is also queued for approval.

## Grounding & safety (non-negotiable)
- **Zero fabrication.** Every claim traces to `output/cv/achievement-bank.md` / `profile/master-profile.md`.
  Never invent a recruiter, a metric, or a company detail. If the researched hook can't be verified, mark it
  `[VERIFY]` and leave it for the human — do not ship a guess as fact.
- **Human-in-the-loop send.** Even in "LinkedIn MCP fully" mode, the MCP is used to *find and draft*, never
  to auto-send DMs or fire connection requests. The owner clicks send.
- **Throttle + cap.** Respect the daily outreach cap and min-delay+jitter from `.env`
  (`DAILY_OUTREACH_CAP`, `MIN_SECONDS_BETWEEN_SENDS`, `OUTREACH_JITTER_SECONDS`,
  `LINKEDIN_CONNECTS_DAILY_CAP`). Personalize every message.
- **One researched detail per Touch 2**, and it must be real. Anti-spam signal #1.
- See `references/message-rules.md` for anti-spam, humanization, and the throttle spec.

## Inputs / Outputs
- **In:** a job row (company, role, url, fit score, notes), the tailored CV in `output/cv/tailored/`,
  the achievement bank, the base Highlight Reel.
- **Out:** `output/outreach/<slug>/contact.md`, `touch-1-email.md`, `touch-2-linkedin.md`;
  a row in `output/outreach/REVIEW-QUEUE.md`. Nothing leaves the machine until approved.

## References
- `references/find-recruiter.md` — ban-safe recruiter discovery + email inference/verification
- `references/dual-touch-templates.md` — the two message templates + the fill-in contract
- `references/message-rules.md` — anti-spam, humanization, throttle/cap, follow-up cadence
