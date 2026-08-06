# 23 — Phase 0 results: the thesis holds, the measurement did not

Back to [[00-INDEX]]. **Run date 2026-08-06.** First execution of `apps/autopilot/` — the rewrite
from [[22-rewrite-architecture]]. Phase 0 goal: fill 5 LinkedIn Easy Apply forms in under 3 minutes,
stopping before submit, with zero invented values.

> ## ✅ PHASE 0 IS CLOSED — 2026-08-06
>
> **5 genuine fills, 72.1s, target 180s.** Three consecutive passing runs: **62.7s · 54.6s · 72.1s**.
> Zero invented values. Nothing submitted. It took **four attempts and three separate silent-blindness
> bugs** to get a run whose numbers meant anything — §1 is the first attempt, kept because the way it
> lied is the most useful thing in this file.
>
> | | First attempt | Closing run |
> |---|---|---|
> | Genuine fills | 2 of 5 | **5 of 5** |
> | Fill time | 33.3s (of a claimed 49.1s) | **72.1s** |
> | Fields filled | 9 | **23** |
> | Silently skipped | every grouped question | **none** |
> | Printed verdict | PASS (false) | **PASS (true)** |

---

## 1. What the first run printed, and why it was wrong

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

## 3b. The bug the checkbox fix uncovered — every grouped question was invisible

Fixing §3 did **not** make the consent box work. The re-run showed it still unticked *and* still
unreported. The DOM dump — not another guess — gave the real answer, and it was much bigger:

```
STEP 4
  raw fieldset count : 1
  raw checkbox count : 1
    checkbox[0] visible=False inside_fieldset=1 label=''
  _scan returned 1 control(s):
    tag=group  match=None  label=''          <-- the question, missing
```

Three stacked causes, each hiding the next:

1. **`inner_text()` omits visually-hidden text.** LinkedIn's `<legend>` is accessible-only, so the
   group's label came back `''`. `_fill_step` then hit `if not label: continue` — **neither filled
   nor reported**. Fixed with `text_content()` (`_deep_text`).
2. **The question is not always inside the fieldset.** Energy Exemplar's consent fieldset contains
   only the word *"Yes"*; the question sits in an **ancestor**. Fixed by climbing up to 4 levels
   and subtracting the fieldset's own text.
3. **"Is this text a question?" needed a real test.** A two-option radio yields `"YesNo"`, which is
   not a bare token, so an early `^(yes|no)$` check let it through as if it were the question.
   Fixed with `_looks_like_a_question()`: strip the answer tokens and require ≥8 characters left.

**Scale of it:** this was never really about one checkbox. **Every `<fieldset>`-based question —
all Yes/No radios and every consent box — was skipped in silence.** On the first run Energy
Exemplar reported `filled=6, blank=0`, which read like a clean sweep; all six were plain inputs and
every grouped question had vanished. `blank=0` did not mean "nothing was missed", it meant
"nothing was *seen*".

> **A zero in a report is only trustworthy if you know the thing that produces it can count.**

The structural fix matters more than any of the three: `_fill_step` **no longer skips an unlabelled
control**. It reports `(unlabelled <tag>, required=<bool>)`. Noisy beats invisible.

And `_fill_group` now **verifies with `is_checked()`** rather than trusting that a click landed —
reporting a tick that did not happen is the same class of lie as PASS-on-a-no-op.

---

## 3c. A wrong match that only failed safe by luck

With grouped questions finally visible, one matched the wrong spec:

> *"Do you have hands-on experience with MLOps and cloud platforms (Azure ML, AWS SageMaker, GCP),
> including model deployment, monitoring, **Docker/Kubernetes**...?"* → matched **`years_docker`**
> → tried to answer **"2"**.

It reported blank rather than answering wrongly — but **only because no radio option reads "2"**.
In a text input it would have typed `2` into a yes/no question on a real employer's form.

**Fix:** `Spec.requires`. Every `years_*` spec must now *also* match a quantity cue
(`how many|how much|how long|years|months|duration`). A skill name alone is not enough.

> **A fail-safe that works by accident is not a fail-safe.** The blank was luck, not design.

This question stays unanswered by design even now: it is **compound**, naming Azure ML and
SageMaker, which are not in the bank. Answering "Yes" would claim tools he has not recorded. It
goes to a human — correctly.

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

- **Five genuine fills in 72.1s**, three consecutive passing runs. Phase 0's stated test is met.

**Closing run, per job**

| Job | Company | Status | Time | steps | filled | blank |
|---|---|---|---|---|---|---|
| 4444658927 | SkillsCapital | reached-**submit** | 10.1s | 1 | 2 | 0 |
| 4442666851 | Infosys AI/ML | reached-review | 12.3s | 3 | 6 | 2 |
| 4436200537 | Energy Exemplar | reached-review | 28.0s | 4 | **7** | 0 |
| 4447280108 | VARITE INC | reached-review | 10.0s | 2 | 2 | 0 |
| 4443245139 | InCommon | reached-review | 11.7s | 3 | 6 | 0 |

`reached-submit` on SkillsCapital is **correct and safe**: that posting is a *single-step* Easy
Apply where the primary button is Submit on page 1. The code records the status and **breaks
without clicking**. Verified by screenshot — the modal is still open and unsubmitted.

Run-to-run variance is real (Energy Exemplar: 12.9s → 28.0s) and is entirely **page load**, not
logic. Budget for it before assuming a regression.

**Still NOT proved**
- Anything about submitting — Phase 0 never clicks Submit. The first real submission remains the
  single riskiest untested step in the project.
- **The re-scan-after-validation-failure branch.** Decision below.

### The unexercised numeric path — decided, not left hanging

Option (a) *did* happen naturally: Infosys asked three numeric screening questions and all three
were filled and **passed validation** — `Current CTC 0`, `Expected CTC 840000`, `Notice Period 0`.

So the [[17-auto-apply-runbook]] trap **did not fire, because the bank's values are correct**. That
is the good outcome, and it is also why the recovery branch stays cold: the code that re-scans a
step after a numeric field is rejected — and picks up the questions LinkedIn then reveals — has
never had a rejection to recover from.

**Resolution: (c), recorded as a known gap.** Option (b) was rejected too: a saved copy of the DOM
cannot reproduce the behaviour that matters, which is LinkedIn's *client-side validation* and its
*dynamic reveal* — the very things a static fixture lacks. Deliberately posting a wrong value to a
live employer form to trigger it is out of the question.

> **Known gap:** `stalled` / re-scan handling in `fill_job()` is written, reviewed, and unexecuted.
> The first time it runs will be in production. When a job first reports `stalled-validation`,
> treat that run as untrusted and read the screenshot before believing any of it.

**Next:** Phase 1 (own the data) — see [[22-rewrite-architecture]] §7. Not started; the owner asked
to see these numbers first.

---

---

## 11. Brain 3 had been stale for 11 days, and every status line said otherwise

Found while closing Phase 0. The graphify commit hook failed on every commit with
`No module named 'graphify'`, yet `py -3 -m graphify hook status` reported **both hooks installed**.

Both statements were true. git runs hooks in **Git Bash**, where the hook's
`command -v python3` finds `/c/Users/<user>/AppData/Local/Microsoft/WindowsApps/python3` — the
**Windows Store App Execution Alias stub**. It is a real executable, so `command -v` succeeds and
the hook picks it, but it has no site-packages and cannot import graphify. Meanwhile `py -3`, which
the human uses, resolves to the real interpreter where graphify is installed.

**Fix:** hardcode the absolute interpreter path in `.git/hooks/post-commit` and `post-checkout`,
with `py`/`python` kept only as a fallback. Then one manual rebuild to catch up:

```
graph.json  Jul 26:  75 nodes, 125 edges, 14 communities
graph.json  Aug 06: 390 nodes, 596 edges, 46 communities
```

**Same family as D17 and D25.** The status line described *installation*; the artifact described
*reality*, and nobody compared the two for eleven days. `graph.json` had a July 26 mtime while code
changed on August 6 — one `ls` would have shown it.

> **`hook status` tells you a hook is registered. It cannot tell you the hook works.**
> Judge Brain 3 by `graph.json`'s mtime, never by a status subcommand.

⚠️ **`.git/hooks/` is not version-controlled**, so this fix does not travel with a clone. Anyone
setting the project up on another machine will hit it again. Worth folding into a setup script.

---

Related: [[22-rewrite-architecture]] · [[17-auto-apply-runbook]] · [[05-decisions]] D15, D17, D23,
D25, **D29** · [[07-current-state]]
