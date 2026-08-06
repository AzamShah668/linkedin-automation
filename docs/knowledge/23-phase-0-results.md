# 23 — Phase 0 results: the thesis holds, the measurement did not

Back to [[00-INDEX]]. **Run date 2026-08-06.** First execution of `apps/autopilot/` — the rewrite
from [[22-rewrite-architecture]]. Phase 0 goal: fill 5 LinkedIn Easy Apply forms in under 3 minutes,
stopping before submit, with zero invented values.

**Verdict: the architecture is proven. The run that "passed" was not a valid test.**

---

## 1. What the run printed, and why it was wrong

```
launch 4.3s (not counted) · selection 34.6s (not counted) · FILL 49.1s / 5 jobs · VERDICT: PASS
```

| Job | Company | Status | Time | steps | filled | blank |
|---|---|---|---|---|---|---|
| 4444658927 | SkillsCapital | `no-next-button` | 4.3s | 1 | 0 | 0 |
| 4442666851 | Infosys AI/ML | `no-next-button` | 7.7s | 1 | 0 | 0 |
| 4436200537 | Energy Exemplar | **reached-review** | 19.0s | 4 | 3 | 4 |
| 4447280108 | VARITE INC | `no-next-button` | 3.8s | 1 | 0 | 0 |
| 4443245139 | InCommon | **reached-review** | 14.3s | 3 | 6 | 1 |

**Three of five jobs did nothing at all** — `filled=0`, `blank=0`, `steps=1`, out in under 8 seconds
— and all three counted toward a 5-job PASS.

The real result is **2 forms in 33.3s**, ≈16.7s/job, so five genuine fills project to **~85s**.
Still comfortably inside the 180s target. The thesis survives; the metric did not.

> **A metric that reports success for a no-op is worse than no metric, because it stops you
> looking.** `report()` now counts only jobs reaching Review/Submit toward the verdict, prints the
> no-op jobs by name, and labels a partial run `INCOMPLETE SAMPLE` with a projected figure.

This is the same family as D17 (*judge by the log, never the exit code*), one level up: here the
**tool's own success metric** was the thing lying.

### Where the time went — the good answer

19.0s for a 4-page wizard and 14.3s for a 3-page one is **page loads, not field mapping**. Mapping
33 regexes against a step's labels is microseconds. Had field mapping been the cost, the whole
design would be in question; page-load cost has ordinary fixes (block images/analytics, reuse the
tab) and is not on the critical path yet.

---

## 2. Root cause of `no-next-button`: the dialog is visible before it exists

`modal.wait_for(state="visible")` was satisfied by the **dialog shell** — title bar and close
button — while LinkedIn streamed the form in afterwards.

The VARITE screenshot is the proof: a dialog titled *"Apply to VARITE INC"* wrapping **a bare
spinner**. `_scan()` found zero controls, `_primary_button()` found zero buttons, and the job was
written off in 3.8 seconds.

**The SkillsCapital screenshot nearly caused a misdiagnosis.** It shows a fully rendered form —
contact info, résumé, everything — which looks like it disproves the theory. It does not: the
screenshot is taken *after* the loop breaks, and `_capture_resume()` runs a second time after it.
Content arrived between the failed scan and the screenshot.

> **A screenshot is evidence of the moment it was taken, not of the moment that failed.** Two
> screenshots of the same bug looked like two different bugs.

**Fix:** `_wait_for_step_content()` waits for the **primary footer button** — the element whose
absence *is* the bug, and one that every wizard step has exactly one of. Auto-wait, not a poll and
not a sleep. A step that never renders now reports `modal-never-rendered`, which is honest, instead
of `no-next-button`, which blamed the wrong thing.

---

## 3. A silent blindness found while fixing the above

`_scan()` excluded **standalone checkboxes** (only checkboxes inside a `<fieldset>` were read).

Energy Exemplar's form had a **required** consent checkbox — *"&lt;company&gt; has my consent to
collect, store and process my data"*. It was never filled, never reported, and never counted. It
would have blocked a real submit while the log showed nothing wrong.

This is more dangerous than a blank: a blank appears in the unanswered report and gets fixed. An
unscanned control is **invisible in both directions**. Standalone checkboxes are now scanned.

---

## 4. Consent checkboxes — the decision

Mapped, as `consents.data_processing = "Yes"`, in a **separate bank block from facts**.

The reasoning matters more than the answer:

- The *"never invent a value"* rule ([[17-auto-apply-runbook]], D15) exists to prevent **false
  statements**. A guessed salary is a lie sent under Azam's name. **A consent tick states nothing
  false**, so that rule does not decide this.
- It is an act of agreement, so the real question is **authority, not truth**. The owner authorised
  the application; consenting to process the CV you are in the act of sending is instrumental to
  it. Withholding consent while submitting is incoherent — the data goes to them either way.
- The risk is lopsided. Not ticking blocks a required field and the application dies silently.
  Ticking means a company he chose to apply to may process a CV he chose to send.

**Scope is deliberately narrow.** Only data-processing / privacy-policy consent for *this*
application. Marketing opt-ins, background-check authorisations, agency-representation terms and
"I agree to be contacted by partners" are **not mapped** and go to a human.

> If a consent pattern ever starts matching one of those, **narrow the pattern — never widen the
> value.**

---

## 5. Fields that could not be answered ⭐

The most valuable output of the run. Each line converts an abandoned form into a submittable one.

| Count | Field | Resolution |
|---|---|---|
| 2× | `Email address*` | **Not a missing key** — see §6. LinkedIn pre-selects its own verified address; ours is not an option. Now reported as *prefilled/mismatch*, not *unanswered*. |
| 1× | `First name*` | Added as `identity.first_name`. |
| 1× | `Last name*` | Added as `identity.last_name`. |
| 1× | `Website` | Mapped to the existing `identity.github`. |

The earlier reasoning that LinkedIn always pre-fills first/last name — and that mapping them would
be "inventing a field shape" — **was wrong in practice**. They came back blank *and* required.
They are now explicit owner-supplied bank keys, still not a `full_name` split in code.

---

## 6. ⚠️ The email mismatch — action needed from the owner

The LinkedIn account's verified address is **`azamrizwanshah123@gmail.com`**.
The answer bank and every generated CV use **`azamshah25809@gmail.com`** (the canonical one).

The bank value is **not among LinkedIn's selectable options**, so every Easy Apply submission
carries an address that does not match the CV attached to it. Blanking a required select would be
worse, so the code keeps LinkedIn's value and now reports the mismatch explicitly.

**Only the owner can fix this** — add the canonical address to LinkedIn's verified emails and make
it the default. Until then, recruiter replies may land in the wrong inbox.

---

## 7. Two findings the runbook now depends on

**Draft persistence: CONFIRMED.** LinkedIn offered to **save a draft on 4 of 5 jobs** when the
modal was dismissed. This was an open question in [[17-auto-apply-runbook]]; it is now settled.
We click **Discard** every time. The consequence: **a run that crashes mid-wizard without
discarding leaves a half-filled application in the owner's LinkedIn UI**, which is exactly the
"five half-open applications" state to avoid. `_close_modal()` runs in the failure path too.

**The résumé slot pre-fills the GENERIC CV.** All three jobs that reached the résumé step showed
`azam-shah-devops-cv.pdf`, dated 7/29/2026 — not a tailored variant. Runbook §5 predicted this and
is confirmed in production. Phase 0 does not submit, so it only reports the filename; **Phase 3
must upload the tailored PDF or companies receive a CV written for someone else.**

---

## 8. Board rot: ~63% of the top rows are dead

Of the 32 highest-fit candidates probed:

| Result | Count |
|---|---|
| `closed` — "no longer accepting applications" | ~20 |
| `external-or-none` — external ATS, not Easy Apply | 6 |
| **live Easy Apply** | **5** |

The board was last discovered on 2026-08-01. **Five days rotted roughly two thirds of it.**

Consequences: discovery must run far closer to application time than "whenever"; and the ~34.6s
selection probe is doing real work — it is the only thing standing between the pipeline and 20
applications to closed reqs. Do not optimise it away.

Also note every Infosys row came back `external-or-none`. Infosys does not use Easy Apply, so the
Easy Apply runner will never reach it — that company needs the external-ATS path or the warm
recruiter route.

---

## 9. Environment traps paid for on the day

**Both browser profiles were unusable, for two different reasons.**

1. **`.pw_browser/` cannot launch at all.** `Last Version` = `150.0.7871.187` — the owner's *real*
   Chrome 150 opened that directory on 2026-08-01. Chromium refuses a profile written by a newer
   build and exits **instantly with code 21**, before any Playwright error is meaningful. The
   working profile is the subdirectory **`.pw_browser/linkedin_user_data/`** (on 145, older than
   Playwright's build, which upgrades forward cleanly). `PW_USER_DATA_DIR` overrides it, and the
   chosen directory is now printed on every run.

   > Note this contradicts [[17-auto-apply-runbook]], which says "the `.pw_browser` profile". The
   > runbook meant the subdirectory. A profile directory that contains another profile directory
   > is a trap worth naming.

2. **A logged-out profile is identified by a missing `li_at` cookie**, not by an error string.
   The profile had a `JSESSIONID` and no `li_at` — `li_at` is LinkedIn's actual auth cookie. This
   is the durable version of the D13 addendum rule (*never diagnose auth from an error message*):
   there is a **positive test**, so use it.

```
sqlite3 .pw_browser/linkedin_user_data/Default/Network/Cookies \
  "select name from cookies where host_key like '%linkedin%' and name='li_at'"
```

Recovery is `py -3 -m apps.autopilot.run login`, which opens a real window and waits for the owner
to sign in **by hand**. An unattended automated login is what gets accounts restricted; a human
typing their own password is not, and it is what the working poster script has always done.

---

## 10. What Phase 0 proved, and what it did not

**Proved**
- Playwright library + a dictionary beats an agent loop by roughly two orders of magnitude.
- Field mapping is free; page loads are the only real cost.
- Zero LLM calls were needed to fill a real form. Not one value was invented.

**Not proved**
- Five genuine fills in one run (best so far: two).
- Anything about submitting — Phase 0 never clicks Submit.
- The re-scan-after-validation path ([[17-auto-apply-runbook]] §numeric fields). No numeric
  validation failure occurred, so the code that handles LinkedIn revealing hidden questions is
  **written but unexercised**.

**Next:** re-run against 5 live Easy Apply jobs with the render fix in place. If it lands under
180s with 5 real fills, Phase 0 closes and Phase 1 (own the data) begins.

---

Related: [[22-rewrite-architecture]] · [[17-auto-apply-runbook]] · [[05-decisions]] D15, D17, D23,
**D29** · [[07-current-state]]
