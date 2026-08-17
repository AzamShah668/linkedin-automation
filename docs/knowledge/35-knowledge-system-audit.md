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
| Brain 2 | **469** ✅ calibrated | 218 | 2.2 : 1 |
| Claude memory | 150 | — | used |
| Brain 1 | 50 (15 of them today) | 28 | 1.8 : 1 |
| **Brain 3 — `graphify query`** | ~~1~~ **RETRACTED** — see below | rebuilt every commit | **unproven** |

**Control status of each row.** Brain 2's 469 was calibrated afterwards against a known positive (it
correctly finds the 43 reads made in the calibrating session) — **that number holds**. Brain 1's and
memory's were not calibrated and should be read as lower bounds. Brain 3's was calibrated and
**failed**.

### 🔴 RETRACTION — the Brain 3 number in this table is not trustworthy

The row above said Brain 3 was **queried once, ever**. **That claim is withdrawn.** It was produced
by an instrument that was never calibrated, and calibrating it later showed it to be blind.

The correction chain, worth keeping in full because each step looked right at the time:

1. **First measurement: 555 queries.** Wrong — it matched the instruction string `graphify query`
   inside `CLAUDE.md`, which loads into *every* session. It counted the instruction, not the action.
2. **Second measurement: 1 query.** Narrowed to `"command":"…graphify…query"`, i.e. inside a tool
   call. Reported as fact in this document.
3. **Calibration, run afterwards on a known positive:** I had run **at least 12** queries earlier the
   same day (the ten-question benchmark in §6, plus two by hand). The pattern found **2**.
   The benchmark drove `graphify` through a Python `subprocess`, so those ten never appeared as a
   shell command anywhere in the transcript. **The instrument cannot see script-driven use.**
4. And `tools/scan_sessions.py` **does** invoke graphify programmatically — so script-driven use is
   not hypothetical in this repo.

**What can honestly be said:** direct shell invocations of `graphify query` across all transcripts
number **2**. Script-driven invocations are **not countable by this method**. The raw string appears
**937** times, almost all of it instruction text. Whether Brain 3 was under-used before today is
therefore *unproven* — the §6 finding that stands is the benchmark (6/10 by question shape) and the
broken documented command, both measured directly rather than inferred.

> **A count is only as good as its control.** Any number in this document derived from grepping
> transcripts should be treated as a lower bound until it has been run against a case whose answer
> is already known.

See §10 for the six instrument failures of 2026-08-17 and the rule that would have caught all of them.

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

### 6a. Brain 3 was never the broken part — correcting an error in this audit

The owner recalled Graphify being built repeatedly and working. **He was right, and my first reading
of the multi-project picture was wrong twice.** Verified:

| Project | Nodes | Graph date | Last commit | post-commit hook |
|---|---|---|---|---|
| linkdin automation | 1,541 | 2026-08-17 | 2026-08-17 | INSTALLED |
| football automation | 1,193 | 2026-06-16 | 2026-06-16 | INSTALLED |
| youtube automation | 639 | 2026-05-30 | 2026-05-30 | INSTALLED |
| PrivateCloud | — | 2026-06-09 | 2026-06-05 | INSTALLED |

I had claimed (a) only this project had the hooks installed and (b) the other graphs were "stale
traps describing two-month-old code". **Both false.** Hooks are installed in all four, and every
graph matches its repo's last commit **to the day** — those projects are dormant, so their maps are
exactly as fresh as their code. That is the system working correctly.

> **"Old" and "stale" are different claims.** A derived artifact that matches its source is current
> no matter what its timestamp says. Comparing the artifact's date to *today* asks the wrong
> question; compare it to the **source's** date.

The genuine Brain 3 defects remain the three above: the wrong command in the docs, the 6/10 hit rate
by question shape, and the absence of an "I don't know" signal. Freshness was never one of them.

---

## 7. The token ledger

**Every row below was confirmed by asking a fresh `claude -p` session what it actually held** — not
by measuring files on disk. That distinction mattered: it revealed that `rules/python` sits in the
loaded folder and is **never loaded**, so an earlier version of this table counted 383 words that
were not there.

| Always-on, every session | words | ~tokens | in a fresh session? |
|---|---|---|---|
| project `CLAUDE.md` | 3,054 | 4,072 | ✅ confirmed |
| `rules/common` (12 files) | 3,335 | 4,447 | ✅ confirmed |
| `MEMORY.md` index (65 entries) | 1,552 | 2,069 | ✅ confirmed |
| global `CLAUDE.md` | 1,321 | 1,761 | ✅ confirmed |
| `brain1-patterns` hook (48 notes) | 1,132 | 1,509 | ✅ confirmed |
| `rules/python` | 383 | 511 | ❌ **on disk, never loaded** |
| **TOTAL** | **10,394** | **~13,858** | |

| | words | tokens |
|---|---|---|
| Start of 2026-08-17 | 17,819 | ~23,700 |
| End of 2026-08-17 | **10,394** | **~13,858** |
| **Cut** | **7,425 (42%)** | **~9,842** |

Where it came from: **24 changelog entries** out of `CLAUDE.md` (−7,600 words) · **`rules/zh`**, a
Chinese translation of `rules/common` with 10 identical filenames (−1,071) · **`rules/web`**, React /
Tailwind / GSAP / Core Web Vitals against a frontend of 4 HTML + 5 JS + 2 CSS files with no build
step (−1,862) · **`CLAUDE.md`'s duplicated Content Hub block** (−30 lines) · global `CLAUDE.md`
justifications moved into the vault note the hook already surfaces (−330). Paid back: the
`brain1-patterns` hook (+1,132).

Both rule sets were **moved, not deleted**, to `~/.claude/rules-disabled/` with the evidence
recorded. One `mv` restores either. A fresh session confirms both are now absent.

⚠️ **The hook still fires on the five standalone scheduled tasks**, which read Brain 1 zero times.
`pipeline.cmd` and `pipeline-free.cmd` set `CLAUDE_UNATTENDED=1` and are gated; the five per-step
runners call their `.ps1` directly and would need an edit to Claude-stack files — see §8.

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

---

## 10. Six instrument failures in one day, and the single rule that catches all of them

The owner's question: *why did the measuring tools keep giving wrong answers, and how do we fix it?*
It is the most important finding here, because every conclusion in this document depends on them.

### The six

| # | What I measured | What it said | Truth | Why it lied |
|---|---|---|---|---|
| 1 | Brain 3 queries | **555** | 2 direct | matched the *instruction* string in `CLAUDE.md`, loaded every session |
| 2 | Brain 3 queries, take 2 | **1** | ≥12 that day | blind to `subprocess`-driven calls; only sees shell commands |
| 3 | Brain 2 reads | **0** | 469 | JSON escapes the separator as `\`; `docs.knowledge` cannot match `docs\knowledge` |
| 4 | Brain 2 stale paths | 3 files | **1** | 2 were *before/after tables documenting the move*; a path matcher cannot tell "is here" from "used to be here" |
| 5 | Is the new hook working? | broken | working | PowerShell pipes **UTF-16** to Node; `JSON.parse` failed and the hook exited 0 in silence |
| 6 | Line counts on 3 files | 76 / 2650 / 262 | 99 / 3325 / 311 | `Measure-Object -Line` disagrees with `wc -l`; briefly looked like 675 archived lines had vanished |
| 7 | Do these 5 facts exist elsewhere? | 2 exist nowhere | all 5 exist | grep was case-sensitive **and** scoped to `docs/knowledge/`, excluding `CLAUDE.md` |

Plus one shell bug: `ls "…/AZAM RIZWAN/…"/*.md \| xargs basename` split on the space in the username
and reported **49 phantom orphans** in the pattern index.

### The one shape they share

Not carelessness, and not seven unrelated bugs. **Every one was a proxy trusted without a control.**

I ran a check, got a plausible number, and reported it. No step in between asked *"does this
instrument find a case whose answer I already know?"*

Four sub-causes, useful because each has a different tell:

- **Mention vs action** (#1, #4). The searched string appears in both the instruction and the deed. A
  count of *mentions* is not a count of *uses*.
- **Forgotten encoding** (#3, #5). JSON escapes backslashes; PowerShell pipes UTF-16 to native
  programs. The data was not the shape the pattern assumed.
- **Two tools disagreeing** (#6). I believed the first one.
- **Silently narrowed scope** (#2, #7). Case sensitivity, one directory, one invocation form — then
  absence treated as proof.

### Why it happened *today* specifically

Normal work is *write code, run tests*. **Tests are self-calibrating**: you watch them fail before
they pass, so a test that cannot detect the thing announces itself in the red phase.

Today was forensic measurement — roughly fifteen one-off greps and throwaway scripts. **Ad-hoc
measurement has no red phase.** Nothing ever demonstrates that the instrument can see anything at
all, so a blind instrument returns a confident zero and reads as a finding.

That is the same structure as [[05-decisions]] D52 (a selector that matched nothing, reporting "not
connected") and D35 (a channel nobody read, reporting "no replies"). **The failure mode this project
keeps meeting is not error — it is confident, plausible silence.**

### The rule

> **Before trusting a measurement, run it against a case whose answer you already know.**
> Then state the control next to the number.

Concretely, each of the seven would have been caught in one extra step:

- Counting queries → first confirm it finds the query you ran ten minutes ago
- "Zero Brain 2 reads" → first confirm it finds the file you opened at session start
- "The hook is broken" → first confirm your harness delivers parseable input (echo it)
- An alarming line count → get it a second way before reporting a loss
- "Exists nowhere else" → first confirm the search finds it where you *know* it is

**This rule already existed, and where it lived is the point.** `calibrate-a-proxy-on-a-known-positive`
and `the-instrument-can-be-the-bug` are **Claude memories** (`~/.claude/projects/*/memory/`), written
2026-08-13/14 — which means their one-line summaries were in the auto-injected index **all day**, and
they still did not fire. The principle is now also in the vault, as the measurement half of
`wrong-probe-gives-a-confident-negative`, with all seven of today's cases and a second index entry
keyed to *"my measurement says something alarming"*.

Deliberately **not** a new note: the finding half and the counting half are one principle, and
splitting them would create the same duplicate-under-a-different-name failure §4 is about.

⚠️ And a correction inside the correction: the first draft of this section said those were *vault*
notes. They were not. **Even writing up an instrument failure, I asserted a location without checking
it.** That is the eighth one.

### What is enforceable, and what is not

**Not enforceable by a hook.** No script can tell whether a number was calibrated; that is reasoning,
not syntax.

**Enforceable by convention, and cheap:**

1. **Never report a count without naming its control.** "469 reads (control: finds the 3 I made this
   session)" is auditable. "469 reads" is a claim.
2. **Prefer structure over prose.** Count JSON fields, not words that appear in sentences.
3. **Prefer Python to shell for anything with a path** — the username contains a space, and that has
   now broken three separate scripts.
4. **When two tools disagree about a number, neither is right until a third agrees.**
5. **For the recurring case** — counting tool usage across transcripts — write it once, correctly,
   with a built-in self-test, instead of re-deriving a grep each time.

---

## 11. Verified from outside, and what is still unproven

### What a fresh session confirmed

The owner asked whether any of this survives into a **new** session, given every test so far had been
run by the person who built it, in the session that built it. Three genuinely separate `claude -p`
processes were spawned and asked what they had received:

| Claim | Fresh session reported |
|---|---|
| Brain 1 index injected | `BRAIN1_BLOCK=yes NOTES=48` + the first trigger quoted back |
| `rules/zh` removed | `CHINESE_RULES=no` |
| `rules/web` removed | `WEB_RULES=no` |
| the snapshot rule is live | `SNAPSHOT_RULE=yes` |
| the Graphify command is fixed | quoted `py -3 -m graphify query "<question>" --budget 2000` |
| vault auto-backup | **two commits appeared at 17:31 and 17:32** — exactly when those sessions ended |
| `rules/python` loaded | **`no`** — corrected the token ledger in §7 |

That last row is the value of the exercise: **the only way to know what is in a session's context is
to ask a session.** Measuring the filesystem measures the wrong thing.

### The `/update-brains` skill

`~/.claude/skills/update-brains/` — a 514-word SKILL.md (loaded only on invoke) wrapping a 237-line
script that is **executed, never read into context**. Always-on cost: **zero**.

It exists because four of the five failures on 2026-08-17 were mechanical: a missed duplicate, a
missing index line, unverified links, an unpushed vault. `brains.py` enforces all four. The fifth —
*is this lesson cross-project?* — stays a judgement, asked out loud in the skill.

Its duplicate check matches on **claim, not filename**, and was calibrated on three controls
including a true negative. **On its first real run it immediately caught two defects created earlier
the same day**: `36-state-archive` written but never indexed, and a broken `[[file]]` link.
A tool that finds a fault in its author's work on first use has earned its place.

### 🔴 Three things this audit does NOT establish

1. **The duplicate guard is skippable.** The skill only runs when invoked. A note written mid-flow
   bypasses it entirely — which is exactly how the two duplicates were written. A `PreToolUse` hook
   blocking writes into `Patterns/` above ~70% similarity would close it; deliberately not built,
   because the underlying behaviour was changed hours ago and a guard against a possibly-fixed
   behaviour is a guess.
2. **Nothing here proves the notes will be *read*.** Fresh sessions proved the index is *present*.
   Presence is mechanical; use is behavioural, and three months of evidence says these notes get
   written and not opened. One day of fixes does not overturn that.
3. **The Brain 3 benchmark is self-graded.** Ten questions written by me, scored by me. 6/10 is an
   indication, not a finding.

**Gaps 2 and 3 have the same fix, and it is not an argument — it is instrumentation.** A
`PostToolUse` logger appending one line per event (`READ_PATTERN`, `GRAPHIFY <q> → next tool`,
`DUPLICATE_HIT`, `SKILL`) costs nothing in context and turns both questions into measurements a week
from now. For Brain 3 it is also the unbiased test: after a query, was the named file read, or did a
broad grep follow?

Until that data exists, the honest summary is: **the plumbing is verified, the behaviour is not.**
