# 14 — The Send Board (live dashboard)

Back to [[00-INDEX]]. The owner-facing view of the pipeline: **who has the CV, who is waiting, and which
companies have had nothing.** Built 2026-07-26, replacing the static "Control Panel" from 2026-07-25.

## ⚠️ There are now TWO front-ends. The local website is the primary one.

| | **Local website** (primary) | **Artifact** (phone view) |
|---|---|---|
| Start | `dashboard.cmd` → <http://127.0.0.1:8765/> | the fixed private Artifact URL below |
| Code | `frontend/` + `backend/server.py` | `output/dashboard/send-board.html` |
| Data | SQLite mirror + files read off disk | live Notion via the `mcp` capability |
| **Downloads** | ✅ **real PDFs and zips** | ❌ impossible |

**The reason the local site exists — and the constraint to remember:** an Artifact **cannot hand you a PDF.**
Its download allowlist is `gif png jpg jpeg webp mp4 webm txt json md` plus `docx pptx epub csv ttf html svg`
— **no `pdf`** — and the contract states outright that "frame code never downloads directly", so an
`<a download>` on a data URI is not a way around it. The owner's actual need was "press it and have the CV
ready to upload", which only a real HTTP server with `Content-Disposition: attachment` can do. Hence the
pivot on 2026-07-26. **Do not try to solve CV download inside the Artifact again.**

**Six real pages, each its own URL** (`/`, `/jobs`, `/research`, `/slack`, `/downloads`, `/controls`) — the
first cut used tabs on one page and the owner asked for genuine separation, correctly: deep links
(`/jobs?id=…`, `/research?c=…`) only work once each subject owns a URL. One shared `static/common.js` plus
exactly one `static/page-<name>.js` per page; adding a page is an HTML shell, a page script and one line in
`Handler.PAGES`. That split also cured the 767-line `app.js` — nothing is over 280 lines now.

### Creating a packet from the front-end (added 2026-07-26)

The owner's question was the right one: *"there are companies where there is no CV, nothing — how do I do
that?"* The dashboard could read and mark, never **create**. Two changes fixed that.

**1. Packets are discovered from disk, not hardcoded.** Each `output/outreach/<slug>/packet.json` describes
its own packet (`company`, `role`, `cv_stem`, `ats`, `job_id`); `discover_packets()` globs for them. The
server previously held a Python list of four packets, which meant **a newly built packet was invisible until
someone edited the server** — the knowledge was in the worst possible place. `company` must match the Notion
value exactly, since that is the join key to a board row.

**2. A per-role Build button.** A role with no packet shows a "No CV yet" panel with the five steps and one
button, wired to a **parameterised** runner action (`build-packet`, `param="job_id"`, `hidden=True` so it
stays off the Controls grid). The parameter reaches a subprocess argv, so it is matched against
`PARAM_PATTERN` server-side — verified that `x; rm -rf /`, `../../etc/passwd` and an over-long string are all
refused before anything spawns.

It runs `tools/build-packet.ps1 -JobId <id>` → headless Claude against [[15-build-packet-runbook]] →
cv-architect + recruiter-outreach → writes the CV, PDF, four documents and `packet.json`, sets the row to
`To Apply`, posts a Slack card. **Sends nothing.**

Two guards, both of which fired correctly in testing:
- **Unknown id** → aborts in a second with "no board row with id …" rather than sending Claude off to
  research a company that was never on the board.
- **Profile contention** → refuses when another MCP server or a browser already holds the LinkedIn profile.
  Note this guard is *stricter* than the one in `watch-accepts.ps1`: the older one only looked for an open
  Chromium holding the profile dir, which does not exist until the MCP launches it on demand, so it missed
  the case that actually happens — a second Claude window with its own server. Counting `python.exe` servers
  catches it. **Consequence: a build only runs with no other Claude window open.**

### `/controls` — running the pipeline by hand (added 2026-07-26)

The owner's ask: *"all the controls should be within my palm of the hand."* `tools/pipeline_runner.py` is an
action registry where every action declares a **tier**, and **the tier is enforced server-side** so a stray
fetch cannot fire outreach:

| Tier | Meaning | Gate |
|---|---|---|
| `safe` | read-only / local-only (doctor, sync board, refresh Slack, invite list, approvals) | one click |
| `heavy` | drives a headless Claude — slow, costs tokens, writes Notion + Slack (discovery, reply-check) | `confirm: true` |
| `send` | **puts a message in front of a real person** (flush-approved, watch-accepts) | `confirm: true` + red confirm panel |

Design points worth keeping:
- **Only two actions are `send`**, and both are irreversible. They are the last things on the page, styled in
  the critical colour, and their blurbs say plainly what leaves the machine. Verified: POST without `confirm`
  returns **409**, as does an unknown action — the UI's confirm dialog is a convenience, not the control.
- **Preflight before any LinkedIn action.** `/api/preflight` counts MCP servers and reports whether a run
  would even work, because more than one server means the run fails and blames the login (D13). It counts
  **python.exe only** (each session also spawns two uvx wrappers, so counting the tree over-reports 3×).
- **One LinkedIn run at a time**, refused with 409 rather than queued — two concurrent runs would reproduce
  the exact profile-contention bug the preflight exists to prevent.
- Output is captured to a bounded deque (600 lines) and polled, so a long discovery run cannot exhaust memory.
- There is **no route that takes a command from the request** — actions come from a fixed registry only.

**Backend + database** — `backend/server.py` (stdlib `http.server`, **127.0.0.1 only**),
`database/board_db.py` (SQLite schema + stage derivation), `tools/sync_board.py` (ingest),
`tools/slack_export.py` (Slack mirror). Notion stays the system of record (D7); SQLite at
`database/board.sqlite3` is a **local mirror** so the site needs no Notion token and works offline.
**It is gitignored** — the `notes` column carries real recruiter names on 17 rows and this repo is public.
`sync_board.py` accepts the **raw `notion-query-data-sources` result shape unchanged**, so a Claude session
pipes the MCP output straight in with no hand-translation — which is where transcription errors would live.
Full operator notes: `tools/README-dashboard.md`.

Two things the design got right by accident and should keep: the Slack channel is **shared with the YouTube
project**, so both front-ends filter to messages from 2026-07-25 onward or June's TTS failures leak in; and
downloads are **allowlisted by stem + extension** rather than path-joined, so `../` cannot escape (verified —
traversal attempts return 404).

## What it is and where it lives

| | |
|---|---|
| **Source** | `output/dashboard/send-board.html` — **in the repo, deliberately** |
| **Published** | private Artifact `claude.ai/code/artifact/8b4c38fe-afac-48c9-9d69-67a45420c8ec` |
| **Updating it** | republish the same file path in the publishing conversation, or pass that **`url`** from any other session — without the `url` a new artifact is minted and the owner's link goes stale |
| **Redeploy needs** | the tool refuses to publish until the session has fetched the current version (`WebFetch` the URL first). This is a concurrency guard, not an error |

> **Why the source is in the repo:** the first control panel was written to a temp scratchpad, Windows
> cleaned the folder, and the source was gone while the page lived on — un-editable without downloading it
> back. Never author an artifact anywhere but the repo.

## The one non-obvious thing: it reads Notion live

The page is not a snapshot of the board. It declares the Artifact **`mcp` runtime capability** and queries
the Notion data source with the *viewer's own* credentials on every open.

```
capabilities: {mcp: {servers: [{server: "claude_ai_Notion",
                                tools:  ["notion-query-data-sources"]}]}}
```

- **In-page call:** `window.claude.mcp.watchTool(server, tool, input, handler, {cache:{staleTime:60000}, refetchInterval:120000})`.
  `watchTool` (not `callTool`) is the arm for *displaying* data — it replays cache, refreshes when stale and
  delivers every later result to the same handler.
- **Input shape** is the same envelope the MCP tool takes: `{data: {data_source_urls: [...], query: "SELECT ..."}}`.
- The metric strip, the board table and the stage-D "no CV out yet" grouping are all **derived** from that one
  query, so they cannot drift the way the old hardcoded "10 jobs / 0 sent" numbers did.

### ⚠️ The bug that cost a publish cycle: two names for one connector

The manifest is declared with the **tool-prefix segment** (`claude_ai_Notion`, taken from
`mcp__claude_ai_Notion__notion-query-data-sources`) and is resolved to the connector's **display name**
(`Notion`) automatically at publish. But the **in-page call must use the display name.** Passing
`claude_ai_Notion` to `watchTool` produced `not_in_manifest` and an empty table, which reads exactly like a
permissions failure and sends you looking in the wrong place.

**The fix, which is also the general rule:** don't hardcode either name — call `listTools()` at boot, find
the server that actually exposes the tool, and use *its* `server` string. A candidate list
(`["Notion", "claude_ai_Notion", ...]`) is the fallback when `listTools()` itself fails, tried in order and
advanced only on the three addressing codes (`not_in_manifest`, `server_not_connected`, `server_not_found`).

### Failure design

Every connector error code gets its own branch and its own fix copy — `needs_reauth` says reconnect,
`server_not_connected` says add the connector, transient codes keep the last good rows with a stale marker.
The page also prints the raw error code in brackets, which is what made the addressing bug diagnosable at
all. Freshness comes from `result.cache.storedAt`, never `Date.now()`.

## Structure — the four stages the owner asked for

Ordered as a CV actually travels, because that ordering *is* the information:

| Stage | Contents | Source |
|---|---|---|
| **A · You** | the only human surface — apply to CodeRound by hand, fix the headline typo, tick Slack cards | snapshot |
| **B · Invited, no answer** | per-person timeline: invited → accepted → CV sends → expires | snapshot |
| **C · Accepted, CV out** | real timestamps, elapsed times computed in-page from ISO strings | snapshot |
| **D · No CV out yet** | **grouped by company**, since several companies have multiple roles behind one contact | live Notion |

The live/snapshot split is stated in the footer rather than implied — stages A–C read local files
(`output/outreach/pending-invites.json`, the runbooks) and only move when the project runs.

## Two consequences worth knowing

1. **A page declaring `mcp` cannot be shared publicly.** Fine for a private board, but it rules the
   dashboard out as a portfolio piece. A shareable version would need the capability dropped and the real
   names removed.
2. **The owner *can* still open it on his phone** — a private artifact opens for its owner, so sending
   himself the link on WhatsApp works. That made the phone layout worth doing properly: below 700px every
   table collapses into one card per row (`data-label` on cells + ordered flex), so nothing scrolls sideways.

## Data-quality catch it surfaces

Oracle's notes say "2 CUK alumni" but its `Warm Intro` checkbox is unticked, so any filter on warm companies
silently skips it. The board renders **◆ ticked** vs **◇ evidence in the notes only**, making the
inconsistency visible instead of costing a warm path. Same treatment for the other rows whose notes mention
alumni without the box set. See [[05-decisions]] D8 for why warm paths matter this much.

Related: [[07-current-state]] · [[13-accept-watch-runbook]] · [[12-approved-send-runbook]]
