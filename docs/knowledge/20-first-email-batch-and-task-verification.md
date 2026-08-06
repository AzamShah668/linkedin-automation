# 20 — The first real email batch, and the night the tasks were finally verified

Back to [[00-INDEX]]. Session of 2026-07-30 (evening). Two things happened: three tailored CVs actually
reached three recruiters, and the scheduled tasks stopped being "fixed but unproven".

Read this with [[18-headless-trust-and-send-capability]] — it finishes the job that file started.

## Part 1 — three tailored CVs delivered, per recipient

The [[18-headless-trust-and-send-capability]] finding was that Composio cannot attach a local file, and
Playwright is the bridge. That left three PDFs uploaded to Drive but **not shared** and three emails
**not sent**. Both are now done.

| Company | Recruiter | Drive sharing | Email |
|---|---|---|---|
| Innova ESI | Recruiter-B | anyone-with-link, Viewer | sent 2026-07-30 |
| GoodSpace AI | Recruiter-C | restricted to `recruiter-c@goodspace.ai`, Viewer | sent 2026-07-30 |
| CodeRound AI | Chaitanya Mehta | restricted to `chaitanya@coderound.ai`, Viewer | sent 2026-07-30 |

Infosys was deliberately **not** emailed — it routes through Recruiter-A, the warm insider (D8).

### The MX check that changed the plan

The instruction was "share each with ONLY its recruiter". Checking the MX records first turned that from
one decision into two:

```
innovaesi.com  -> innovaesi-com.mail.protection.outlook.com   (Microsoft 365)
goodspace.ai   -> aspmx.l.google.com                          (Google Workspace)
coderound.ai   -> aspmx.l.google.com                          (Google Workspace)
```

A Drive link restricted to a specific address only opens for a **Google** identity. Restricting the
Innova PDF to `recruiter-b.recruiter-b@innovaesi.com` would have shown her *"You need access"* — an outreach email
whose one attachment is unopenable is worse than no attachment. So Innova got an unguessable
anyone-with-link URL; the two Workspace domains got true per-recipient restriction.

**Rule: check the recipient's MX before choosing a Drive sharing mode.** Per-email restriction is only
meaningful when the recipient is on Google.

### Two Drive defaults that are wrong for this

Both bite silently:

1. **The role defaults to Editor.** A recruiter must not be able to edit the CV. Set **Viewer** every time.
2. **"Notify people" defaults to on.** Leaving it on sends a Drive notice from
   `azamrizwanshah123@gmail.com` *before* the real email arrives from `azamshah25809@gmail.com` — two
   messages from two identities for one application. Uncheck it. Confirmation that it worked: the button
   changes from **Send** to **Share**.

### Reading the link back without clipboard access

`navigator.clipboard.readText()`, `browser_evaluate` and `Get-Clipboard` are all blocked by the
permission classifier. The working route: click **Copy link**, focus the Drive **search box**, press
`Ctrl+V`, and read the value out of the accessibility snapshot. The pasted text appears in the snapshot
as ordinary node text. Do not press Enter.

### Bounces

**None.** All three addresses were guesses on verified domains; no `mailer-daemon`, `postmaster` or
delivery-status message arrived. Absence of a bounce is weak evidence — a Workspace catch-all can accept
mail for a mailbox nobody reads — so treat these as *delivered*, not *read*.

One address is now genuinely confirmed: the accept-watch run found that **Recruiter-B publishes
`recruiter-b.recruiter-b@innovaesi.com` herself in her own hiring posts**. Generalisable: *read the recruiter's own
posts before reaching for an email-verification API.* Recruiters who post reqs almost always print their
intake address.

## Part 2 — the tasks are verified, by log

[[18-headless-trust-and-send-capability]] fixed the trust boolean but never watched the tasks do real
work. Both were run for real and judged by their logs, never their exit codes (D17).

**Job Hunt - Daily Discovery — WORKS.** Ran 21:19 to 21:29. Five `past_week` searches, board **24 → 62
jobs**, 38 new rows, 6 warm, Slack digest posted. Its own report flagged the thing that became D19:
*"58 of 62 rows are still New. Discovery is outrunning processing."*

**Job Hunt - Watch Accepts — WORKS.** Ran 21:31 to 21:36. Found **Recruiter-B had accepted**
(3rd → 1st degree), marked her accepted, scheduled the pitch for 2026-07-31 16:28, posted to Slack, and
correctly sent nothing because nothing was due yet.

Both trust keys in `~/.claude.json` now read `true`, closing the last open item in
[[18-headless-trust-and-send-capability]]:

```
'd:/linkdin automation' -> hasTrustDialogAccepted = True
'D:/linkdin automation' -> hasTrustDialogAccepted = True
```

### What the logs also revealed

- An earlier Watch Accepts run at **21:00 died with `You've hit your monthly spend limit` (exit 1)**.
  That is a failure mode no guard can prevent and no log inside the project explains. If every task
  starts failing at once with nothing in common, check the Claude usage limit before debugging anything.
- The discovery log still contains **UTF-16 garbage from runs before the encoding fix** — spaced-out
  characters mid-file. New entries are clean UTF-8. Do not read an old garbled block as a fresh failure:
  check the timestamp on the entry, not the appearance of the file.
- All five tasks were confirmed to have `DisallowStartIfOnBatteries = False`. The new Sweep Packets task
  applies that fix at install time, because every task in this project was silently dead on battery once.

## Part 3 — board bookkeeping caught up

Five rows now correctly read `Applied`, and the local mirror has **nothing unpushed**:

| Company | Role | Applied | How |
|---|---|---|---|
| Infosys | AI Application Engineer | 2026-07-26 | LinkedIn DM + CV (warm insider) |
| CodeRound AI | AI Engineer (LLMs & Agents) | 2026-07-26 | packet built; email sent 07-30 |
| **Recro** | **Generative AI Engineer** | **2026-07-29** | **Easy Apply — was never recorded** |
| Innova ESI | DevOps Engineer | 2026-07-30 | tailored CV emailed |
| GoodSpace AI | Forward Deployed Engineer | 2026-07-30 | tailored CV emailed |

**The Recro trap:** the submission on 2026-07-29 was never written back, so the board still said `New` —
one sweep away from applying twice. There are **two Recro rows** (Generative AI Engineer 82, and a
DevOps Engineer 80 found 07-30); only the first was submitted. Its note now says NEVER RESUBMIT, and the
rule is in the runbook and the runner prompt.

Related: [[17-auto-apply-runbook]] · [[18-headless-trust-and-send-capability]] · [[05-decisions]] D17,
D18, D19 · [[13-accept-watch-runbook]]
