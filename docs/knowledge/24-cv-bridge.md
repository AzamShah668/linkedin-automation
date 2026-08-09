# 24 — The CV bridge: Claude Code as a subprocess

Back to [[00-INDEX]]. **Built 2026-08-06**, immediately after [[23-phase-0-results]] closed Phase 0.
This is `apps/autopilot/cv.py` plus the résumé-attach path in `fill.py` — the step that makes a fast
application also a *correct* one.

Phase order was changed for this: see [[22-rewrite-architecture]] §7.

---

## 1. Why this came before the database

Phase 0 succeeded in a way that created a new problem. `fill.py` fills a form in ~14 seconds **and
attaches whatever LinkedIn pre-filled** — confirmed in production to be the generic
`azam-shah-devops-cv.pdf` on every job tested.

Speed without the tailored CV is not a partial win. It is the exact failure this project exists to
avoid: ten generic applications in two minutes is the mass automation forbidden by the core rule
(and [[05-decisions]] D1/D2). **The faster `fill.py` got, the more urgent `cv.py` became.**

The database (D23, D29) is real and still needed, but it unblocks nothing a recruiter ever sees.

---

## 2. What `cv.py` is

~20 lines of actual logic. The intelligence stays where it already was — in
[[15-build-packet-runbook]] and the `cv-architect` / `recruiter-outreach` skills, reused unchanged.

```
claude -p "read docs/knowledge/15-build-packet-runbook.md and follow it for job id <id>. Send nothing."
```

CV writing is the one place a full agent session earns its cost: once per **company**, read by a
**human**, not latency-sensitive, and needing judgment (read the JD, find evidence, refuse to
fabricate). Everything else in the app is a dictionary lookup.

**Measured:** one packet ≈ **7 minutes** wall clock (Energy Exemplar, 17:00 → 17:07), producing a
tailored CV in HTML + MD, a 105 KB PDF at **ATS 90**, `jd.txt`, `contact.md`, `cover-letter.md`,
`touch-1-email.md`, `touch-2-linkedin.md`, and `packet.json`. Sends nothing.

---

## 3. The ordering bug this shipped with, and the fix

The very first real run got it wrong, and the way it was wrong is the most useful thing here.

The packet built **completely**. Claude Code then hit its session limit *right after finishing*.
`cv.py` checked the limit string before checking for the artifact, so it raised `UsageLimitHit`:

```
** STOPPED: Claude usage limit — NOT a problem with job 3ae29d9d...
** 1 job(s) untouched. They are NOT failures — retry after the reset.
```

Meanwhile `output/pdf/8-Energy-Exemplar-DevOps-Engineer.pdf` was on disk, 105 KB, complete.

**The report and the filesystem disagreed, and the filesystem was right.**

The bug was in the D25 port itself: over-correcting for "a limit is not a job failure" into "a log
message outranks a file on disk". The rule that resolves it:

> **Check the artifact first. Only when there is no artifact does the log get to explain why.**

`build_packet` now returns the completed packet carrying a `limit_notice`. `build_many` records the
success *and* stops the batch — because the limit is real and the next job would fail — without
disowning work that finished. Both D17 and D25 hold, in that order.

Regression test: `tests/test_cv_bridge.py::test_completed_packet_wins_over_a_usage_limit_message`.

---

## 4. The résumé upload: there is no file input

`fill.py` attaches `output/pdf/<cv_stem>.pdf` from the packet. The obvious implementation —
`locator("input[type=file]").set_input_files(...)` — **silently does nothing**, because there is no
such element.

Verified by counting it on every step of a live form:

```
STEP 1  modal input[type=file]: 0   PAGE input[type=file]: 0
STEP 2  modal input[type=file]: 0   PAGE input[type=file]: 0   'Upload resume' button: 1
STEP 3  modal input[type=file]: 0   PAGE input[type=file]: 0
STEP 4  modal input[type=file]: 0   PAGE input[type=file]: 0
```

LinkedIn's **Upload resume** button opens a **native OS file chooser** through JS. The correct
Playwright API is `page.expect_file_chooser()`:

```python
with page.expect_file_chooser() as chooser_info:
    upload_button.first.click()
chooser_info.value.set_files(str(pdf))
```

`_attach_resume` tries a real `input[type=file]` first (other forms do have one) and falls back to
the chooser.

### The read-back is not optional

After upload, the filename is read back off the modal and compared to the expected name. A mismatch
sets status `resume-mismatch` and **aborts that job**.

This check exists because its failure is invisible: a company receives a CV written for a different
company, the form submits cleanly, every log looks fine, and nobody finds out. Runbook §5 warned
about it; Phase 0 measured it happening on 100% of jobs.

**Proof it works** — first run after the fix:

```
resume=8-Energy-Exemplar-DevOps-Engineer.pdf [OK]      (was: azam-shah-devops-cv.pdf [unverified])
```

plus LinkedIn's own *"Resume uploaded successfully"* toast and the consent box ticked, stopped at
Review. Fill time 14.5s including the upload.

⚠️ **Side effect:** uploading adds the tailored CV to the owner's LinkedIn résumé store. Harmless
(nothing is submitted) but the list will accumulate one CV per company over time.

---

## 5. Status flags `fill.py` can now return

| Status | Meaning |
|---|---|
| `reached-review` / `reached-submit` | filled successfully, stopped before submitting |
| `resume-mismatch` | uploaded CV did not read back correctly — job aborted, nothing submitted |
| `modal-never-rendered` | dialog shell appeared, contents never streamed in |
| `stalled-validation` | step would not advance — **untested path**, see [[23-phase-0-results]] §10 |
| `no-easy-apply` / `closed` / `already-applied` | not actionable |

`[OK]` / `[MISMATCH]` / `[unverified]` in the report is the résumé verification state.
`[unverified]` means no packet was supplied, so the generic CV is still attached — fine while
nothing submits, **fatal once it does**.

---

## 6. What is still not done

- **Nothing submits.** Still behind a flag the owner has not asked for. This remains the single
  riskiest untested step in the project.
- **Packets exist for 8 of ~90 board rows.** Every row without one would attach the generic CV.
  Building the rest costs ~7 min each and is capped by Claude session limits at roughly 5/day
  ([[22-rewrite-architecture]] §10). **Partly mitigated 2026-08-09** — see §7.
- **`build_many` is untested against a mid-batch limit in production** — only the offline test
  covers it.

---

## 7. The middle tier: role-family CVs (2026-08-09)

There were only two tiers before: a **per-company packet** (~7 min, capped at ~5/day) or the **generic
`azam-shah-devops-cv.pdf`**. With packets on 8 of ~90 rows, the generic CV was the real default, and it
is a *DevOps* CV going out for AI and general-engineering roles.

Three reusable **role-family** CVs now sit between the two. Each targets a whole family rather than one
employer, so it attaches to many applications without another Claude session:

| Family | Stem | PDF |
|---|---|---|
| DevOps / Platform / SRE | `FAMILY-DevOps-Platform-SRE` | `output/pdf/FAMILY-DevOps-Platform-SRE.pdf` |
| AI / ML Engineer (LLMs, agents, MLOps) | `FAMILY-AI-ML-Engineer` | `output/pdf/FAMILY-AI-ML-Engineer.pdf` |
| Software Engineer (fallback) | `FAMILY-Software-Engineer` | `output/pdf/FAMILY-Software-Engineer.pdf` |

Sources: `output/cv/family/<stem>.{html,md}`. Built from `output/cv/achievement-bank.md` + `profile/`
only, zero fabrication, self-audited at **ATS 95** each.

**What changed in the writing.** A tailored CV leads with a company hook. A family CV has no company,
so it leads with **breadth of evidence** instead: the stat-card row and the summary establish range
(18+ projects, 6 languages, the numbers that hold across every JD in that family), and the projects are
ordered by relevance to the family rather than to one job.

**They do not replace packets.** Ranking stays: per-company packet > family CV > generic. Use a family
CV where a packet does not exist and is not worth 7 minutes; build the packet for anything scoring high
enough to write outreach for.

⚠️ `fill.py`'s `[unverified]` state still applies — nothing wires these into the runner yet, so a run
without a packet still attaches whatever LinkedIn pre-filled. Selecting a family CV by role family is
the obvious next step and is **not built**.

---

Related: [[23-phase-0-results]] · [[22-rewrite-architecture]] §5, §7 · [[15-build-packet-runbook]] ·
[[17-auto-apply-runbook]] §5 · [[05-decisions]] D17, D25, **D30**
