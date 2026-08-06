# `profile/` — your personal dossier (NOT in this public repo)

This directory is the **single source of truth** every generated CV, cover letter, and recruiter
message draws from. It is **gitignored on purpose**: it holds real personal data (contact details,
date of birth, salary expectations, education records).

Only two files here are tracked — this README and the answer-bank template.

## What you create locally

| File | What it holds | Used by |
|---|---|---|
| `master-profile.md` | Identity, skills, the metrics bank, positioning angles | `cv-architect` skill |
| `projects-catalog.md` | Every project: stack, key facts, quantified outcomes, which roles it supports | `cv-architect` skill |
| `application-answers.json` | **The answer bank** — the only legal source of form values | the form filler |

Copy `application-answers.example.json` → `application-answers.json` and fill it in.

## The two rules that make this safe

**1. Never invent — for CVs.**
Everything a generated CV claims must trace back to a fact recorded here. Reframe emphasis per
target role; never fabricate a skill, a metric, or a job. A CV that overstates gets found out in
the interview, and the cost lands on a real person.

**2. Never invent — for forms.**
The form filler may only type values that exist in `application-answers.json`. Any field whose
value is `null` is left **blank** and reported. A guessed notice period or salary is a false
statement sent to a real company under your name.

> **Blank beats wrong. Skip beats invent.**

## Keeping it current

Refresh the dossier whenever new work ships (`gh repo list`, new notes). Stale facts here become
stale claims in front of a recruiter — the one place in this pipeline where being out of date has
a real cost.
