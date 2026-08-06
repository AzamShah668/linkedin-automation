# 03 — Data Sources (legitimate & ban-safe)

Back to [[00-INDEX]]. Why we avoid scraping: [[05-decisions]].

The trick to a *ban-safe* job hunter: most companies publish their openings through structured,
public APIs. We use those instead of scraping LinkedIn.

## Tier 1 — ATS public job boards (best: structured, free, legitimate)

Companies using these platforms expose public JSON of their live jobs:

- **Greenhouse** — `https://boards-api.greenhouse.io/v1/boards/{company}/jobs?content=true`
- **Lever** — `https://api.lever.co/v0/postings/{company}?mode=json`
- **Ashby** — `https://api.ashbyhq.com/posting-api/job-board/{company}`
- **Workable** — `https://apply.workable.com/api/v3/accounts/{company}/jobs`
- **SmartRecruiters** — `https://api.smartrecruiters.com/v1/companies/{company}/postings`
- **Recruitee** — `https://{company}.recruitee.com/api/offers/`

Strategy: keep a watchlist of target companies + their ATS slug. This is the cleanest, richest data
(full descriptions, locations, departments) and covers most startups/scaleups — which also tend to
have **faster hiring processes** than big corporates.

## Tier 2 — Job-board aggregator APIs

- **Adzuna** — global, generous free tier (needs app_id + app_key)
- **Reed** — UK-focused, free API key
- **Remotive** — remote jobs, open API
- **Arbeitnow** — free jobs API (EU + remote)
- **The Muse** — company + jobs API
- **USAJOBS** — US government roles

## Tier 3 — LinkedIn (official / ToS-friendly only)

- **Gmail LinkedIn Job Alert parser** — set up LinkedIn Job Alert emails, then parse them via the
  already-connected **Gmail API**. Clean, legitimate LinkedIn signal with zero scraping. **Primary
  LinkedIn path.**
- **Browser-assisted capture** (optional, later) — owner browses LinkedIn normally; a helper saves
  the currently-viewed posting. Human-driven, not a headless bot.
- ❌ Not used: headless scraping, `linkedin-api` style unofficial clients, bulk auto-DMs.

## Tier 4 — Company career-page RSS / feeds

Some career pages / job boards expose RSS. Cheap to poll for a curated set of dream companies.

## Recruiter contact discovery (ban-safe)

- Prefer emails already present in the job posting / ATS payload.
- Infer likely email from company domain + common patterns (verify before use).
- Public professional info only. Outreach goes via **Gmail** (better for CV delivery than a LinkedIn
  DM, and not rate-limited into a ban).

## Dedupe

Same role often appears across sources. Key on `(source, source_id)`; fuzzy-match title+company to
collapse cross-source duplicates into one job record.
