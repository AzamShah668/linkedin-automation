# Handoff — Phase 0 kickoff prompt

Paste the block below into a **fresh Claude Code session** opened in `d:\linkdin automation`.

It is written to be token-cheap: it names the exact files to read, tells the model to **stop reading**
after them, and inlines the facts that would otherwise cost an exploration pass to rediscover.

Branch discipline: `main` is the published, working system — **it must not change.** All Phase 0 work
happens on `rewrite/phase-0`.

---

```
Work ONLY on branch `rewrite/phase-0`. Never commit to `main` or `master` — `main` is the published
working system and is our rollback point. Confirm the branch with `git branch --show-current` first.

READ EXACTLY THESE FIVE THINGS, THEN STOP READING AND START WRITING:
1. README.md                                       — what this project is
2. docs/knowledge/22-rewrite-architecture.md       — the plan. Sections 5, 6, 7 are the spec.
3. docs/knowledge/17-auto-apply-runbook.md         — the form rules. Every rule here was learned by
                                                     breaking something in production; keep all of them.
4. profile/application-answers.json                — the real answer bank (gitignored, local only)
5. tools/post_creator/playwright_linkedin_poster.py — a WORKING Playwright-library script for LinkedIn
                                                     in this exact environment. Copy its patterns.

Do not read the rest of docs/knowledge/ unless one of the five leaves you with a real question.
Do not read tools/*.ps1 — that is the old stack we are replacing.

BUILD: apps/autopilot/ — Phase 0 only.

  llm.py   One function: ask(prompt, max_tokens) -> str.
           Provider from env: LLM_PROVIDER (openrouter|anthropic), LLM_BASE_URL, LLM_API_KEY, LLM_MODEL.
           OpenRouter/OmniRouter path uses the OpenAI-compatible client.
           MUST raise a clear error if the response has no choices — free providers return empty
           responses and the resulting crash prints nothing (measured 2026-07-29).

  fill.py  Open a LinkedIn Easy Apply job, fill the form from the answer bank, STOP BEFORE SUBMIT,
           screenshot, print elapsed seconds.

           - Playwright LIBRARY, sync API. NOT the Playwright MCP. No screenshots-as-input, no vision.
           - launch_persistent_context(user_data_dir=".pw_browser") so the LinkedIn login persists.
             If it lands on a sign-in page: STOP the whole run, report "linkedin-logged-out".
             NEVER attempt a login — that is what gets accounts restricted.
           - Find fields with get_by_label / get_by_role. Let Playwright auto-wait; do not poll.
           - Map each field to a key in the answer bank via a FIELD_MAP dict.
               known            -> fill from the bank
               unknown+optional -> leave blank
               unknown+required -> ONE llm.ask() call with just the question text; if it returns
                                   null/empty, abort THIS job and log the field name. Never guess.
           - Easy Apply is a multi-step wizard: contact -> resume -> questions -> review -> submit.
             Loop the steps; click Next; re-scan each new step.

  run.py   CLI: `py -3 -m apps.autopilot.run fill --url <job-url>` and `--urls-file <file>`.

THE ONE HARD RULE (from 17-auto-apply-runbook.md):
  Only values from the answer bank go into a real employer's form. A null means LEAVE IT BLANK.
  Blank beats wrong. Skip beats invent. A guessed salary is a false statement sent under a real name.
  Exactly one derivation is allowed: how_did_you_hear_about_us -> "LinkedIn".

TRAPS ALREADY PAID FOR — do not rediscover these:
  - LinkedIn numeric inputs REJECT words. Notice period must be "0", not "Immediate".
    Expected CTC must be "840000", not "8.4". Client-side validation silently blocks Next.
  - Once a failing numeric field validates, LinkedIn REVEALS extra questions that were hidden behind
    it. Always re-scan the step after any correction — the first scan is never the full picture.
  - India vs international salary differ ~40x. Wrong one = instant auto-reject. If the employer's
    country is unclear, use the India figure.
  - The resume slot pre-fills with whatever was uploaded last — almost always the wrong CV. Phase 0
    does not submit, so just verify which filename is shown and print it.

PHASE 0 IS DELIBERATELY INCOMPLETE. Do NOT build: submitting, the database, the job queue, cv.py,
discovery, Notion/Slack writes. Those are Phases 1-5 in 22-rewrite-architecture.md section 7.

SUCCESS TEST — this is the whole point of Phase 0:
  5 job URLs filled in under 3 minutes total, with zero invented values.
  Print per-job elapsed time and a total. If it misses 3 minutes, say so plainly and tell me where
  the time went — do not quietly move on to Phase 1.

PUBLIC REPO — this repo is public at github.com/AzamShah668/linkedin-automation:
  - NEVER commit a real recruiter's name, email, or LinkedIn URL. They are `Recruiter-A/B/C` in docs.
  - output/ and profile/ are gitignored. Keep it that way. Check `git status` before every commit.

WORKING STYLE:
  - Answer me in short, plain bullet points. No long paragraphs.
  - Judge a run by its log and its artifacts, never by an exit code — exit 0 proves nothing here.
  - If something fails, check the boring shared cause first (a lock, a quota, a battery setting)
    before any clever structural theory. We lost a day to that on 2026-08-01.

Start by confirming the branch, then read the five files, then show me your plan for fill.py before
you write it.
```

---

## Why the prompt is shaped this way

| Choice | Reason |
|---|---|
| Names five files and says **stop** | A fresh session's biggest token cost is exploration. This removes it. |
| Inlines the numeric-field / hidden-question traps | Cheaper than making it read and infer them; also guarantees they survive. |
| Points at `playwright_linkedin_poster.py` | A working precedent in this exact environment beats any explanation. |
| States what **not** to build | Scope creep is the main risk once an agent has momentum. |
| Puts the success test in the prompt | Gives it a falsifiable target, so it can't declare victory vaguely. |
| Repeats the public-repo rule | The one mistake here is irreversible. |

## After Phase 0 passes

Next session's prompt is the same shape, pointing at section 7 of `22-rewrite-architecture.md`:
Phase 1 (own the data — kills D23) then Phase 2 (job queue — kills D20). Do not skip ahead; each
phase's success test is what makes the next one safe.
