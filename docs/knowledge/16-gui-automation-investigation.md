# 16 — GUI Automation Investigation (desktop-agent as the autopilot's hands)

Back to [[00-INDEX]]. Siblings: [[12-approved-send-runbook]], [[13-accept-watch-runbook]], [[15-build-packet-runbook]].

**Date: 2026-07-29.** The owner asked for full autonomy: find ~10 jobs, build the CVs, and have a
screen-control agent fill and submit the application forms and drive LinkedIn outreach — no human tick.
This file records what was measured, what was built, what broke, and the one thing still blocking it.

The agent in question is a **separate project**: `d:\New folder (2)\desktop-agent` (Brain 1 page
`Projects/desktop-agent.md`). It screenshots the screen, a vision model returns one JSON action, a safety
gate runs, pyautogui executes, repeat.

## Verdict in one line

The architecture works and the accuracy problem is **solved**; the blocker is that **no model backend on
this machine can currently reach an API**. Nothing in the pipeline code is at fault.

---

## 1. Free OpenRouter models cannot do GUI control — measured, not assumed

The owner wanted to run everything on a free OpenRouter key. Benchmarked all 4 usable free vision models
(there are only 8 free+vision models on OpenRouter at all) on **the easiest possible GUI task**: click the
Windows Start button — a large, fixed, famous target.

| Model | Hits | Hard errors | Avg latency |
|---|---|---|---|
| nvidia/nemotron-nano-12b-v2-vl:free | 0/2 | 1 (provider returned no `choices`) | 65s |
| google/gemma-4-26b-a4b-it:free | 1/2 | 1 | 11s |
| google/gemma-4-31b-it:free | 0/2 | 1 (429 upstream) | 9s |
| openrouter/free | 1/2 | 0 | 14s |

**The two "hits" were not hits.** Both answered x=15–18 (bottom-left). The Start button was at **x≈344** —
the taskbar is centred on Windows 11. They only passed a loose y-band test. **Real success: 0 of 8.**

Other failure modes seen: `y=975` returned for a **720px-tall** image (coordinates hallucinated in the
real-screen space, not the image space), and `click_element` chosen when element grounding was switched
off, leaving `element: null`.

Also found: the OpenRouter account is `is_free_tier: true` and **out of credit** — a paid call returns
`402 … you requested 1024 tokens but can only afford 488`. And `ANTHROPIC_API_KEY` is empty.

## 2. The root cause of every failure: raw coordinate regression

Not the model. Not OpenRouter. **`USE_GROUNDING=false`**, which forces the model to guess pixel coordinates.

This is the hardest thing for a vision model and small ones collapse at it — but so did the big one.
Claude, asked the same question, answered **x=16 when the truth was x≈344** (a 328px miss), reasoning
*"in a 1280x720 layout the Start button is at the far-left, roughly x=16"* — i.e. from convention, not from
looking. Asked directly, it then replied *"no taskbar is present in the image"* while looking at a
screenshot with a taskbar plainly across the bottom.

Swapping brains does not fix this. **Every brain fails the same way.**

## 3. The fix: UIA grounding (already in the codebase, switched off)

`USE_GROUNDING=true` turns on `grounding.py` — Windows UI Automation + Set-of-Marks. The screen's real
controls are enumerated and numbered; the model picks *"element 7"*; the agent clicks that element's true
rectangle centre. **Screenshot-downscaling error stops existing.**

Verified live:
```
[7]  MenuItemControl   File      rect=(43,0)-(89,43)
[13] MenuItemControl   Terminal  rect=(363,0)-(445,43)
```
Asked to click the File menu → returned `click_element element=7`. **Correct, first try, 13.6s.** The same
brain had missed the Start button by 328px seconds earlier without grounding.

The desktop-agent's own `pending-work.md` had listed this as priority #2 the whole time.

**Chrome caveat, still open:** Chrome does expose UIA — 3 elements were read from a Chrome dialog. But
those were **native browser chrome, not web page content**. Whether *form fields inside a webpage* are
enumerable is **unproven** and is the one remaining technical unknown for job-form filling.

## 4. What was built

| File | Purpose |
|---|---|
| `desktop-agent/brains/claude_code_brain.py` | **NEW backend** — shells out to the local `claude` CLI, so it needs no API key and no metered credit |
| `desktop-agent/apply_to_job.py` | Open a job URL, fill the form, **never submit** |
| `desktop-agent/diagnose_brain.py` | 4 escalating checks; the first failure names the cause |
| `profile/application-answers.json` | The answer bank (see below) |

### The answer bank — the rule that makes autonomy safe
`profile/application-answers.json` holds the **only** values the agent may type into a real employer's
form. Twelve fields are deliberately `null` (years with Python/Docker/K8s/AWS/Linux, DOB, gender, CGPA,
passport, reason for change, how-did-you-hear). If a form asks for one of those, the agent **leaves it
blank and reports it** rather than inventing. A guessed notice period or salary is a false statement sent
to a real company under Azam's name.

**Salary, resolved 2026-07-29:** the owner first said *"70K per month rupees, if in dollars 30K$ per
month"* — those differ by ~40×. Clarified to **two deliberate figures**: `8.4 LPA` (₹70,000/month) for
Indian employers, `$30,000/year` for remote/international (`--international` flag). Current CTC: `0`,
fresher. Caught before it reached a form; a wrong number there is an instant auto-reject.

## 5. Three real bugs found and fixed in desktop-agent

1. **The agent destroyed its own error messages.** `session.py` printed emoji status icons to a cp1252
   Windows console → `UnicodeEncodeError` **raised inside the error handler**, then again in the nested
   handler. Every real failure was lost. Fixed by reconfiguring stdout/stderr to UTF-8 with replacement.
2. **Screenshots were unreadable by the brain.** They were written to `%TEMP%`; the `claude` CLI may only
   Read inside its working directory, so every call returned *"the Read tool was denied permission"* and
   the model correctly refused to act. Fixed: write to `<repo>/.agent_shots/` and pass `cwd=REPO_ROOT`.
3. **Failures reported nothing.** The brain surfaced only `stderr`, but Claude Code prints its errors to
   **stdout** — producing a bare `claude CLI exited 1:` with nothing after the colon. **This hid the real
   cause for two entire runs.** Fixed: report both streams plus the prompt length. Timeout also raised
   180s → 420s (`CLAUDE_CODE_BRAIN_TIMEOUT`).

## 6. The blocker: the standalone Claude CLI cannot reach the API

After the fixes, runs failed with `API Error: Unable to connect to API (ConnectionRefused)`.

**It is not the `-p` path and not our code** — typing `hi` into an *interactive* `claude` in the same
PowerShell fails identically (`Retrying in 7s · attempt 5/10`).

Ruled out, all checked: no proxy (`netsh winhttp` = direct), no `HTTP(S)_PROXY`, no `ANTHROPIC_BASE_URL`,
no hosts-file entry, no `sandbox.*` settings, DNS resolves (`160.79.104.10` / `2607:6bc0::10`), and
**TCP 443 connects successfully**. The OS network is clean.

**The decisive asymmetry:** the identical brain call succeeds in **18.9s** when spawned from inside a
Claude Code session, and fails from a plain PowerShell. A nested call inherits `CLAUDECODE=1`,
`CLAUDE_CODE_CHILD_SESSION=1`, `CLAUDE_CODE_ENTRYPOINT=claude-vscode` and rides the parent's established
connection. A top-level shell has none of that and must connect on its own — and cannot.

Untested idea (one line, free): the API resolves IPv6-first; Node can mishandle that on Windows —
`$env:NODE_OPTIONS="--dns-result-order=ipv4first"` before running.

**Consequence:** the `claude_code` brain only works when launched from inside a Claude Code session, which
defeats unattended use. Until the CLI connects standalone, the practical route is **~$10 of OpenRouter
credit** plus `AGENT_BACKEND=openrouter`, `OPENROUTER_MODEL=anthropic/claude-sonnet-4.5` (≈$0.50 per
application). The architecture is proven; only the model connection is missing.

## 7. Lessons worth keeping

- **Never conclude "the code is broken" from a failure in one shell.** The same call passed in one context
  and timed out in another. Reproduce in both before diagnosing.
- **An error handler that can crash is worse than no error handler** — it deletes the evidence.
- **Report every stream on failure.** Two runs were wasted because stdout was discarded.
- **Grounding beats a better model.** Element selection turned a 328px miss into a first-try hit; no model
  upgrade would have done that.
- **A vision agent that can see a problem will still act wrongly.** During the Notepad test the model wrote
  *"the active window appears to be a code editor/IDE"* and typed anyway — three times, into an open
  document (unsaved buffer, no file touched, cleared with Ctrl+Z). Seeing ≠ acting correctly.
