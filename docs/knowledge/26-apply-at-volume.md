# 26 — Apply at volume: what the batch runner does, what it broke, and the half it left out

> Written 2026-08-10, after two days of real submissions. Read with [[23-phase-0-results]] (the filler),
> [[24-cv-bridge]] (the CV), and [[05-decisions]] **D31 · D32 · D33**.
>
> One-line summary: **the machine now applies. It does not yet reach a human, and that is the half that
> was ever going to produce an interview.**

---

## 1. What was built

Phase 0 filled a form. Phase 1 (`cv.py`) attached a tailored CV. This layer answers the question those two
left open: *what do you attach to the other eighty rows, and how do you avoid applying to the same job
twice?*

| Piece | File | What it is |
|---|---|---|
| **Role-family CVs** | `apps/autopilot/families.py` | Three pre-built CVs — DevOps/Platform/SRE, AI/ML Engineer, Software Engineer — routed by job title |
| **Never-resubmit ledger** | `apps/autopilot/ledger.py` | Append-only, fsync'd JSONL at `output/apply-log/submitted.jsonl` |
| **Batch runner** | `apps/autopilot/run.py apply-all` | Plans from the board mirror, picks a CV, throttles, submits behind `--submit` |

### The family CV is a deliberate middle tier

Two tiers existed before and both were wrong for eighty rows:

- **Tailored packet** — ~7 minutes of Claude Code per company. Correct, unaffordable at eighty.
- **Generic CV** — free, and the thing this project exists *not* to send.

The family CV is the third option: written once per role family, so a DevOps req gets DevOps evidence and
an AI req gets AI evidence, without a per-company run. `pick_cv()` prefers a tailored packet when one
exists, falls back to the family, and **never falls back to the generic CV** — a missing family CV returns
`kind="none"` and the row is skipped, because "apply with whatever LinkedIn pre-filled" is a worse outcome
than not applying.

### The ledger is deliberately independent of every board status

`ledger.py` imports nothing that can reach Notion or the SQLite mirror, and a test asserts that by walking
the module's AST. The reason is [[05-decisions]] D23/D29: the mirror has been both stale *and* wrong, and a
duplicate application to the same employer is not a recoverable error. The ledger is the one fact that must
not depend on a store that has already lied twice.

It was seeded from **the send record** — Gmail Sent and LinkedIn application history — not from board
notes. That distinction was not academic: the board said SkillsCapital was "still unsent", and Gmail proved
it had been emailed on 2026-08-01. Seeding from notes would have produced a duplicate on the highest-fit
row on the board.

`fill_job()` checks the ledger **before navigation**, so a duplicate costs 0.0s rather than a page load,
and it also reads LinkedIn's own "Applied" indicator as an independent second mechanism.

---

## 2. What actually went out

**Thirteen applications, two days, zero replies.**

| Channel | Count | Notes |
|---|---|---|
| Email (tailored packet) | 5 | 07-30 batch + SkillsCapital 08-01; four follow-ups sent 08-09 |
| LinkedIn DM | 1 | Infosys, via Recruiter-A |
| **Easy Apply (family CV)** | **8** | 08-09 ×5, 08-10 ×3 |

Fill time held at Phase 0's numbers — around 15 seconds a form once the browser is warm. Throttling
between applications is randomised 40–180s, because LinkedIn watches application *velocity*, not fill
speed.

---

## 3. Four bugs the runner shipped with, all found by the owner watching it run

Each one is a variant of the same disease [[05-decisions]] D30 names: **the tool reported something
plausible while doing the wrong thing.**

### 3.1 It throttled after skips, so it looked busy and applied to almost nothing

The 40–180s sleep ran after *every* row, including rows that were skipped in one second. The owner watched
a batch "go through the jobs but not apply for those jobs" — accurate, and the log gave no hint, because a
skip and a submission printed at the same cadence. Now only a real submission earns a throttle; a skip gets
3–8s.

### 3.2 Yes/No radios were never clicked

`_fill_group()`'s text-matching fallback required `count == 1`. That condition covers a lone consent
checkbox and **nothing else** — every two-option Yes/No group in existence has `count == 2`, so every one
of them silently went unanswered. The owner spotted it from a screenshot; the runner had reported those
jobs as filled.

### 3.3 `--limit 5` submitted zero

`--limit` capped the *plan*, not the applications. The five highest-fit rows are all external-ATS companies
with no Easy Apply button, so the runner planned five rows, skipped all five, and exited having done
nothing while reporting a completed run. The loop now walks the whole plan and stops once `limit`
applications have genuinely gone out.

### 3.4 An over-broad pattern typed the wrong answer onto a real form — see **D31**

The `city` spec contained a bare `\blocation\b`. It matched:

> *"Have you ever appeared for an Interview at any Exl **location** during the last 90 days?"*

and answered **"Srinagar"**.

This is the single most important bug in the project's history, because of *how it evaded the guard*. The
answer-bank rule is "only values from the bank go on a real form". Srinagar **is** in the bank. The check
passed. A false statement went onto a real employer's form with every safety mechanism reporting green.

All `city` patterns are now anchored (`^city\b`, `^location\b`, `your current location`, …) and nine
regression tests taken from real forms assert that interview-location, shift, and client-location questions
do **not** match `city`. `Spec.requires` was added at the same time so that a Yes/No question mentioning
"Docker" can no longer match `years_docker` — that one had failed safe only because no radio option reads
"2", which is luck, not design.

---

## 4. 🔴 The half that was left out

Asked directly whether the people behind the filled forms had been researched and contacted, the answer
was **no**:

| Company | Packet | Recruiter identified | Outreach sent |
|---|---|---|---|
| Energy Exemplar | ✅ | ✅ | ❌ never sent |
| SkillsCapital ×3 | ⚠️ exists, but for a **different role** (the Intern req) | ⚠️ | ❌ |
| Crossing Hurdles ×2 | ❌ | ❌ | ❌ |
| Neurones IT Asia | ❌ | ❌ | ❌ |
| Celigo | ❌ | ❌ | ❌ |

The project's design is **packet = tailored CV + named recruiter + touch-1 email + touch-2 LinkedIn
message**. The batch runner implements the first half and nothing else. Five of eight submissions reached
an ATS queue with no human aware of them.

This is recorded as **D32** because it is not a bug — every component worked as written. It is a *scope*
failure: the fast path was built, and shipped, without the slow path that makes it worth running.
Thirteen applications and zero replies is the evidence, not the theory.

---

## 5. 🐛 Known, unfixed: the company cap locks out the best row on the board

`apply-all` caps applications at **one role per company**, counted across the ledger as well as the current
run — added after three SkillsCapital applications went out inside ten minutes.

The cap counts **every ledger row for that company, regardless of channel or age**. Infosys has one ledger
entry: a LinkedIn DM about *AI Application Engineer*. That single old DM now permanently blocks all four
Infosys rows, including **Junior AI Engineer (fit 90)** — the highest-value row in the project, the one
where Recruiter-A is already a 1st-degree connection inside the company, and the rare *Junior*-titled AI
req that fits a final-year student.

Recorded as **D33**. The cap should be about recency and channel — "no second Easy Apply to this company
within N days" — not a lifetime lockout triggered by a message sent weeks ago about a different job.

Same shape hides the other top rows: SkillsCapital (fit 93) is correctly skipped by the ledger, so the
plan's actual ceiling is **85**, and the "why is it applying to 80s?" question in [[07-current-state]] has
this as its answer rather than a broken scorer.

---

## 6. Where the board stands

- **31 candidate rows** planned and ready, 8 skipped (1 ledger, 7 company cap)
- ~60% of the wider board is **external ATS** with no Easy Apply button — no path built yet
- The two highest rows on the board are both unreachable by the batch runner, for different reasons

## 7. What this file says to do next

1. **Fix D33** — the cap is a ten-minute change and unblocks the single best opportunity in the project.
2. **Stop adding volume; add contact.** Thirteen applications with no named human is the measured
   failure. One identified human per submitted application converts a queue entry into a conversation.
3. **Then** resume the batch.

Not the database (Phase 1). It unblocks nothing a recruiter sees — the same argument that moved
[[24-cv-bridge]] ahead of it in [[22-rewrite-architecture]] §7.
