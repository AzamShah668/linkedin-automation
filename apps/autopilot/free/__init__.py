"""The OmniRoute stack: the same pipeline, with no Claude Code anywhere.

Built BESIDE the Claude stack, never instead of it (Azam, 2026-08-16: "the previous one with the
cloud agents should be there. It should not get deleted"). Everything here has a working
equivalent on `tools/*.ps1` that stays untouched, so a disappointing free model costs nothing.

Shared, already-Claude-free modules are imported from `apps.autopilot`, not copied:
fill · answers · families · ledger · sourcing · coverage · intake · replies · nudge · outreach ·
connect · accepts · pitch. Forking one of those would double the bug surface for no gain.

See docs/knowledge/33-omniroute-stack.md.
"""
