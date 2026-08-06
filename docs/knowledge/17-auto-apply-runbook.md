# 17 — Auto-apply runbook (LinkedIn Easy Apply: fill AND submit)

Back to [[00-INDEX]]. The recipe a headless Claude follows to take one built packet and actually **submit**
a **LinkedIn Easy Apply** application. Driven by `tools/auto-apply.ps1 -JobId <id>` (or `-All`).

**This runbook SUBMITS.** It is the only thing in this project that completes an irreversible action with
no human tick — owner decision D16, 2026-07-29 — after he pointed out that a queue waiting on his laptop
is not automation. Read D16 before changing any rule below.

> **Retargeted 2026-07-30 (D18).** This runbook used to drive **external ATS** sites (Greenhouse, Lever,
> Ashby, Workday) and explicitly skipped anything Easy-Apply-only. That was backwards: the board is
> populated from LinkedIn search, so the overwhelming majority of rows *are* Easy Apply, and the runner
> was skipping the exact thing it should have been doing. External ATS is now the fallback, not the target.

## Which browser drives this

**Playwright, in the `.pw_browser` profile** — the same local-file bridge used everywhere else
([[18-headless-trust-and-send-capability]]). It runs on the machine, so it can attach a PDF from disk,
which no cloud tool can.

**That profile must be logged into LinkedIn.** It is a different directory from
`~/.linkedin-mcp/profile`, so a LinkedIn login in the MCP's Chromium does **not** carry over. If step 1
finds a logged-out profile, the run stops and says so rather than flailing at a login wall.

The **LinkedIn MCP is not used here**. The job description is read off the page we are already standing
on. That keeps this runner clear of the D13 profile-contention bug entirely.

## Inputs

- `-JobId <notion-page-id>` — one role, or `-All` to sweep every board row at status `To Apply`.
- The packet must already exist: `output/outreach/<slug>/packet.json` plus `output/pdf/<cv_stem>.pdf`.
  If it does not, stop. Building is [[15-build-packet-runbook]]'s job, not this one.
- `profile/application-answers.json` — the **answer bank**. The only legal source of field values.

## The one hard rule

> **Only values from the answer bank go into a real employer's form.**

No inference, no "reasonable guess", no filling a number because the form insists. A guessed notice period
or salary is a false statement sent to a company under Azam's name. The bank's `NEEDS_AZAM` block is null
on purpose — null means *leave blank*, always.

**One derivation is permitted**, because it is a fact and not a guess:
`how_did_you_hear_about_us` → `LinkedIn`, since every role on this board was discovered through LinkedIn.
Nothing else may be derived.

## ⚠️ Numeric fields reject words (proven 2026-07-29 — do not rediscover this)

LinkedIn's Easy Apply number inputs validate client-side and silently block the Next button. Two answers
in the bank are the *word* form and will fail:

| Question | What fails | What to type | Bank key |
|---|---|---|---|
| Notice period | `Immediate` | `0` | `availability.notice_period_days` |
| Expected CTC (India) | `8.4` | `840000` | `compensation.expected_ctc_india_annual_inr` |
| Expected CTC (international) | `30k` | `30000` | `compensation.expected_ctc_international_usd_year` |

**And the part that matters more:** once those two validate, LinkedIn **reveals additional Yes/No
questions that were hidden behind the failing field**. A snapshot taken before fixing them is an
incomplete picture of the form. Always re-snapshot after any value is corrected, and never assume the
first snapshot showed you every question.

Salary India vs international differ by roughly 40x. The wrong one is an instant auto-reject. If the
employer's country is genuinely unclear, use the India figure.

## Steps, in order

### 1. Preflight
- Confirm `output/outreach/<slug>/packet.json` exists and `output/pdf/<cv_stem>.pdf` is on disk.
  No PDF, no application.
- Confirm the row's status is `To Apply`. Anything else means it was already handled — skip it.
- `browser_navigate` to `https://www.linkedin.com/feed/`, then `browser_snapshot`. If it shows a sign-in
  page, **stop the whole run** and report `linkedin-logged-out`. Do not attempt to log in; a headless
  login attempt on LinkedIn is exactly the behaviour that gets accounts restricted.

### 2. Open the job
`browser_navigate` to the row's LinkedIn job URL, then `browser_snapshot`.

- **Easy Apply button present** → continue at step 3.
- **Only an external "Apply" that leaves LinkedIn** → follow it and fall back to the external-ATS path
  (step 3b). Same rules, same answer bank.
- **Already applied** (LinkedIn shows "Applied") → log `already-applied`, set status `Applied`, move on.

Read the job description off this same snapshot. That is the input for the salary country decision and
for nothing else — it never becomes a form value.

### 3. Work the Easy Apply modal, one step at a time
Easy Apply is a **multi-step wizard**, not one form. Typical order: contact info → résumé →
screening questions → review → submit. So:

1. `browser_snapshot` the current step.
2. Map every visible field (table below) and fill what is known.
3. Click **Next**.
4. `browser_snapshot` again. **Verify the step actually advanced.** If the same step is still showing,
   a field failed validation — re-read it, apply the numeric rule above, and expect newly revealed
   questions.
5. Repeat until the button reads **Review** then **Submit application**.

Never click Next twice without a snapshot in between. That is how a run half-fills a form and loses track.

#### 3b. External ATS fallback
If the route left LinkedIn, this is the old path: single long form, `browser_fill_form` for the bulk,
`browser_select_option` for dropdowns, submit once. Everything else in this runbook still applies.

### 4. Map every field before typing anything

| Verdict | Meaning | Action |
|---|---|---|
| **known** | maps to a non-null answer-bank value | fill it |
| **unknown-optional** | no bank value, field not required | leave blank |
| **unknown-required** | no bank value, field IS required | **abort this job** |

Do the mapping **first, for the whole step**, then fill.

On **unknown-required**: stop, do not submit, set status `Blocked - needs answer`, append the field name
to `output/apply-log/needs-answer.md`, and move to the next job. Do not wait for anybody.

Dropdowns: `browser_select_option`. If no option matches a bank value, that field is **unknown**, not a
licence to pick the nearest one.

### 5. Attach the TAILORED CV
LinkedIn pre-fills the résumé slot with whatever was uploaded last. That is almost always the wrong one.

- Read `cv_stem` from `output/outreach/<slug>/packet.json`.
- The file is `output/pdf/<cv_stem>.pdf`.
- Choose **Upload résumé** and `browser_file_upload` that absolute path. Do **not** accept the
  pre-selected previous résumé, and never attach the generic CV.
- Verify by snapshot that the shown filename is `<cv_stem>.pdf`. A wrong filename here means the company
  receives a CV written for a different company.

### 6. Verify before submitting
On the review step, `browser_snapshot` and re-read what is actually in the fields. Confirm:
- name, email, phone match the bank exactly
- the résumé shows the tailored filename
- no field contains a value that is not in the bank
- no validation error is showing

Any mismatch → do not submit. Log and move on.

### 7. Submit
`browser_click` **Submit application**, then `browser_wait_for` the confirmation ("Your application was
sent", "Application sent", or the modal closing).

### 8. Confirm it landed
- `browser_take_screenshot` → `output/apply-log/<slug>-<date>.png`. This is the receipt.
- If no confirmation appears within the wait, mark `Submitted - unconfirmed`. Do **not** resubmit; a
  duplicate application is worse than an uncertain one.
- ⚠️ LinkedIn's "your application was sent to X" **email is an auto-acknowledgement, not a reply.** Never
  let it tick the Notion `Reply` field — that kills the Day-3/Day-7 nudges.

### 9. Record
- Status → `Applied` in the local mirror, then `py -3 tools/notion_push.py`.
- Append one line to `output/apply-log/<YYYY-MM>.md`: date, company, role, outcome, screenshot path.

### 10. Next job
On `-All`, continue to the next row. **Randomised 40-180s gap between applications.** LinkedIn watches
application velocity; ten submissions inside a minute looks exactly like what it is. Cap a single `-All`
run at **5 applications**, then stop and report the rest as remaining.

## Never resubmit

One attempt per company per role, ever. **Recro (Generative AI Engineer) was submitted 2026-07-29** and
must never be attempted again, regardless of what its board status says.

## Definition of done (per job)

- [ ] Every filled value traces to `application-answers.json`
- [ ] Tailored PDF attached, not the generic CV, filename verified in a snapshot
- [ ] Screenshot receipt on disk
- [ ] Status `Applied` / `Blocked - needs answer` / `Submitted - unconfirmed` in Notion and the mirror
- [ ] A line in the apply log

## Failure rules

- **Never invent a value.** Blank beats wrong. Skip beats invent.
- **Never resubmit.**
- **Never attempt a LinkedIn login** from an unattended run.
- **Never use `browser_run_code_unsafe` or `browser_evaluate`** on an employer's form.
- On anything strange — a login wall, a CAPTCHA, a payment request, an assessment test — stop that job,
  log the reason, move on. Do not attempt to solve a CAPTCHA.

## Unblocking more forms

Every null in `NEEDS_AZAM` is a form the robot may have to abandon. The ones that block most often, in
order: `highest_qualification_percentage_or_cgpa`, `current_employer`, `reason_for_change`,
`passport_number`. Filling those in the bank converts abandoned forms into submitted ones with no code
change.

Related: [[15-build-packet-runbook]] · [[16-gui-automation-investigation]] ·
[[18-headless-trust-and-send-capability]] · [[05-decisions]] D15, D16, D18
