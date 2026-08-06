# 15 — Build-packet runbook (one role → a ready-to-send packet)

Back to [[00-INDEX]]. The recipe a headless Claude follows when the owner presses **Build the CV + outreach
packet** on a role in the dashboard. Driven by `tools/build-packet.ps1 -JobId <notion-page-id>`.

**This runbook sends nothing.** It researches, writes and stages. The only thing that leaves the machine is
a Slack card asking the owner to approve — which is the existing stage-1 gate ([[12-approved-send-runbook]]).

## Inputs

`-JobId` is the Notion page id of one row on the board. Everything else is looked up. If the row cannot be
found, stop and say so — do not guess a company from a partial match.

## Steps, in order

### 1. Read the role
Query the local mirror first (cheap, offline):

```
py -3 -c "import sys; sys.path.insert(0,'tools'); from board_db import connect, all_rows;
print([r for r in all_rows(connect()) if r['id']=='<JobId>'])"
```

Take: `job`, `company`, `fit`, `work_type`, `location`, `url`, `notes`. The **notes field often already
holds the research** from discovery (warm-alumni counts, apply instructions, comp signals) — read it before
doing any new research, or you will redo work that is already paid for.

If `url` is present, fetch the real job description with the LinkedIn MCP `get_job_details` so the CV is
tailored to the actual posting rather than to the job title.

### 2. Skip if it is already built
If `output/outreach/<slug>/packet.json` exists, stop and report that. Rebuilding silently overwrites drafts
the owner may have already approved.

### 3. Decide the slug
Lower-case, hyphenated company name (`Innova ESI` → `innova-esi`, `Procter & Gamble` → `procter-gamble`).
One packet per **company**, not per role: several companies on this board have two or three open roles behind
one contact, and messaging them twice is the fastest way to look automated ([[05-decisions]] D8).

### 4. Tailor the CV — invoke the `cv-architect` skill
Non-negotiables from that skill: **ATS ≥ 90**, zero fabrication, no AI-tells. Outputs:

- `output/cv/tailored/<n>-<Company>-<Role>.html` (+ `.md`)
- run `tools/html-to-pdf.sh` so `output/pdf/<same-stem>.pdf` exists — **the dashboard's download button
  needs the PDF**, and a packet without one is half-built
- audit it: `py -3 tools/ats_audit.py --cv <html> --jd <jd-file>` and record the score

### 5. Find the contact and write the messages — invoke the `recruiter-outreach` skill
**Warm insider first** ([[05-decisions]] D8): before any cold recruiter, look for someone inside who shares
real ground with the owner — home region, Central University of Kashmir, mutual connections. That is how the
Infosys door opened. Write `output/outreach/<slug>/`:

- `contact.md` — who, why them, degree, verification state of any email, and the strategy
- `touch-1-email.md` — the formal email (links the ONE general CV, never a tailored variant)
- `touch-2-linkedin.md` — the pitch that goes out **after** they accept, opening with the warm hook
- `cover-letter.md`

**Standing checks before writing anything to disk:** no em-dashes, no markdown asterisks (LinkedIn renders
them literally), no unresolved `{}`/`[]` placeholders, every number traceable to a public repo.

### 6. Write `packet.json` — this is what makes it appear in the dashboard

```json
{"slug": "...", "company": "<exact Notion Company value>", "role": "...",
 "cv_stem": "<pdf/html stem>", "ats": 94, "job_id": "<JobId>", "built": "YYYY-MM-DD"}
```

`company` **must match the Notion value exactly** or the board row will not find its packet. The dashboard
discovers packets by scanning for this file, so a packet without it is invisible however complete it is.

### 7. Set the status to `To Apply`
Notion (system of record) and the local mirror. From this runbook the clean way is
`py -3 tools/notion_push.py` after setting it locally, or update the Notion page directly if the MCP
connector is available in the run.

### 8. Post the Slack action card
`py -3 tools/slack_action_card.py` — ~5 lines: role, who, the CV, and the ✅/❌ gate
([[slack-message-brevity]] convention: cut anything that does not change the decision). The ✅ is what later
releases stage 1.

## Definition of done

- [ ] `output/outreach/<slug>/` has all four documents plus `packet.json`
- [ ] `output/cv/tailored/<stem>.html` **and** `output/pdf/<stem>.pdf` both exist
- [ ] ATS score recorded in `packet.json` and ≥ 90 (or the shortfall explained in `contact.md`)
- [ ] Status is `To Apply` in Notion and the mirror
- [ ] A Slack card is up, unticked
- [ ] Nothing was sent to anybody

## Failure rules

- **One LinkedIn server only.** If `tools/linkedin-doctor.cmd` reports more than one, stop — a contended
  browser profile reports as expired auth and you will waste the run chasing it ([[05-decisions]] D13).
- **Never invent a contact.** If no plausible person is findable, write `contact.md` saying so and leave the
  apply link as the route. A fabricated name is worse than no name.
- On anything strange, stop and report. A half-written packet is fine; a wrong one that gets approved is not.

Related: [[14-send-board-dashboard]] · [[12-approved-send-runbook]] · [[09-discovery-runbook]]
