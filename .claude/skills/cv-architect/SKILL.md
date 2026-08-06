---
name: cv-architect
description: Build a top-tier, ATS-90+, human-sounding CV/résumé grounded in real evidence (GitHub + the three brains), rendered in a clean stat-tile visual style. Use when creating, tailoring, or reviewing a CV/résumé, or generating a per-job tailored application packet (CV + cover letter + recruiter highlight reel).
---

# CV Architect

Produce a résumé that (1) scores **≥90 on ATS parsers**, (2) reads as **written by a human**, not an
LLM, (3) is **grounded in verifiable evidence** (never fabricated), and (4) looks like a designed
document, not a template. This skill is the `tailor/` engine of the Job Hunt Autopilot.

## The four non-negotiable rules

1. **ATS ≥ 90.** Single-column body, standard section names, real fonts, no content in tables/images/
   text-boxes/headers-footers, keyword-matched to the target role. Full checklist: `references/ats-optimization.md`.
2. **Human, not robotic.** No AI-tell vocabulary, no uniform sentence rhythm, specific > generic.
   Run the humanization pass every time. Blocklist + rewrites: `references/humanization.md`.
3. **Zero fabrication.** Every number, tool, and claim traces to real evidence (GitHub repo, Brain 2
   `docs/knowledge/`, Brain 1 Obsidian, or the person's own input). Reframe and emphasize — never invent.
4. **Dual output.** Ship two artifacts from one source of truth:
   - **Visual version** (HTML → PDF) — the designed, stat-tile look, for *human eyes* / direct recruiter email.
   - **ATS-plain version** (`.md`/`.txt`) — parser-clean, for pasting into application forms / ATS uploads.
   Engineer the visual one to *degrade gracefully* (see `references/visual-spec.md`) so it also parses acceptably.
   **Templates in `assets/`:** `cv-template.html` = the reusable, dependency-free, tokenized default (preferred —
   no CDN fonts, ATS-graceful); `cv-template-azam.html` = the proven Azam layout ported from cv-builder (uses a
   Google-Fonts CDN link — self-host or strip it before relying on it offline/ATS).

## Process (run in order)

1. **Gather evidence.** For Azam, the **canonical source of truth is the `profile/` dossier**
   (`profile/master-profile.md` + `profile/projects-catalog.md`) plus `output/cv/achievement-bank.md` — these
   are the deeply-researched, current record and **supersede** the older master CV. Use
   `references/master-cv.md` (the master CV ported from the retired `cv-builder`) as a secondary/legacy
   reference. For anyone else, gather from `gh repo list <user>` + repo READMEs, Brain 1 Obsidian `Projects/`,
   Brain 2 `docs/knowledge/`, and provided notes. Build/refresh the **achievement bank** (verified, quantified
   wins with a source) — see `references/achievement-mining.md`. **Approved framing (always):** OSS =
   *contributor-level* to Everything Claude Code (never personal output); canonical contact =
   azamshah25809@gmail.com / +91 <YOUR-PHONE>.
2. **Position.** Pick ONE primary title (what they're applying for) + 1–2 supporting angles. Everything
   downstream serves that positioning. Reframe off-target work to the role's favor (e.g. a "YouTube
   automation" hobby → "fault-tolerant, self-healing pipeline with CI/CD quality gates").
3. **Tailor to the job.** If a job description is supplied, mine its keywords/requirements and mirror
   the true ones. Order sections and bullets by relevance to THIS role.
4. **Draft.** Use the bullet formula: **`<Action verb> <what you built> <with which tech> → <quantified
   outcome>`**. Lead with impact + numbers. One idea per bullet. No first-person pronouns.
5. **Render both outputs.** Fill `assets/cv-template.html` for the visual version; produce the parallel
   `.md` for the ATS version. Keep them in sync.
6. **Score before delivering (gates).** Self-audit against BOTH rubrics and fix misses:
   - ATS gate: score with `references/ats-optimization.md` → must be ≥90.
   - Humanization gate: score with `references/humanization.md` → zero blocklist hits, varied rhythm.
   Only deliver when both pass. State the scores to the user.

## Bullet quality bar

- ✅ `Built a Jenkins CI/CD pipeline (parallel Docker builds → Docker Hub → SSH deploy with health
  checks) that cut manual release steps to a single push.`
- ❌ `Leveraged cutting-edge CI/CD tools to spearhead seamless deployment solutions.` ← AI-tell, vague, no number.

## Output locations

- Skill assets (reusable, generic): this folder.
- A person's actual CV (project deliverable): `output/cv/<name>-<role>-cv.{md,html}` + their `achievement-bank.md`.

## Tailoring for the Autopilot

For a per-job packet, this skill emits three grounded artifacts: the **tailored CV**, a **cover letter**,
and the **recruiter Highlight Reel** (punchy achievement-led message). All three read from the same
achievement bank and the researched company brief.
