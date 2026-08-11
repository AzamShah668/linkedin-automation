# 28 — frontend / backend / database, and the console page

> Written 2026-08-11. Read with [[14-send-board-dashboard]] (what the dashboard is for) and
> [[22-rewrite-architecture]] (where the runtime is going).
>
> One-line summary: **three folders now say what each part is, and one page finally shows the
> whole pipeline at once.**

---

## 1. What moved

| Was | Now | Why |
|---|---|---|
| `web/` | `frontend/` | pages, static assets, and a README explaining how a page is wired |
| `tools/serve_dashboard.py` | `backend/server.py` | the server was buried among forty unrelated scripts |
| `tools/pipeline_runner.py` | `backend/pipeline_runner.py` | it only exists to serve the `/controls` page |
| `tools/board_db.py` | `database/board_db.py` | the schema belongs with the store |
| `output/dashboard/board.sqlite3` | `database/board.sqlite3` | see §3 |

`tools/` keeps everything else — the PowerShell runners, Slack, Notion, the post creator.

## 2. 🔴 The two shims exist for a reason. Do not "tidy" them away.

**`board_db` had sixteen callers.** Three of them are PowerShell scripts launched by Task
Scheduler (`auto-apply.ps1`, `build-packet.ps1`, `sweep-packets.ps1`); seven more are
`post_creator` scripts. Every one of them does `sys.path.insert(0, "tools")` then `import
board_db`. Moving the file without a shim would have broken all sixteen **silently, overnight, in
a log nobody reads** — the exact failure mode this project keeps paying for.

⚠️ **The shim must load the real module BY FILE PATH.** Both files are called `board_db.py`, so a
plain `from board_db import *` inside `tools/board_db.py` re-imports *itself* and dies with:

```
ImportError: cannot import name 'ALLOWED_STATUS' from partially initialized module 'board_db'
(most likely due to a circular import)
```

`importlib.util.spec_from_file_location` with an explicit path is the only thing that
disambiguates two modules that share a name. This was hit on the first attempt.

`tools/serve_dashboard.py` is a second shim, for the same reason in a different costume:
`dashboard.cmd`, the repo README and four knowledge files all named that path. It prints a note
and launches `backend/server.py`.

**Retire either only when `grep -rn "board_db\|serve_dashboard" --include=*.py --include=*.ps1
--include=*.cmd` comes back clean.**

## 3. 🔴 The database file left `output/` for two reasons

**It is not build output.** `output/` holds generated CVs, PDFs, exports and screenshots — things
that can be regenerated and are routinely cleaned. `board.sqlite3` is the one store the whole
pipeline plans from. Keeping it there made the single irreplaceable file look disposable.

**And a security consequence had to be handled immediately.** `output/` is gitignored; `database/`
was not. The board's `notes` column carries **real recruiter names on 17 rows** — who was
approached, when, and through which warm connection. **This repo is public.**

`.gitignore` now blocks `database/*.sqlite3`, `*.sqlite` and `*.db`. The **schema and access layer
are tracked; the data is not.** Verified after the change that the file no longer appears as
untracked.

`board_db.DB_PATH` and `apps.autopilot.run.BOARD_DB` both fall back to the old location if the new
one is missing, so a machine that has not pulled the migration is never silently handed an **empty
board** — which would read as "no jobs" rather than as an error. That is D30 applied to a file
move.

## 4. The console page

`frontend/console.html` + `static/page-console.js` + `static/console.css`, served at `/console`
and in the nav on every page. One screen answering the questions that were previously spread
across a chat log:

- what has happened over 30 days, and how far it got
- **what to do now**, ranked, each item tagged *only you can do this* or *the system can do this*
- **Easy Apply versus external-site jobs, separated**, every row linking to the posting
- every application on record, with a *reached a person?* column
- what to learn next, and what the machine can do unaided

### It reads four sources, and reports a broken one out loud

`/api/console` assembles the board, the triage cache, the apply ledger and the coverage report
**independently**. A source that fails lands in `warnings` and the page says so in a callout.

> A page rendering zeros looks identical to a page whose data source vanished.

That is the same defect as D30/D35 in a new place, so it was designed out rather than waited for.
Do not collapse those four loads into one `try`/`except`.

### Charts

Five categorical colours are defined as **new tokens** in `console.css`. The base stylesheet only
carries semantic colours (good / warn / crit) and those are **reserved for state** — reusing
`--good` for "series 2" would make a neutral category read as a healthy one. Light and dark steps
were each checked for colour-blind separation against their own surface; the dark set is chosen,
not an automatic lightening of the light set.

## 5. `triage.py` — the data the split needed

Nothing had ever recorded **which** board rows can actually be one-click applied to, so the
Easy Apply / external split could not have been drawn honestly. `apps/autopilot/triage.py` opens
every live posting and writes the answer to `output/apply-log/triage.json`.

**First full run: 14 easy-apply · 22 external · 4 dead.** Roughly three in five live rows have no
Easy Apply button, which is the clearest number yet on how much of the board the batch runner can
even reach.

It is a **cache with a `checked` date on every record**, not a source of truth. Postings close.

## 6. Adding a page

1. `frontend/<name>.html`
2. `frontend/static/page-<name>.js` calling `JH.ready(fn)`
3. an entry in `NAV` in `frontend/static/common.js`
4. an entry in `PAGES` in `backend/server.py`

**Miss step 4 and the route 404s with no other clue.**

## 7. Verified after the move

All seven routes returned 200 · `/api/bootstrap` unchanged · the four PowerShell Python callers
still import through the shim · `apps.autopilot` finds the board at its new path (39 candidates) ·
94 rows readable · 98 tests passing.

---

## 8. The cull — seven pages to four, sixteen actions to eleven (2026-08-11 evening)

The owner's report was *"aside from console, every other page is basically not up to date."*
Audited by **the age of the file each page reads**, not by opinion:

| Page | Its data source | Verdict |
|---|---|---|
| Console | live | keep |
| Board `/` | DB live, but the Notion capture behind it 10 days old | **fold in** |
| Slack | **16 days** — newest message 26 Jul | **deleted** |
| Research | queue 5 days, highlight reel **17 days** | **deleted** |
| Jobs & CV | packets on disk, live | keep |
| Downloads | files on disk, live | keep |
| Run it | live | keep |

### The finding worth keeping: the stamp was the bug, not the data

**The old Board page was never stale.** Its rows came from the local database and were always
current. It *looked* stale because it printed `board synced 1d 23h ago` in the corner — a stamp
describing the **last Notion capture** and nothing else on the page.

> A freshness indicator that describes one source while sitting above five is worse than no
> indicator: it makes live data look dead, and it would equally make dead data look live.

`common.js` now only stamps pages that do not set their own (`stamp.dataset.own`), and the console
publishes a **per-source** strip instead. Same root cause as D23/D29/D35, showing up in a UI.

### What moved rather than vanished

The board's filterable table is on the console, with filters that match how the board is actually
used (**still open / all / applied / warm / remote / fit 85+**) and a count of how many rows are
hidden — the old table silently omitted them.

### Slack: the mirror went, the gate stayed

`slack.html` mirrored a channel already on the owner's phone, and its newest message was 16 days
old. **`check_approvals.py` queries Slack directly**, so the ✅-to-send gate (D12) is untouched.
Only the mirror, its `slack-refresh` action, its `/api/bootstrap` payload and the export step in
`dashboard.cmd` are gone.

### Actions: 16 → 11, because five could not work or duplicated the console

**`NOTION_TOKEN` is not set**, so `notion-push` and `notion-queue` could never do anything —
they were buttons that were always going to fail. `invites`, `invites-due` and `expire` duplicated
what the console shows live or what `watch-accepts` already does as its first step.

⚠️ **Consequence to state plainly:** with no Notion token, status changes made on the dashboard
stay local. **`database/board.sqlite3` is the real store** — `apps/autopilot` plans from it, and
nothing pushes back to Notion. `sync-board` (import from a manual capture) is kept as the only
inbound path.

### Two breakages caught in verification, not in production

- The **startup guard still checked for `index.html`** and aborted naming a file nobody had
  touched.
- The **Jobs page linked to `/research`**, now a 404. It links to the packet zip instead — same
  research, current on disk. The first replacement URL was also wrong; the route needs a `.zip`
  suffix. Both found by curling every route rather than assuming.

**Verified after:** four pages + both APIs 200, `/research` and `/slack` 404, 11 actions, 98 tests.
