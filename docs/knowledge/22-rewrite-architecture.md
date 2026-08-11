# 22 — The rewrite: agent-as-tool, not agent-as-runtime

Back to [[00-INDEX]]. **Decided 2026-08-06.** This is the plan for what the project becomes next.
Read it after [[07-current-state]]. Decisions behind it: [[05-decisions]] **D26, D27, D28**.

> **If you are an AI or a person picking this repo up cold, read this file second (after the root
> `README.md`). It explains why the code looks the way it does and what it is being changed into.**

---

## 1. The problem, in one sentence

**We used Claude Code — an interactive IDE tool — as the production runtime.**

Every pipeline step spawns a full Claude Code session, which reads a Markdown runbook and makes
~20 MCP calls to do work that is 90% identical every time.

That single choice caused almost every bug in [[05-decisions]]:

| Symptom we logged | Real cause |
|---|---|
| D24 → D25: "one PowerShell layer too many", then "no, it was a usage limit" | A coding agent has **session limits**. A server does not. |
| D13: four LinkedIn MCP servers fighting over one browser profile | An interactive tool assumes **one user at one keyboard** |
| D20: five missed tasks firing within three seconds on wake | Task Scheduler is **not a job queue** |
| D17: one `hasTrustDialogAccepted` boolean silently voided 55 permissions | A permission system designed for **a human approver who is present** |
| 16 minutes to build one packet | A full agent loop for work that is mostly **templating** |
| Playwright MCP is slow | **Screenshot → vision → decide**, on every single step |

None of these are bugs in our code. They are the cost of running an IDE as a server.

### The corollary that took two days to learn

We twice diagnosed a *clever* cause when the real one was mundane (D24, then D25 correcting it).
Both times the giveaway was in a child process's log, not the runner's summary. **When several
unrelated things fail at once, check the boring shared resource first** — a usage limit, a lock, a
battery setting.

---

## 2. The rule everything follows from

> **Anything that is the same every time → code.**
> **Anything that is different every time → AI.**

Applied to a LinkedIn Easy Apply form — the pipeline's most-repeated task:

| Fields | Example | Needs a brain? |
|---|---|---|
| 1–19 | name, email, phone, notice period, expected CTC, relocate, work auth, résumé upload | ❌ **No** — a dictionary lookup |
| 20 | *"Why do you want to join us?"* | ✅ **Yes** |

Today an agent does all twenty. **We pay a frontier model to type a name, twenty times, for sixteen
minutes.** The rewrite gives it field 20 and nothing else.

### Why this is mostly about reliability, not tokens

Cost is the smallest win. Ranked:

1. **Reliability** — code *always* types the right value; a model *usually* does.
2. **Speed** — 16 minutes → seconds.
3. **Portability** — it can run for someone other than the owner (the eventual product).
4. Cost.

Proof from our own rules: [[17-auto-apply-runbook]] contains *"Never invent a value. Blank beats
wrong. Skip beats invent."* **That rule exists because a model might improvise on a real employer's
form.** Replace the worker with a dict lookup and the failure mode ceases to exist. We wrote rules
to police a worker who could improvise; code cannot improvise.

---

## 3. Three different things are called "Claude"

The confusion that kept the old design in place. Only #3 belongs in a runtime.

| # | Name | What it is | Right job |
|---|---|---|---|
| 1 | **Claude Code** (CLI / IDE) | A coding assistant in your editor | Building the app; the CV step (see §5) |
| 2 | **Claude Code cloud / routines** | The same tool, on someone else's machine, on a timer | Chores that touch **no local files** |
| 3 | **Claude API** | A function your own program calls | **Production** |

Moving #1 → #2 (cloud) fixes only *two* of the seven problems in §1 — the sleeping laptop and
profile contention. It does not fix session limits, speed, or portability, and it makes local files
**worse**: a cloud agent cannot attach `output/pdf/<cv>.pdf`, which we already learned the hard way
with Composio ([[cloud-tools-cannot-touch-local-files]] / [[20-first-email-batch-and-task-verification]]).

**Cloud is a patch for one symptom. The API is the fix for the class.**

---

## 4. What "an agentic framework" actually is

The owner asked what to learn before building one. The answer is that he had already described it:

```
Code that knows the steps  +  an LLM called only for the unclear parts
```

That is the whole definition. An agent loop is about a hundred lines:

```python
while True:
    reply = llm(messages, tools)
    if reply.done:
        break
    result = run_tool(reply.tool, reply.args)
    messages.append(result)
```

CrewAI, LangGraph, AutoGPT are that loop plus vocabulary. **Write it once by hand before adopting a
framework**; after that the frameworks are legible and mostly unnecessary here. CrewAI in particular
is multi-agent role-play — the wrong shape for deterministic form filling.

---

## 5. The chosen architecture (owner's design, 2026-08-06)

The owner proposed the split and it is correct: **free/cheap models for plumbing, Claude Code for
the one artifact a human reads.**

```
Python orchestrator  ──  does everything
        │
        ├── free LLM (via OmniRouter/OpenRouter) → scoring, odd form questions
        ├── plain code                            → discovery, filling, tracking, submitting
        └── Claude Code CLI                       → the tailored CV + cover letter   ⭐
```

### The inversion

This is the entire change. Same components, opposite direction.

| | Today | After |
|---|---|---|
| Top of stack | Task Scheduler → PowerShell → **Claude Code** → everything | **Python** → everything |
| Claude Code is | the runtime | a subprocess called for one step |
| Called | ~50× / day | ~3× / day |
| Doing | typing the owner's name | writing what a recruiter reads |

### Why the CV step keeps Claude Code

CV generation is the one place a full agent session earns its cost:

| | CV writing | Everything else |
|---|---|---|
| Frequency | once per **company** | every application |
| Read by | **a human recruiter** | a form field |
| Latency-sensitive | **no** (built ahead, offline) | yes |
| Needs judgment | **yes** — read the JD, check `profile/` for evidence, refuse to fabricate | no |

Low frequency + high stakes + not urgent = correct place for a slow, expensive, careful tool. And
Claude Code is **already paid for by the owner's subscription**, so the marginal cost is zero.

> **The resulting design costs ₹0/day to run.** Not "free except CVs" — free.

### Model routing

| Task | Engine | Why |
|---|---|---|
| Fetch jobs from ATS boards | plain HTTP | no AI needed at all |
| Score fit 0–100 | free LLM | easy, short, structured output |
| Fetch the job description | plain HTTP | — |
| **Tailored CV + cover letter + ATS score** | **Claude Code** ⭐ | quality-critical, human-read |
| Fill 19 known fields | answer bank (dict) | must be exact |
| One odd screening question | free LLM | easy, short |
| Submit, screenshot, record | plain code | must be exact |

⚠️ **Do not let a free model write the CV.** Free models were measured at an effective **0/8** on the
easiest GUI task ([[16-gui-automation-investigation]]); more relevantly, CV prose is the single
artifact a human judges. Saving a rupee there is the wrong trade. Free models *are* fine for
screening questions — that is a much easier task, and the 0/8 result was about **pixel-coordinate
regression**, not text.

### Latency, honestly

Using our own measured free-model latencies (65s / 11s / 9s / 14s, avg ≈25s), 10 applications:

| | Browser work | LLM calls | Owner waits |
|---|---|---|---|
| Today (Claude Code runtime) | — | — | **~2.5 hours** |
| Free models + rotation | ~3 min | ~4 min | **~7 min** |
| Paid Haiku | ~3 min | ~15 s | **~3.5 min** |

Free vs paid is 7 minutes vs 3.5. **Both are ~30× better than today.** The win is the architecture,
not the model tier — so start free.

---

## 6. Target structure

```
apps/autopilot/
├── llm.py         # ONE function the whole app calls. Provider is a config value.
├── discover.py    # ATS + board adapters              → 0 AI calls
├── score.py       # fit score vs profile              → 1 free call
├── cv.py          # subprocess → Claude Code CLI      → ⭐ the one smart step
├── fill.py        # Playwright + answer bank          → 0–1 free calls
├── track.py       # DB, status transitions, logging   → 0 AI calls
└── run.py         # the orchestrator / CLI entry point
```

### `llm.py` — why provider choice is not an architecture decision

Everything calls one function, so switching providers is one line in `.env`:

```python
# llm.py
import os

def ask(prompt: str, max_tokens: int = 300) -> str:
    provider = os.getenv("LLM_PROVIDER", "openrouter")

    if provider == "anthropic":
        from anthropic import Anthropic
        r = Anthropic().messages.create(
            model="claude-haiku-4-5", max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return r.content[0].text

    from openai import OpenAI                      # OpenRouter / OmniRouter speak this format
    c = OpenAI(base_url=os.getenv("LLM_BASE_URL"), api_key=os.getenv("LLM_API_KEY"))
    r = c.chat.completions.create(
        model=os.getenv("LLM_MODEL"), max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    if not r.choices:                              # measured 2026-07-29: free providers do this
        raise RuntimeError(f"provider returned no choices: {r}")
    return r.choices[0].message.content
```

**OmniRouter** (the owner's key-rotation layer: many free keys, rotate on rate-limit) plugs in as a
`LLM_BASE_URL`. It genuinely fixes free-tier **rate limits**. It does **not** fix latency, quality,
or silent dropouts — rotating keys gives you *more* calls, not *faster* ones. ⚠️ Rotating multiple
free accounts to bypass limits also violates most providers' terms; fine for one person's job hunt,
**not** a foundation for the paid product (same shape as the LinkedIn-scraping rule in [[05-decisions]] D2).

### `cv.py` — the whole bridge to Claude Code

~20 lines. Reuses `cv-architect`, the runbooks, and the achievement bank **unchanged**:

```python
import subprocess, json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

def build_packet(job_id: str, timeout: int = 1800) -> dict:
    prompt = (f"Read docs/knowledge/15-build-packet-runbook.md and follow it "
              f"for job id {job_id}. Send nothing.")
    r = subprocess.run(["claude", "-p", prompt],
                       cwd=REPO, capture_output=True, text=True, timeout=timeout)

    # D-lesson: Claude Code prints its errors to STDOUT, not stderr. Report both.
    if r.returncode != 0:
        raise RuntimeError(f"packet build failed\nSTDOUT:{r.stdout}\nSTDERR:{r.stderr}")

    # D17: exit 0 proves nothing. Judge by the artifact.
    packet = REPO / "output" / "outreach" / slug_for(job_id) / "packet.json"
    if not packet.exists():
        raise RuntimeError("claude exited 0 but wrote no packet")

    return json.loads(packet.read_text())
```

⚠️ **Port the usage-limit check** from `tools/sweep-packets.ps1`: on *"You've hit your session
limit"*, stop the batch and say so — do **not** record each job as an individual `FAILED` (D25).

---

## 7. Phased plan

> **⚠️ REORDERED 2026-08-06, after Phase 0 closed.** The CV bridge (was Phase 3) now comes
> **before** the database (was Phase 1). Reasoning below — the reorder is recorded, not just done.

| Phase | Goal | Success test | State |
|---|---|---|---|
| **0** | Prove the thesis. `fill.py`: Playwright + answer bank, stop before submit | **5 forms in under 3 minutes** | ✅ **CLOSED** — 5 fills, 72.1s ([[23-phase-0-results]]) |
| **1** ⭐ | `cv.py` → Claude Code. Tailored CV attached and **filename verified** before any submit | a real application carries the CV written for *that* company | ← next |
| **2** | Own the data. SQLite/Postgres + Alembic; Notion becomes a *view*, not the source | the stale-mirror bug (D23) and the wrong-status bug (D29) are structurally impossible | |
| **3** | Real queue (`arq`/RQ + Redis). Idempotency keys; retries; backoff | delete `pipeline-lock.ps1`, `run-pipeline.ps1`, all 6 scheduled tasks | |
| **4** | ATS source adapters (Greenhouse / Lever / Ashby / Workable) | LinkedIn becomes 1 adapter of 5, not the foundation | |
| **5** | Product: FastAPI + Next.js, Stripe, per-user credentials | someone other than the owner can run it | |

### Why the CV bridge jumped the queue (owner's call, 2026-08-06)

Phase 0 succeeded in a way that created a new problem. `fill.py` now completes a form in ~14
seconds — **and attaches whatever CV LinkedIn pre-filled**, which production confirmed is the
generic `azam-shah-devops-cv.pdf` on every job tested ([[23-phase-0-results]] §7).

Speed without the tailored CV is not a partial win, it is the **failure mode this project exists to
avoid**. Submitting a generic CV to ten companies in two minutes is precisely the mass automation
forbidden by the core rule in `CLAUDE.md` and [[05-decisions]] D1/D2 — recruiters bin it, and the
volume is what gets an account restricted. **The faster `fill.py` gets, the more urgent `cv.py`
becomes.**

Against that, the database unblocks nothing a recruiter would ever see. D23 and D29 are real and
the mirror genuinely needs replacing, but both are mitigated today by reconciling before trusting a
status filter, and neither stops an application going out. **Infrastructure that unblocks nothing
user-visible does not outrank the one artifact a human reads.**

So the ordering rule is: *fix what blocks a correct application first; fix what blocks a tidy
codebase after.*

**Phase 0 first, and measure it.** If 5 applications take under 3 minutes, the design is proven and
everything after is plumbing. If it does not, stop and re-diagnose before building more.
*(Done: 72.1s. Three consecutive passes.)*

---

## 8. What is kept vs replaced

**Kept — this is the actual asset:**

- `docs/knowledge/` — 22 documents, 28 decisions. Six weeks of production truth that exists nowhere else.
- `profile/application-answers.json` — the answer bank, and the rule that governs it
- `.claude/skills/cv-architect` + `recruiter-outreach` — called by `cv.py`, unchanged
- `database/board_db.py`, `invite_tracker.py`, `notion_push.py`, `backend/server.py` — real, working logic
- `tools/pipeline-lock.ps1` — an atomic lock debugged in production; its *lessons* migrate even though the file goes

**Replaced:**

- Task Scheduler + the six scheduled tasks → a job queue
- `*.ps1` runners whose only job is `claude -p "read <runbook>"` → Python modules
- Playwright **MCP** (screenshot loop) → the Playwright **library** (DOM selectors)
- Notion-as-source-of-truth → Notion-as-view

**The runbooks do not get deleted — they become the code.** Every rule written in Markdown turns
into a line Python actually executes. That is why this rewrite is faster than it looks: the
specification was written months ago.

---

## 9. What to learn, in order

The owner is not a beginner — he has shipped atomic locks, schedulers, race conditions, and
idempotency. Skip the basics.

| # | Topic | Why it matters here |
|---|---|---|
| 1 | **Playwright as a library** (not the MCP) — `launch_persistent_context`, `get_by_role`, auto-wait | biggest single win; removes the screenshot loop |
| 2 | **Structured LLM output** (JSON schema / tool use) | turns "the agent decides" into "a function returns typed data" |
| 3 | **Hand-write one agent loop** (~100 lines) | demystifies every framework; see §4 |
| 4 | **A real job queue** (`arq` / RQ + Redis) | permanently kills D20 (the wake stampede) |
| 5 | **FastAPI + SQLModel + Alembic** | permanently kills D23 (the stale mirror) |
| 6 | **Structured logging / tracing** | D17 says *judge by the log, never the exit code* — build it in |
| 7 | *(optional)* LangGraph | only if resumable state machines are wanted. **Skip CrewAI.** |

---

## 10. Two constraints that do not go away

1. **LinkedIn forbids automation.** This is why the product plan is **ATS-first** (Greenhouse, Lever,
   Ashby, Workable have public job APIs and ordinary web forms) with LinkedIn as one optional
   adapter running in the user's own browser. The commercial tools that do this are mostly **browser
   extensions** for exactly that reason — the user's own session, no stored credentials, no
   ban-attribution to a central service. See [[05-decisions]] D2.
2. **Claude Code session limits** cap the CV step at roughly **5 packets/day**. Current need is 2–5/day,
   so this is not yet binding — but it is the reason the CV step must fail *loudly* and stop the batch
   rather than mark jobs failed (D25).

---

Related: [[07-current-state]] · [[05-decisions]] D26–D28 · [[02-architecture]] (the older target design,
now superseded by §6) · [[17-auto-apply-runbook]] · [[16-gui-automation-investigation]]
