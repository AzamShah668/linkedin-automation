# Humanization — make it read like a person wrote it

Recruiters (and AI-detectors) increasingly spot LLM-written résumés. They read as generic, evenly
paced, and adjective-heavy. A human-sounding CV is specific, varied, and quietly confident.

## AI-tell blocklist (do not use)

**Verbs/phrases:** leverage(d), spearhead(ed), utilize(d), delve, foster, empower, orchestrate (as
filler), "passionate about", "results-driven", "detail-oriented", "team player", "proven track record",
"dynamic professional", "cutting-edge", "state-of-the-art", "seamless(ly)", "robust solutions",
"in today's fast-paced world", "wear many hats", "think outside the box", "synergy", "holistic".

**Structural tells:**
- Every bullet the same length and shape.
- Every bullet starting with the same 2–3 verbs.
- Triads everywhere ("designed, developed, and delivered").
- Em-dash overuse and identical rhythm in every sentence.
- Vague scale words with no number ("various", "numerous", "several key").

## Humanization rules

1. **Specific beats grand.** Replace "improved system performance" with "cut cold-start from 60s to
   under 8s by lazy-loading models". Real detail is the strongest human signal.
2. **Vary rhythm.** Mix short punchy bullets with one longer explanatory one per role. Not every line
   needs a metric — but the important ones must.
3. **Plain verbs.** built, wrote, shipped, deployed, fixed, cut, automated, debugged, ran, migrated,
   scaled, wired, hardened. Save fancier verbs for where they're literally accurate.
4. **Concrete nouns.** Name the actual tools, numbers, and outcomes. "7-service Docker Compose stack",
   not "a complex containerized architecture".
5. **Own voice in the summary.** One or two sentences that sound like the person. Confident, not salesy.
6. **No pronouns in bullets** ("Built…", not "I built…"), but the summary may read naturally.
7. **Admit the true shape.** A student who's built real systems should say that plainly — authenticity
   reads as honest and lands better than inflated seniority language.

## Before → after

- ❌ "Leveraged cutting-edge containerization to spearhead robust, scalable deployment solutions."
- ✅ "Containerized a 7-service platform with Docker Compose (health checks, named volumes, internal
  networks) behind a single `docker compose up`."

- ❌ "Passionate, results-driven engineer with a proven track record of delivering seamless automation."
- ✅ "Final-year CS student who ships production infrastructure: CI/CD pipelines, Ansible-provisioned
  server stacks, and GPU-scheduled Kubernetes workloads."

## Humanization gate (pass before delivering)

- [ ] Zero blocklist hits.
- [ ] Bullet lengths and opening verbs vary.
- [ ] Every claim is concrete (a real tool, number, or outcome) — no vague filler.
- [ ] Summary sounds like a person, not a brochure.
- [ ] Reads naturally aloud in one pass.
