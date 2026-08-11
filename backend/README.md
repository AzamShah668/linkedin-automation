# backend/ — the local dashboard server

A dependency-free `http.server` app. No framework, no build step, no port exposed beyond
localhost.

| File | What it is |
|---|---|
| `server.py` | routes, JSON API, static file serving, zip downloads |
| `pipeline_runner.py` | runs the allow-listed actions the `/controls` page offers |

## Run it

```
dashboard.cmd            # refreshes the Slack mirror, then starts this
py -3 backend/server.py  # or directly
```

## Routes

| Route | Serves |
|---|---|
| `/`, `/console`, `/jobs`, `/research`, `/slack`, `/downloads`, `/controls` | pages from `frontend/` |
| `/static/*` | `frontend/static/` |
| `/api/bootstrap` | the board, packets, Slack feed — what every page starts from |
| `/api/console` | the console page: triage split, ledger, coverage, 30-day series |
| `/api/actions`, `/api/preflight`, `/api/runs`, `/api/run/<id>` | the action runner |
| `/download/*` | packet zips and individual artefacts |

## Two things to know before editing

**`/api/console` reads four independent sources** — board, triage cache, apply ledger, coverage
report — and degrades each one separately. A source that fails lands in `warnings` and the page
says so out loud, because **a page rendering zeros looks identical to a page whose data vanished.**
That confusion has cost this project real time; do not "simplify" it into a bare try/except.

**`sys.path` is set explicitly**, not inherited from the working directory. This is launched from
`dashboard.cmd`, from Task Scheduler, and by hand — and those three do not agree on where they
start.
