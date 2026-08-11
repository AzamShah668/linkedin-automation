# The dashboard (local website)

    dashboard.cmd            # refresh Slack, start the server, open the browser
    py -3 backend/server.py --port 9000 --no-browser

**Six real pages**, each its own URL — not tabs on one page:

| URL | Page | What it does |
|---|---|---|
| `/` | Board | metrics, the four send stages, quick grabs, the whole board with filters |
| `/jobs` | Jobs & CV | pick a role -> job + apply link left, **tailored CV with a real PDF download** right. Deep-linkable: `/jobs?id=<notion-page-id>` |
| `/research` | Research | the six rules every message follows, the Highlight Reel, then per-company dossier + exact messages with copy buttons. Deep-linkable: `/research?c=<slug>` |
| `/slack` | Slack | every job-hunt message with the reactions that gated each send |
| `/downloads` | Downloads | every artefact, grouped, real files behind each button |
| `/controls` | Run it | **every pipeline step on a button**, with live output |

Front-end is one shared `static/common.js` (bootstrap fetch, nav, markdown, formatting) plus exactly one
`static/page-<name>.js` per page. Adding a page = an HTML shell + a page script + one line in
`Handler.PAGES`.

## Running the pipeline from the browser (`/controls`)

`tools/pipeline_runner.py` holds the action registry. Every action carries a **tier**, and the tier is
enforced **server-side** so a stray fetch cannot fire outreach:

| Tier | Meaning | Gate |
|---|---|---|
| `safe` | read-only or local-only | one click |
| `heavy` | drives a headless Claude; slow, costs tokens, writes Notion/Slack | `confirm: true` |
| `send` | **puts a message in front of a real person** | `confirm: true` + a red confirm panel |

Only two actions are `send`: `flush-approved` (stage 1, bare connection requests) and `watch-accepts`
(stage 2, the CV + pitch). Both are irreversible. Verified: a POST without `confirm` returns **409**.

**Preflight.** `/api/preflight` counts LinkedIn MCP servers before you fire anything LinkedIn-shaped. More
than one server means a run would fail and misreport it as expired auth (05-decisions D13), so the page says
so up front. It counts **python.exe only** — each Claude session also spawns two uvx wrappers.
Concurrency: one LinkedIn-touching run at a time, refused with 409 rather than queued.

    POST /api/run            {action, confirm}   -> starts, returns the run
    GET  /api/run/<id>                           -> status + captured output
    POST /api/run/<id>/stop                      -> terminate
    GET  /api/runs                               -> recent history
    GET  /api/actions                            -> the catalogue with tiers

## Why local and not the published Artifact

An Artifact cannot hand you a PDF: `pdf` is not in its download allowlist and frame code cannot download
directly. A server can. The Artifact stays useful as the phone view.

## Where the data comes from

| Data | Source | Refresh |
|---|---|---|
| Job board | **SQLite** `database/board.sqlite3` (mirror of the Notion board, gitignored) | `/controls` -> Refresh the board, or `py -3 tools/sync_board.py <rows.json>` |
| Outreach + research | `output/outreach/**` read live off disk | nothing to do |
| CVs | `output/cv/tailored/*`, `output/pdf/*` read live off disk | nothing to do |
| Slack | `output/dashboard/slack-export.json` | `/controls` -> Refresh the Slack mirror |
| Invite pipeline | `output/outreach/pending-invites.json` | the accept watcher writes it |

Notion stays the system of record (D7). SQLite is a **local mirror** so the site works offline with no Notion
token: a Claude session re-queries Notion over MCP and pipes the raw result into `sync_board.py`, which
accepts the MCP shape unchanged.

## Marking a role done yourself

When you apply by hand (LinkedIn Easy Apply, a company form), nothing else will ever flip that row off
"packet ready" — the board can only read Notion. So `/jobs` has a status control:

    "I sent the CV — mark as applied"      -> Applied, stamps today's date, stage becomes delivered
    a dropdown for the rest               -> Invite sent / Interview / Rejected / Not for me / back to To Apply

    POST /api/job/<notion-page-id>/status   {status, note?}

**Local edits win over syncs until pushed.** A change is recorded in `status_changes` as unpushed, and
`upsert_rows` refuses to overwrite the status *or* the applied date of a job with an unpushed change.
Without that, marking a role applied and then hitting "Refresh the board" would silently revert it — the
edit appears to work, then undoes itself, which is worse than not having the feature.

### One button does the whole update

On the job panel: **"Push to Notion now"**. It writes the status into the Notion pages, refreshes the local
capture so nothing can revert, and clears the queue. Same thing as a button on `/controls`
("Push my changes to Notion") or `py -3 tools/notion_push.py`.

**It needs `NOTION_TOKEN` in `.env`** to touch Notion, because Notion is otherwise only reachable through a
Claude session's MCP connector, which a local server does not have. Create an internal integration at
notion.so/my-integrations, share the "Job Hunt — Autopilot" database with it, and paste the secret in.
Without the token the button still does the local half (keeps the capture aligned so nothing reverts) and
says plainly that Notion is waiting on a Claude session.

The `Status` property may be a `status` or a `select` in Notion; `notion_push.py` tries `status` first and
falls back on a 400, so it works either way without being told which.

### Why there is no longer an ordering trap

An earlier version compared nothing and relied on you refreshing the seed *before* clearing the queue —
get that order wrong and the next sync reverted the row. Now `upsert_rows` takes the capture's `captured`
timestamp and keeps a local change **unless the capture is provably newer than the change**. The guard
lifts itself once Notion demonstrably knows, so there is no sequence to remember and no way to lose an edit
by syncing at the wrong moment.

## Downloads

    /download/cv/<stem>.pdf        one tailored CV, as an attachment
    /download/cv/<stem>.html       the same CV as HTML
    /download/packet/<slug>.zip    one company: CV (pdf+html) + all messages + reel
    /download/all.zip              every CV and every draft (~1.3 MB, 30 files)

## Safety

Binds to **127.0.0.1 only**. Downloads are allowlisted by stem and extension (not path-joined), static files
are containment-checked against `web/`, and run actions come from a fixed registry — there is no route that
takes a command from the request. Verified: traversal attempts and unknown actions both refused.
