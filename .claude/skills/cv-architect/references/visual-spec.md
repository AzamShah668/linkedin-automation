# Visual Spec — the stat-tile résumé look

The signature look: a centered header, a **grid of stat tiles**, a summary, then clean sections with
blue underlined headings. Designed, professional, lots of whitespace. Engineered to also parse well.

## Design tokens

```
--navy:        #1b2a4a;   /* name, stat numbers, sub-headings */
--accent:      #2c5aa0;   /* section headings, tagline, links */
--accent-line: #2c5aa0;   /* section underline rule */
--text:        #24292f;   /* body */
--muted:       #5b6672;   /* labels, contact, dates */
--tile-bg:     #f7f9fc;   /* stat tile background */
--tile-border: #e2e8f0;   /* tile + rule borders */
--page:        #ffffff;
Font: system sans stack — -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif.
Page: max-width 820px, ~48px padding, 11–11.5pt body, 1.4 line-height.
```

## Structure (top to bottom)

1. **Name** — centered, ~30px, bold, letter-spacing 1–2px, `--navy`, uppercase.
2. **Tagline** — centered, ~13px, `--accent`, the role line (e.g. "DevOps Engineer · Platform · MLOps").
3. **Contact** — centered, ~11px, `--muted`, ` | `-separated: email · phone · location · GitHub · portfolio.
   **Contact lives in the body** (not a header) so ATS reads it.
4. **Divider** — 2px `--navy` rule.
5. **Stat tiles** — CSS grid, 3 columns × 2 rows (stacks to 2-col on narrow). Each tile: `--tile-bg`,
   1px `--tile-border`, radius 6px, centered. Big number (~22px bold `--navy`) over a small uppercase
   label (~9.5px, letter-spacing, `--muted`). Tiles contain **plain text in reading order** so parsers
   still extract "108 Production Python Tools …".
6. **Summary** — 2–4 lines, no heading (or a "Summary" heading for max ATS clarity).
7. **Sections** — heading = `--accent`, uppercase, ~12px, bold, letter-spacing, with a 1px bottom
   border spanning the width. Standard names (Skills, Experience, Projects, Education).
8. **Sub-headings** — bold `--navy` left, optional date right (`--muted`), via flex.
9. **Bullets** — `--text`, comfortable spacing, one idea each.
10. **Skills** — "**Label** — value" lines (NOT an HTML table), so it parses cleanly.
11. **Footer** — small muted line ("References available on request").

## ATS-safe engineering rules for the HTML

- Single-column body throughout. The only grid is the stat tiles (linear text inside).
- No `<table>` for content; no text baked into images; no CSS that reorders DOM vs reading order.
- Real selectable text everywhere. Print to PDF (A4/Letter), margins on, backgrounds on for tiles.
- Keep the DOM order = the reading order a human expects.

## Print

Include `@media print` and `@page { margin: 14mm; }`. Ensure tile backgrounds print
(`-webkit-print-color-adjust: exact; print-color-adjust: exact;`). Ctrl/Cmd+P → Save as PDF.
