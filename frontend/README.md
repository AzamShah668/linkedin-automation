# frontend/ — the dashboard pages

Plain HTML + CSS + vanilla JS. No framework, no bundler, no `node_modules`. Every page is a file
you can open and read.

| Page | Route | What it answers |
|---|---|---|
| `console.html` | `/` and `/console` | **The home page.** Live: progress, what to do next, the Easy Apply / external split, the whole board, what to learn |
| `jobs.html` | `/jobs` | One row at a time — packet, CV, status |
| `downloads.html` | `/downloads` | Every artefact, with a real file behind each button |
| `controls.html` | `/controls` | Run a pipeline action |

## Three pages were removed on 2026-08-11

Not because they were broken, but because they were **out of date and nobody could tell**:

- **`index.html`** (the old Board) — its data was always live; the page only *looked* stale
  because it stamped "board synced Xd ago", which describes the last Notion capture and nothing
  else on the page. Its useful half, the filterable table, moved onto the console.
- **`research.html`** — read `REVIEW-QUEUE.md` (5 days old) and `highlight-reel.md` (17 days old),
  and duplicated what the Jobs page already shows per row.
- **`slack.html`** — a mirror of the Slack channel whose newest message was **16 days old**. Slack
  is already on your phone; a stale copy of a live app is worse than no copy.

Their payloads (`slack`, `research`) were also removed from `/api/bootstrap`, where they were being
computed on every request for nobody.

## How a page is wired

1. The HTML loads `/static/style.css`, then `/static/common.js`, then exactly one `page-*.js`.
2. `common.js` fetches `/api/bootstrap`, renders the nav, and calls `JH.ready(fn)` with the data.
3. The page script draws into elements the HTML already declared.

Adding a page means: the HTML file, a `page-*.js`, an entry in `NAV` in `common.js`, and an entry
in `PAGES` in `backend/server.py`. Miss the last one and you get a 404 with no other clue.

## Styling

`style.css` owns the tokens — colours, type, spacing, and the dark theme. Page-specific sheets
(`console.css`) may **add** tokens but must not redefine the base ones, or the two pages drift
apart and dark mode has to be solved twice.

The five categorical chart colours in `console.css` are new tokens on purpose: the base sheet only
carries semantic colours (good / warn / crit) and those are reserved for state. Reusing `--good`
for "series 2" would make a neutral category read as a healthy one. Both the light and dark steps
were checked for colour-blind separation against their own surface — the dark set is chosen, not
an automatic lightening of the light set.
