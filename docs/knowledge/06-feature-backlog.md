# 06 — Feature Backlog (confirmed additions)

Back to [[00-INDEX]]. Confirmed with owner **2026-07-25**. Build **after** the CV/portfolio + setup phase
(owner: "we get into it after we are done with this"). All approved.

## Core outreach — the highest-leverage feature (owner's explicit ask)

- **Dual-touch outreach.** For every job, besides submitting the application, send a **personal message to
  the recruiter / hiring manager who posted it** (or the org head), leading with 2–3 achievements matched to
  that exact role (the **Highlight Reel**) + the tailored CV.
  - Find the recruiter via LinkedIn **read-only** search (`search_people` / the job poster). No ban risk.
  - The system **drafts** the message; the **owner sends it** — by hand on LinkedIn, or via email if we have
    the address. **Never auto-DM on LinkedIn** (that's the #1 ban trigger). See [[05-decisions]] D1/D3.

## Confirmed feature additions (all 7 approved)

1. **Warm-intro detection** — flag companies where the owner's connections/alumni already work (the live
   LinkedIn search already surfaced CUK alumni at Oracle and Infosys) → warm intro over cold apply.
2. **Application tracker + daily Slack digest** — status per job (found → applied → viewed → replied →
   interview → closed), pushed to Slack so nothing slips.
3. **Smart follow-ups** — auto-remind to nudge on **Day 3** and **Day 7** if no reply.
4. **Interview-prep generator** — on "interview booked", build company-specific prep (likely questions +
   talking points drawn from the owner's real projects).
5. **LinkedIn profile optimization** — draft a strong headline + summary (current headline is weak:
   *"currently pursuing my BTECH"*); owner pastes it (the LinkedIn MCP has no profile-edit tool).
6. **Response analytics** — track which CVs/messages get replies; double down on winners; A/B message variants.
7. **Calendar integration** — interviews auto-added to Google Calendar (already connected via MCP).

## Notifications

- **Slack** for every event: new match, draft ready to review, message sent, reply received, follow-up due,
  interview scheduled. **Reusing the owner's existing Slack setup from the AXIOM project** if its webhook /
  token is available (owner already wired Slack there).

## Advanced Extensions & Multi-Source Additions

See [[10-advanced-ideas]] for full specifications of the 6 advanced features (Email Classifier, Interactive Slack Buttons, ATS Auditor, Exa AI Search MCP, Hacker News Parser, and Conversion Analytics).

