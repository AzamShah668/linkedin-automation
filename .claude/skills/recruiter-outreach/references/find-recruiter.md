# Find the recruiter — ban-safe contact discovery

Goal: resolve a **real, named hiring contact** (or a legitimate role inbox) for a target company, with a
confidence level and a channel — without scraping-at-scale or anything that risks the LinkedIn account.

> **Always capture the `apply_url` first.** The formal application is where the tailored CV actually gets
> uploaded; outreach only supports it. Use `get_job_details` to record whether it is Easy Apply or an
> external portal, how old the post is, and the applicant count — freshness decides send order. A packet
> without an apply link is incomplete (this was a real miss on 2026-07-26).

Output of this step: `output/outreach/<slug>/contact.md` (schema at the bottom).

## Priority ladder (stop at the first that yields a verified contact)

### 1. Contact already in the posting / ATS payload  — confidence: HIGH
Greenhouse/Lever/Ashby/Workable payloads and many LinkedIn/job-board posts name a recruiter or give an
apply email. If present, use it verbatim. No inference, no guessing. Prefer this always.

### 2. LinkedIn MCP — read-only person lookup  — confidence: MED–HIGH
Use the connected `mcp-server-linkedin` tools to **find and read** a hiring contact. Read-only: capture
name, title, and profile URL. **Do NOT `connect_with_person` or `send_message` in this step** — those are
send actions and belong to the human after approval.

> **ALWAYS DO THIS FIRST — hunt for a warm insider before any cold recruiter.** Before (or alongside)
> searching for the formal recruiter, run one search for someone **already inside the company who shares a
> real tie with the owner** — a warm referral beats a cold recruiter every time, at every company. This is
> not optional; do it for every target. Tie types to search, in rough order of strength:
> 1. **Mutual connections / 1st–2nd degree** — `network=["F"]` then `["S"]`.
> 2. **Same university** — `keywords="<Company> <owner's university>"` (owner: Central University of Kashmir).
> 3. **Same home region / community / language** — `keywords="<Company> <owner's region>"`
>    (owner: Kashmir / Srinagar / J&K). *This is the move that found the two Kashmiri engineers inside Infosys.*
> 4. **Former employer / shared project / OSS overlap.**
>
> If a warm insider exists, they become the ⭐ primary path (a **referral ask**), and the formal recruiter
> drops to a fallback. Record the tie + the *evidence* for it in `contact.md`. Only claim a tie you can see
> in the data — if the tie is inferred (e.g. region matches but university unconfirmed), lead with the
> verified part and mark the stronger version `[VERIFY]` (never assert an unverified bond).

- `search_people(keywords, location)` — e.g. `keywords="technical recruiter <Company>"`,
  `keywords="<Company> talent acquisition"`, or `keywords="<role> hiring manager <Company>"`.
  Filter `network=["F"]` first (a 1st-degree/warm contact is worth far more than a cold one), then widen.
- `get_company_employees(company_slug, keywords="recruiter|talent|hiring")` — needs the exact LinkedIn URL
  **slug** (path after `/company/`), which is often not the display name. If unsure, `search_companies`
  first and take the slug from the result.
- `get_company_profile(company_slug)` — confirms the company + exposes the URN id used by
  `search_people(current_company=<urn>)` for precise employee filtering.

Pick the best match by: (a) warm degree, (b) title relevance (technical recruiter / talent partner for the
exact function > generic HR), (c) recency/activity. Capture the **profile URL** so the human can verify and
send from the app.

> If the MCP errors or the session is not authenticated, **do not fabricate a contact.** Record
> `contact_status: LINKEDIN_UNAVAILABLE`, fall back to the email ladder below, and leave the LinkedIn
> Touch 2 recipient as a `[RECRUITER NAME — fill from LinkedIn]` slot for the human to complete.

### 3. Inferred company email + verify  — confidence: LOW–MED
Only when 1–2 don't yield a usable address. Derive the domain from the company's careers site, then apply
the **known pattern** for that company if one is established; otherwise generate the common candidates and
**verify before use**:

```
first.last@domain        jane.doe@acme.com
firstlast@domain         janedoe@acme.com
first@domain             jane@acme.com
f.last@domain            j.doe@acme.com
firstinitiallast@domain  jdoe@acme.com
```

Verify with a deliverability/MX check (or an email-verification API) — never blast unverified guesses.
If none verify, drop to step 4.

### 4. Legitimate role / careers inbox  — confidence: LOW
`careers@`, `jobs@`, `talent@`, `hiring@<domain>`, or the ATS apply address. Address Touch 1 here and
**hold Touch 2** (no named human to personally message). Still fully personalized to the role + company.

## Verification checklist before a contact is "usable"
- [ ] Name + title look real and role-relevant (not a random employee).
- [ ] Email verified (MX/deliverability) **or** taken directly from the posting.
- [ ] LinkedIn profile URL captured (for the human to eyeball before sending Touch 2).
- [ ] Confidence recorded honestly (HIGH / MED / LOW).
- [ ] No invented data anywhere. Unknowns are `[VERIFY]` slots, not guesses.

## `contact.md` schema (write this per company)

```markdown
# Contact — <Company> · <Role>

- apply_url:       <the job posting URL — ALWAYS capture this; it is where the CV actually goes>
- apply_note:      <Easy Apply or external portal · how old the post is · applicant count if shown>
- also_open:       <other roles at the same company, so one outreach can cover them>
- name:            <full name | UNKNOWN>
- title:           <recruiter title | UNKNOWN>
- linkedin_url:    <profile url | UNKNOWN>
- email:           <verified email | role-inbox | UNKNOWN>
- email_source:    posting | ats | inferred-verified | role-inbox
- degree:          1st | 2nd | 3rd | n/a
- confidence:      HIGH | MED | LOW
- contact_status:  READY | LINKEDIN_UNAVAILABLE | EMAIL_ONLY | NO_NAMED_CONTACT
- found_via:       <search_people query / posting / careers page>
- notes:           <warm-intro path, alumni overlap, anything the human should know>
```

## Warm-insider-first rule (the highest-signal move — use it EVERY time)
A stranger asking for a job is easy to ignore; someone who shares your roots is not. So for **every**
company, the first job is to find a warm insider and lead the personal touch with the shared tie — **before**
falling back to a cold recruiter. Tie strength, best first: mutual connection → same university → **same
home region / community** → former employer / shared project. The Kashmiri-engineers-inside-Infosys result
came from searching the *region* tie, not the school — so search all of these, not just alumni.

**How to use it:**
- Record the insider + the *evidence* of the tie in `contact.md` (mutuals seen, "Education: <uni>",
  "Location: <region>"). Make them the ⭐ primary path; demote the formal recruiter to fallback.
- **Lead Touch 2 with the tie**, warmly and briefly ("fellow Kashmiri here 👋, we share a few connections…").
- **Grounding guardrail (non-negotiable):** claim only the tie the data actually shows. If region matches
  but the university isn't confirmed, say "fellow Kashmiri," not "fellow CUK grad," and leave the stronger
  line as `[VERIFY]`. A warm opener that's *true* beats a stronger one that's a guess — and a false claim of
  connection is the fastest way to lose a recruiter's trust.
- The ask to a warm insider is a **referral / "get your read on the team"**, not a hard pitch — softer,
  higher-converting. Keep the hard metrics for the recruiter/email touch.
