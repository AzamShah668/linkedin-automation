# frontend/ — the dashboard pages

Plain HTML + CSS + vanilla JS. No framework, no bundler, no `node_modules`. Every page is a file
you can open and read.

| Page | Route | What it answers |
|---|---|---|
| `index.html` | `/` | Where every CV stands right now |
| `console.html` | `/console` | **Everything at once**: progress, what to do next, the Easy Apply / external split, what to learn |
| `jobs.html` | `/jobs` | One row at a time — packet, CV, status |
| `research.html` | `/research` | Company research and contacts |
| `slack.html` | `/slack` | The notification feed |
| `downloads.html` | `/downloads` | Every artefact, with a real file behind each button |
| `controls.html` | `/controls` | Run a pipeline action |

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
