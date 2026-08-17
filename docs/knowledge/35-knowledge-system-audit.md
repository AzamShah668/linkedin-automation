# 35 — Knowledge system audit (2026-08-17)

**Question asked:** is the three-brain system beneficial or gibberish, does it cost too much context,
and — the real one — *does a problem it has already solved stay solved?*

**Answer in one line:** the content is good, the capture is excellent, and **retrieval is the broken
half**. Nothing here is gibberish; the system writes 3–5× more than it reads, so lessons are recorded
faithfully and then re-derived months later at full cost.

Every number below is a count or a date. No adjective without evidence behind it.

---

## 1. There are five stores, not three

| Store | Where | Size | In the doctrine? |
|---|---|---|---|
| Brain 0 — Conversations | vault `Conversations/` (230 md) | 6.9 MB | as an appendix |
| Brain 1 — Patterns / Projects | vault | 164 + 99 KB | ✅ |
| Brain 2 — `docs/knowledge/` | this repo, 35 files | 646 KB | ✅ |
| Brain 3 — Graphify | this repo | 1.26 MB | ✅ |
| **Claude Code memory** | `~/.claude/projects/*/memory/` — **126 notes, 330 KB, 6 projects** | | ❌ **not documented anywhere** |

The undocumented fifth store is the one whose index is **auto-injected into context every session**,
so it has more influence on behaviour than the three that are documented. Most of this audit's
duplication findings involve it.

Also present in the vault but outside the system: **28 MB of course notes** (`pw ai-ml` 17 MB,
`web dev- pw` 6 MB, `hover-notes-images` 4 MB, `data analytics`, `udemy`). They cost nothing —
nothing loads them — and are out of scope.

---

## 2. Behaviour: what was actually read, counted over 164 transcripts (312 MB)

| Store | Real reads | Writes | Read : write |
|---|---|---|---|
| Brain 2 | **469** | 218 | 2.2 : 1 |
| Claude memory | 150 | — | used |
| Brain 1 | 50 (15 of them today) | 28 | 1.8 : 1 |
| **Brain 3 — `graphify query`** | **1** | rebuilt every commit | **once, ever** |

⚠️ **The first attempt at this measurement said 555 Brain-3 queries.** That was matching the
instruction string inside `CLAUDE.md`, which loads every session — not invocations. The instruction
has been carried **564 times** to be executed **once**. Any repeat of this audit must count *tool
calls*, never string occurrences. This project's own vault already warns about it:
`the-instrument-can-be-the-bug`.

### 2a. Brain 2's usage is not what the doctrine claims

Of its 469 reads, **254 come from the 96 scheduled-runner sessions** reading their runbooks. Those
same 96 sessions read Brain 1 **zero** times.

So Brain 2 is doing **two different jobs**, and only one of them is "the why":

| Half | Files | Reads | What it really is |
|---|---|---|---|
| **Runbooks** | 09, 11, 12, 13, 15, 17, 31 | ~254 | **executable procedure** — load-bearing, a robot follows it verbatim |
| **Reasoning** | 01–08, 22–34, decisions | ~215 | consulted by interactive sessions for orientation |

This distinction is worth making because the two need opposite treatment: a runbook must be exact
and current or the robot breaks; a reasoning file may be long and historical.

---

## 3. Content quality — Brain 1 (45 Patterns, 35 Projects pages)

**Verdict: high.** Scored on transferable / actionable / falsifiable / unique, the Patterns notes
hold up. They state what to *do*, carry the failing input or the date, and most would be true in a
repo sharing no code with their origin. `success-sentinel-not-exit-code`,
`survey-before-you-pay-per-lesson` and `name-match-is-not-identity-match` are better than most
published writing on the same topics.

**The defect is placement, not quality.**

- `Research/` **empty**. `Sessions/` one file since April. `Daily/` dead since 9 June.
  `Decisions/` untouched 66 days. These four need a human ritual; `Patterns/` survives because it is
  written as a by-product of real work. **A store that needs a ritual dies.**
- Until today the 45 notes had **no index**, so retrieval meant blind grepping — slower than
  re-solving the problem. The sibling store that *is* read constantly (Brain 2) differs structurally
  in exactly one way: it has an `00-INDEX.md`.
- 11 cross-project lessons were written onto a **project page** (`Projects/LinkedIn-Automation.md`)
  where no other repo would ever see them. Promoted 2026-08-17; the page now records which.

---

## 4. The disease: duplication, not absence

The same principle is recorded in two or three stores, under names sharing **no words**, so no
filename check would catch it.

### Confirmed duplicate pairs

| Claude memory (auto-injected) | vault `Patterns/` | Note |
|---|---|---|
| `choose-failure-direction-first` (2026-08-11) | `choose-the-failure-direction-then-earn-it` | written **today**, 6 days after the memory |
| `never-exercised-is-never-checked` (2026-08-14) | `green-without-work-is-not-a-pass` | written **today**, 3 days after |
| `a-channel-you-dont-read-is-not-quiet` | `wrong-probe-gives-a-confident-negative` | same principle |
| `recording-the-send-matters-more` | `verify-outward-actions-from-outside` | same principle |
| `silent-failure-is-the-house-style` | `success-sentinel-not-exit-code` | same principle |
| `one-source-is-not-enough` · `a-keyword-hit-is-not-a-relationship` | `name-match-is-not-identity-match` | 2 → 1 |
| `fallback-must-be-a-different-road` | `free-model-fallback-chain` | same principle |
| `consent-is-not-access` | `google-oauth-clients-across-projects` | same principle |

🔴 **The first two were written by me today, while diagnosing the duplication problem** — and the
index for the store I duplicated (`MEMORY.md`, 66 one-line entries) **was already in my context.**
The failure was not a missing index. It was not reading the index I had.

That matters for the fix: **an extra index does not cure it.** A write-time check does.

### The opposite gap: cross-project lessons trapped in project scope

Nine memories are general engineering truths with **no vault counterpart** — invisible to every other
repo:

| Memory | Why it belongs in Brain 1 |
|---|---|
| `headless-automation-gotchas` · `scheduled-tasks-are-born-broken` · `wake-stampede-needs-a-lock` · `powershell-lock-gotchas` · `business-hours-must-be-code` · `one-browser-profile-many-steps` | Windows scheduling and single-resource contention — true of **any** unattended automation on Windows |
| `derive-the-input-set-never-retype-it` | a stale hand-copied list hid a whole channel for 8 days |
| `shim-of-the-same-name-imports-itself` · `slug-is-not-a-comparison-key` · `freshness-stamp-must-match-its-scope` | plain software-engineering traps |

So the system fails in **both directions at once**: the same lesson written twice across scopes, and
genuinely global lessons never promoted out of one.

---

## 5. Is Brain 2 capable? Yes — 95% accurate

Checked every repo path mentioned in `docs/knowledge/*.md`:

```
190 paths referenced   180 exist   10 missing
```

Five of the ten are in `10-advanced-ideas.md` — proposed files, not drift. Two are deleted temp files
named in `07-current-state.md`.

⚠️ **The detector over-reported, and the correction is worth recording.** It flagged
`tools/pipeline_runner.py` in three files; two of those are **before/after tables documenting the
move** (`| tools/pipeline_runner.py | backend/pipeline_runner.py |`), which are correct. A path
matcher cannot tell "this file is here" from "this file used to be here". Real drift: **one**
reference, in `14-send-board-dashboard.md` — now fixed. *A tool that counts mentions is not measuring
claims.*

**Weakness:** `07-current-state.md` is **2,496 lines / 221 KB** and named "current state" while
being an append-only diary. `CLAUDE.md` instructs "read it 2nd each session", which is impossible —
and an unfollowable instruction gets skipped entirely rather than partially.

---

## 6. Is Brain 3 capable? Yes for one question shape, and it never admits a miss

Benchmarked on **10 real questions** taken from past sessions:

```
6/10 answered from the graph alone · avg 0.5s · ~1,500 tokens per query
```

| Result | Questions |
|---|---|
| **HIT** | pitch delivery flow · answer bank → fill · scoring → board · CV family routing · browser contention · finding a human |
| **MISS** | what writes the ledger · where the connect cap lives · where the free stack calls the LLM · what validates a CV |

The pattern is sharp: **hits are multi-file *flow* questions; misses are "where is X" questions whose
answer is the filename** — `ledger.py`, `connect.py`, `llm.py`, `cv_validate.py`. For those, a glob
costs ~0.2s and ~50 tokens and never misses.

🔴 **And a nonsense query returns 6,038 chars of confident-looking nodes.** `graphify query "banana
zeppelin unrelated nonsense"` produces the same volume of plausible output as a real question. There
is **no "I don't know" signal**, so a miss is indistinguishable from a hit — the same disease as
everything else in this audit.

**Therefore the rule is narrow, not general:** use Brain 3 for *how does X flow across modules* and
*what touches Y*. Use a glob for *where is X*. Never trust a single query's output as complete
without one corroborating read.

---

## 7. The token ledger

| Always-on, every session | words | ~tokens |
|---|---|---|
| project `CLAUDE.md` | 3,382 | 4,498 |
| global `CLAUDE.md` | 1,112 | 1,479 |
| `rules/` (common + web + zh + python) | 6,273 | 8,343 |
| — of which **`rules/zh/` is a Chinese translation of `rules/common/`** | 1,071 | 1,424 |
| `MEMORY.md` index | 1,486 | 1,976 |
| `brain1-patterns` hook (new today) | 955 | 1,270 |
| **TOTAL** | **13,208** | **17,567** |

**This morning it was 17,819 words (~23,700 tokens). Net saving: 4,611 words (~6,100 tokens) per
session**, after paying for the new hook — funded by moving 24 changelog entries out of `CLAUDE.md`
into [[34-changelog]].

⚠️ **The hook fires on all 96+ scheduled-runner sessions too, and those read Brain 1 zero times.**
That is ~1,270 wasted tokens per robot run. Gate needed (see §8).

`rules/zh/` is the single largest remaining pure waste: 10 of its 11 filenames are identical to
`rules/common/`, saying the same thing in Chinese.

---

## 8. What was changed, and what remains

### Applied 2026-08-17

| Fix | Effect |
|---|---|
| `Patterns/00-INDEX.md` created (45 → 50 notes, 0 orphans) | Brain 1 has a door |
| `brain1-patterns.js` SessionStart hook | the index is present without anyone remembering |
| `graphify query` → `py -3 -m graphify query` in both CLAUDE.md files | Brain 3 was unusable as documented |
| 24 changelog entries → [[34-changelog]] | −7,400 tokens/session |
| 11 mis-filed lessons promoted to 5 Patterns notes | cross-project lessons made visible |
| Conversation index filters 88 robot sessions | Brain 0's front page shows decisions again |

### The routing rule (this is the deliverable that prevents recurrence)

| Kind of fact | Canonical home |
|---|---|
| True in a repo sharing no code with this one | vault `Patterns/` **+ index line in the same edit** |
| Why this repo's code is shaped this way | `docs/knowledge/05-decisions.md` (D-numbers; never rewrite history) |
| Live state of this repo | `docs/knowledge/07-current-state.md` (a snapshot, not a diary) |
| An exact procedure a robot executes | `docs/knowledge/<n>-*-runbook.md` (must be exact and current) |
| How *I* should behave in this repo | `~/.claude/projects/*/memory/` (auto-injected) |
| What was said and rejected | vault `Conversations/` (automatic; never hand-write) |
| What the code *is* | `graphify-out/` (derived; never authored) |

**Write-time check, because the read-time index demonstrably did not stop me:** before creating any
note, search the *claim* — not the filename — across `Patterns/`, this project's `memory/`, and
`05-decisions.md`. The two duplicates found today share **no words** in their names.

### Also applied

| Fix | Detail |
|---|---|
| **14 duplicate pairs merged** | canonical vault note keeps the principle; each memory gained a `Canonical (cross-project)` pointer and kept only its project-specific instance. **27 of 65 memories now point at a canonical note; 11 distinct targets, 0 broken.** |
| **13 trapped memories promoted** | three new vault notes: `unattended-windows-automation-realities` (the 6 Windows/scheduler realities, from 7 memories), `derive-the-input-set-never-retype-it` (from 4), `identifiers-that-look-equal-but-are-not` (from 3) |
| **Hook gated for unattended runs** | `CLAUDE_UNATTENDED=1` set in `pipeline.cmd` and `pipeline-free.cmd`; verified — 0 chars emitted when set, 7,966 when not |
| **`14-send-board-dashboard.md`** | the one genuine stale path fixed |

Brain 1 is now **47 notes, 47 indexed, 0 orphans, 0 broken links**; hook ~1,418 tokens.

### Still open — owner's call

1. **Five individual scheduled runners remain ungated.** `Reply Check`, `Watch Accepts`,
   `Flush Approved`, `Daily Discovery`, `Sweep Packets` call their `.ps1` **directly**, so gating them
   means editing Claude-stack files — which breaks the "diff against `rewrite/phase-0` is empty"
   invariant you asked for. One additive `$env:CLAUDE_UNATTENDED='1'` line each would do it. Cost of
   leaving it: ~1,400 tokens per robot run, a handful of runs a day.
2. **Split `07-current-state.md`** into a ≤150-line snapshot plus an archive — it is 2,496 lines and
   `CLAUDE.md` tells every session to read it.
3. **Delete `rules/zh/`** unless it is read: −1,424 tokens **every** session, and 10 of its 11
   filenames duplicate `rules/common/`.
4. **A `PreToolUse` hook on Write into `Patterns/`** that greps the other stores first — the
   mechanical version of §8's write-time check, if discipline fails again.

---

## 9. The recurrence test — the only measure that matters

Three known repeats, and whether the post-audit system would now surface the answer *before* the
action:

Run against the **live hook output**, not argued — 8 of 8 pass:

```
PASS  2026-08-16 wrong-person invite  -> name-match-is-not-identity-match
PASS  2026-07-26 auth false alarm     -> verify-live-identity-before-diagnosing
PASS  2026-08-14 fallback rebuilt     -> free-model-fallback-chain
PASS  2026-08-17 duplicate written    -> knowledge-needs-a-hook-not-a-rule
PASS  silent success / exit 0         -> success-sentinel-not-exit-code
PASS  task dead on battery            -> unattended-windows-automation-realities
PASS  stale hand-typed input list     -> derive-the-input-set-never-retype-it
PASS  Gmail credential question       -> google-oauth-clients-across-projects

15 trigger-table rows · 47 notes reachable in one read · ~1,418 tokens
```

All eight are present before the first user message of a session. **That is the system working as
designed for the first time.**

> **The honest caveat.** Today's own duplication was *not* caused by a missing index — the relevant
> index was already in context and went unread. So the hook raises the floor; it does not close the
> loop. The write-time claim search in §8 is the part that addresses what actually happened, and it
> depends on discipline, which is what failed. If it fails again, the next step is mechanical: a
> `PreToolUse` hook on Write into `Patterns/` that greps the other stores first.

See also [[00-INDEX]] · [[34-changelog]] · [[05-decisions]] D52/D53 · vault
`Patterns/knowledge-needs-a-hook-not-a-rule`.
