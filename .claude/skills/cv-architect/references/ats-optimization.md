# ATS Optimization — scoring to ≥90

ATS (Applicant Tracking Systems) parse a résumé into fields before a human sees it. A beautiful CV that
parses wrong gets auto-rejected. This is why we ship a parser-clean version. Score every CV against this.

## What breaks parsers (avoid in the ATS version; minimize in the visual one)

- **Multi-column body text** — parsers read left-to-right and scramble columns. Single column only.
- **Tables for real content** — skills/experience in `<table>` cells often parse as gibberish. Use
  plain "Label: value" lines instead.
- **Text inside images / graphics / icons** — invisible to parsers. Never put words in an image.
- **Headers/footers** holding contact info — many parsers skip them. Keep contact in the body.
- **Non-standard section titles** — use the exact words parsers expect (below).
- **Exotic fonts / text as vectors** — stick to common sans/serif system fonts.
- **Date formats that aren't `MMM YYYY` or `YYYY`** — keep them standard and consistent.

## Standard section headings (use these literal words)

`Summary` · `Skills` (or `Technical Skills`) · `Experience` (or `Work Experience`) · `Projects` ·
`Education` · `Certifications`. Avoid cute renames ("Where I've Made Dents").

## The 90+ checklist (score 1 point each unless weighted; target ≥90/100)

**Parseability (30)**
- [ ] Single-column body (10)
- [ ] No content in tables/images/text-boxes (10)
- [ ] Contact info in the body, not a header/footer (5)
- [ ] Standard, consistent date format (5)

**Keyword match (30)**
- [ ] Target job title appears verbatim near the top (10)
- [ ] Hard-skill keywords from the JD present and truthfully used (12)
- [ ] Both acronym and expansion at least once ("CI/CD", "Kubernetes (K8s)") (8)

**Content quality (25)**
- [ ] Every experience/project bullet has a quantified outcome (10)
- [ ] Action-verb-first bullets, one idea each (8)
- [ ] Reverse-chronological, most-relevant first (7)

**Contact & hygiene (15)**
- [ ] Name, phone, professional email, city/remote, LinkedIn, GitHub/portfolio (7)
- [ ] File saved as `.pdf` (text, not scanned) or `.docx`; sensible filename (4)
- [ ] No spelling/grammar errors; consistent tense (past for done, present for current) (4)

## Keyword method

1. Extract the JD's hard requirements (tools, methods, certs).
2. Keep only the ones that are **true** for the candidate.
3. Weave them into Summary + Skills + the bullets where they were actually used.
4. Never keyword-stuff or add a white-text keyword block — modern ATS + humans both penalize it.

## Length & format

- 1 page for <5 yrs experience, 2 pages otherwise. Dense but scannable.
- Export a **text-based PDF** (not an image/scan). Verify by selecting text in the PDF.
- Filename: `First-Last-Role.pdf` (e.g. `Azam-Shah-DevOps-Engineer.pdf`).
