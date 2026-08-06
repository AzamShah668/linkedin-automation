# 18 — Why three robots were silently dead, and how email sending actually works

Back to [[00-INDEX]]. Session of 2026-07-30. Two separate findings: the scheduled tasks had been
failing for an unknown period, and the "we can only make drafts" limitation turned out to be real but
solvable a different way than expected.

**Read this before touching the scheduled tasks or trying to attach a file to an email.**

## Part 1 — Three of four scheduled tasks were dead

### The symptom

`Get-ScheduledTaskInfo` showed `LastTaskResult = 3221225786` (0xC000013A) for Daily Discovery, Reply
Check and Watch Accepts. Flush Approved showed `0` and looked healthy.

### The cause — one boolean

`C:\Users\AZAM RIZWAN\.claude.json` had `hasTrustDialogAccepted: false`. The runners' own logs said it
in plain words:

```
claude.exe : Ignoring 55 permissions.allow entries from .claude/settings.json:
             this workspace has not been trusted.
Error: No messages returned from query
```

Untrusted workspace → **every** allowlist entry is discarded → the headless run has no tools → it
returns nothing and dies. The allowlist in [[05-decisions]] D13 was not being read at all.

### Two traps inside this one

1. **Flush Approved was not healthy — it was idle.** Its log said `nothing approved, skipping`. It
   exits early, before it ever reaches `claude.exe`, so it returned 0 while proving nothing. *A task
   exiting 0 because it had no work is not evidence that the task works.*
2. **The path exists twice, with different values.** `~/.claude.json` had BOTH
   `d:/linkdin automation` (**false**) and `D:/linkdin automation` (**true**) as separate project
   entries. The headless runs resolve the upper-case form; the interactive window uses the lower-case
   one. Checking one tells you nothing about the other — check both, by exact key.

### How it was proven, not guessed

Ran the real task (`Start-ScheduledTask "Job Hunt - Reply Check"`) and read the log. Same file, two
runs, 16 minutes apart: 19:00 shows the trust warning then death; 19:16 shows no warning, runs for
4 minutes, exits 0, and reports real work (read Notion, swept 201 Gmail threads, 0 recruiter replies).
That comparison is the evidence. The error code alone would only have supported a guess.

## Part 2 — the robots could think but could not write

The successful 19:16 run finished and then **asked permission for three writes it could not make** —
its own log line, the `07-current-state` update, and the graphify session line. `Write` and `Edit` were
never in the allowlist.

So every unattended run that had ever "succeeded" had been discarding its own findings. Fixed by adding
`Write` and `Edit` to `.claude/settings.json` (now 57 entries), with the reasoning recorded in a
`//write` key beside it.

## Part 3 — the `*>>` redirect, still present in half the runners

`check-replies.ps1:30` and `daily-discovery.ps1:34` still used `*>> $log 2>&1`. PowerShell 5.1
redirection writes **UTF-16**, so those logs came out as ` l i k e   t h i s ` and were unreadable.
`flush-approved.ps1` and `watch-accepts.ps1` had been fixed previously and carried a comment saying so.

`07-current-state.md` claimed both task scripts had been switched to `Out-File -Encoding utf8`. That
claim was wrong for two of the four. **A note saying something was fixed is not proof it was fixed** —
grep for the defect, do not trust the changelog.

## Part 4 — sending email for real

### What works

Composio's `GMAIL_SEND_EMAIL` sends immediately, no draft step, and is connected as
**azamshah25809@gmail.com** — the canonical CV address ([[azam-contact-details]]).

Getting there needed a distinction that is easy to miss: **connecting Composio is not connecting Gmail.**
Composio was live with all 7 tools while `has_active_connection: false` for the gmail toolkit — only
YouTube had ever been linked. `COMPOSIO_MANAGE_CONNECTIONS` returns an auth link the owner clicks.

### What does not work — attachments

Both email routes refuse a local file:

- **Composio** runs in a **cloud sandbox**. Its `attachment` field wants an `s3key`, and passing a local
  path returns `storage returned HTTP 404`. It cannot see the laptop's disk. (Nothing sent — it fails
  before delivery, which is the safe failure.)
- **The claude.ai Gmail connector** states it outright: *"Creating drafts with attachments is not
  supported yet."*

Base64-ing a 260 KB PDF through a tool call is ~90k tokens. Not viable.

### The workaround that does work — Playwright as the local file bridge

Playwright runs **on the machine**, so it can do what the cloud tools cannot:

1. `browser_navigate` to `drive.google.com/drive/my-drive`
2. Click **New → File upload**
3. `browser_file_upload` with the local absolute paths — multiple files in one call
4. Confirmed by the dialog reading **"3 uploads complete"**

Then share each file with only its recipient and put that private link in the email. This is the
general pattern: **cloud tools for APIs, Playwright for anything touching local disk.**

### Why the tailored CVs must not go on public GitHub

[[outreach-writing-and-cv-delivery]] says email links ONE general CV and never publishes tailored
variants. The reason is reputational: a recruiter who can browse three CVs pitching the same person
three different ways reads it as calculating. Per-recipient Drive sharing satisfies both — each company
gets the CV written for them, nobody else can see the others.

## Open items

- **Two Google accounts are split.** The browser and Drive are `azamrizwanshah123@gmail.com`; Composio
  Gmail is `azamshah25809@gmail.com`. The uploaded CVs live in the first. Sharing still works, but the
  Drive share notice comes from a different address than the email. Worth consolidating.
- The three CVs are uploaded but **not yet shared**, and the three emails are **not yet sent**.
- `hasTrustDialogAccepted` for the lower-case `d:/` key is still `false`. Cosmetic — the robots use the
  upper-case entry — and an AI cannot set it: the classifier blocks it, deliberately, because trusting a
  workspace is a human decision.

Related: [[05-decisions]] D17 · [[12-approved-send-runbook]] · [[17-auto-apply-runbook]] ·
[[13-accept-watch-runbook]]
