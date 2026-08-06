# Achievement Mining — build the verified evidence bank

A great CV is assembled from a **bank of real, quantified, sourced achievements**, then tailored per
role. Build the bank once; reuse and re-order it forever. Every entry must be traceable — no invention.

## Where to mine (in order)

1. **GitHub** — `gh repo list <user> --limit 100` then per repo: README, languages, file/dir counts,
   CI configs (`.github/workflows`, `Jenkinsfile`), Dockerfiles, k8s manifests, test dirs. Counts are
   gold: "N services", "N tests", "N playbooks", "N tools".
2. **Brain 1 (Obsidian `Projects/`)** — the *why* and the crisp framings the person already wrote.
3. **Brain 2 (`docs/knowledge/`)** — decisions, architecture, debugging journals (root-cause stories
   make strong interview talking points and honest bullets).
4. **Person's input / existing CV** — fill gaps, confirm dates, get preferences.

## Entry format (store in `output/cv/achievement-bank.md`)

```
### <Short title>
- Metric: <the number/scale>            (e.g. 98 passing tests; 7-service stack; 1,103-node codebase)
- What: <one-line what was built>
- Tech: <the real stack>
- Outcome: <why it mattered>
- Source: <repo URL / brain note>       ← proof it's real
- Reframes-to: <roles this supports>    ← e.g. DevOps, MLOps, Backend
```

## Turning evidence into bullets

- Lead with the **metric or outcome**, then the mechanism.
- Prefer counts you can defend in an interview. If unsure, use a safe lower bound ("15+ playbooks").
- Reframe honestly for the target role: the *same* project yields a DevOps bullet (CI/CD, IaC,
  containers) or an MLOps bullet (quality gates, GPU scheduling, experiment tracking) depending on
  which real facet you foreground.

## Honesty guardrails

- Never state a number you can't point to a source for.
- "Contributed to" ≠ "built" — match the verb to the real role.
- Reframing = choosing which true facet to emphasize. Inventing scope, metrics, or tools is off-limits
  and collapses in interviews.
