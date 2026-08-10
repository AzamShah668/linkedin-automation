# 27 — LinkedIn Content Engine (7-Day Content Calendar)

**Created**: 2026-08-10  
**Status**: ACTIVE  
**Related**: [[21-linkedin-content-strategy-and-research-engine]], [[19-post-creator-and-image-studio]]

---

## What This Is

A complete 7-day LinkedIn content calendar engine that posts daily — 2 project showcases
(Tue/Thu) with PDF carousels, and 5 daily posts (Mon/Wed/Fri/Sat/Sun) about trending topics,
engineering lessons, and real pair-programming stories. **Every post ships with a visual.**

## Architecture

```
Content Hub DB (SQLite)
├── tools/content_hub_db.py        — database layer (20 projects seeded)
├── tools/log_experience.py        — CLI to log ideas from any agent session
├── tools/seed_content_hub.py      — one-time seeder for 20 project showcases
├── tools/trend_finder.py          — Hacker News / NewsData.io topic fetcher
├── tools/post_creator/
│   ├── dispatch_engine.py         — unified orchestrator (reads queue → generates image → posts)
│   ├── prompt_templates.json      — per-post-type FLUX.1 image prompt templates
│   ├── generate_fallback_cache.py — pre-generates 10 safety-net images
│   └── install-dispatch-task.cmd  — Windows Scheduled Task (daily 9 AM)
└── output/content_hub/
    └── content_hub.sqlite3        — the database file
```

## Design Decisions

> ⚠️ **Renumbered 2026-08-10 to D37-D40.** These were originally written as D33-D36, which had
> already been taken in [[05-decisions]] by four unrelated decisions (the company cap, the packet
> layout, the LinkedIn inbox blind spot, and the sourcing screen). **[[05-decisions]] is the single
> numbering authority** — a duplicate number makes every future lookup ambiguous.


### D37: SQLite over Notion as primary store
Notion is only reachable via MCP during an active agent session. The Content Hub
needs to work offline (scheduled tasks, quick CLI adds). SQLite is the local truth,
same proven pattern as `board_db.py`. A Notion sync layer can be added later.

### D38: Agent-agnostic pipeline
Both Claude and Antigravity share the same:
- `.mcp.json` → same MCP servers
- `.pw_browser/linkedin_user_data/` → same LinkedIn session
- `output/` → same generated files
- `tools/*.py` → same CLI scripts
Either agent can log ideas, draft copy, approve, and dispatch. The database is the shared state.

### D39: Human-in-the-loop approval before posting
The dispatch engine only posts items with `status='approved'`. The scheduled task
runs daily but does nothing if no approved post exists. This prevents robotic patterns
and keeps content quality high.

### D40: Every post gets a visual
LinkedIn engagement data (2026): Carousels 24-45%, multi-image 6.6%, single image 6%,
text-only 4%. Image-less posts are a waste. The engine generates a FLUX.1 hero image
for every non-project post, with a 3-engine fallback chain + cached safety net.

## Post Types & Schedule

| Day | Type | DB Value | Visual |
|-----|------|----------|--------|
| Mon | Daily Build Story | `daily-build` | FLUX.1 hero (workspace + code scene) |
| Tue | Project Showcase | `project` | 6-page PDF carousel (real screenshots) |
| Wed | Trending Tech | `trend` | FLUX.1 infographic (data visualization) |
| Thu | Project Showcase | `project` | 6-page PDF carousel (real screenshots) |
| Fri | Engineering Lesson | `lesson` | FLUX.1 hero (contemplative tech scene) |
| Sat | Behind The Scenes | `reflection` | FLUX.1 scene (personal atmosphere) |
| Sun | Tech Reflection | `reflection` | FLUX.1 concept art |

## Content Pipeline

```
1. IDEAS come from three sources:
   ├── Agent session discoveries → log_experience.py → "idea" status
   ├── Trending topics → trend_finder.py → "idea" status
   ├── SESSION SCANNER → scan_sessions.py → mines all 5 brains for post ideas
   └── 20 seeded project showcases → already in DB as "idea"

2. DRAFTING: Agent reads idea + copywriter skill → writes copy + generates image prompt → "drafted"

3. APPROVAL: Human reviews (Notion / CLI / Slack) → "approved"

4. DISPATCH: dispatch_engine.py → generates image → posts via Playwright → "posted"
```

## Session Scanner (`tools/scan_sessions.py`)

Mines ALL 5 knowledge sources for post-worthy content:

| Source | Path | What It Finds |
|--------|------|---------------|
| Brain 3 | `graphify-out/log.md` | Session problems/solutions/decisions |
| Brain 2 | `docs/knowledge/*.md` | Engineering decisions (D1-D36+), architectural insights |
| Claude | `~/.claude/projects/d--linkdin-automation/*.jsonl` | User problem descriptions from Claude sessions |
| Antigravity | `~/.gemini/antigravity-ide/brain/*/transcript.jsonl` | User discussions from Antigravity sessions |
| Obsidian | `~/Desktop/obsedian/AntigravityKnowledge/` | Cross-project patterns and lessons |

Uses **signal word scoring** (root cause, fix, bug, gotcha, trap, built, decision, etc.)
to rank candidates by how "post-worthy" they are. Deduplicates against existing Content Hub entries.

## Key Commands

```bash
# Content Hub
py -3 tools/content_hub_db.py --stats
py -3 tools/content_hub_db.py --list --status idea

# Log a discovery
py -3 tools/log_experience.py --title "..." --insight "..." --type daily-build

# Fetch trends
py -3 tools/trend_finder.py --count 3 --dry-run

# Dispatch
py -3 tools/post_creator/dispatch_engine.py --dry-run --post-id N
py -3 tools/post_creator/dispatch_engine.py --post-id N --headless

# Fallback cache
py -3 tools/post_creator/generate_fallback_cache.py
```

## Current State (2026-08-10)

- **20 project showcases seeded** — scheduled Tue/Thu from 2026-08-11 to 2026-10-15
- **1 daily-build idea logged** — "Playwright browser profile lock" debugging story
- **Trend finder tested** — successfully pulling live Hacker News stories
- **Dispatch engine tested** — dry-run verified for both project and daily-build types
- **Scheduled task installer created** — not yet installed (user decides when to activate)
- **Fallback cache generator created** — not yet run (generates 10 images, ~5 min)
