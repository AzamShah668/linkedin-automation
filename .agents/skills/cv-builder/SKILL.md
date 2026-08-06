---
name: cv-builder
description: RETIRED — merged into the canonical `cv-architect` skill (2026-07-25). Do not use.
---

# cv-builder — RETIRED (merged into `cv-architect`)

This skill was consolidated into **`cv-architect`** (`.claude/skills/cv-architect/`) on 2026-07-25 —
the single canonical CV engine. See decision **D9** in `docs/knowledge/05-decisions.md`.

**Why:** two CV engines had diverged. `cv-builder` held the real content (Azam's master CV + the approved
OSS-framing/contact corrections) but lived in `.agents/skills/`, which is **not a registered/invokable
skill**. `cv-architect` was the invokable one but lacked the master CV. We merged into `cv-architect`.

**Where its content went:**
- Master CV (source of truth) → `.claude/skills/cv-architect/references/master-cv.md`
- Proven Azam HTML template → `.claude/skills/cv-architect/assets/cv-template-azam.html`
- Approved corrections (OSS framed as contributor-level, canonical contact) → live in the master CV above
  and `output/cv/achievement-bank.md`.

➡ **Use `cv-architect` for all CV work.** This folder is kept only as a tombstone pointer.
