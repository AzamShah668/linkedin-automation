# 30 — Finding a named human at a company (the warm-insider runbook)

> Status **2026-08-14**: written by executing it end to end on **Recro**, the one row
> `coverage.py` flags as having reached nobody. It produced a verified, role-matched
> recruiter in about six MCP calls. Every step below is a step that actually ran.

**What this is for.** [[05-decisions]] D41 counts applications that reached a named human;
D32 is the finding that five of eight submissions reached nobody at all. This is the
procedure that closes one of those gaps. The project's NEXT list calls it "the warm-insider
finder" — this is that, and it is deliberately **a runbook, not a program.**

## ⚠️ Why this is not automated, and must not be

D41 fixed the division of labour on purpose:

> **code finds the gap · an agent finds the recruiter · the human approves the invite**

Automating LinkedIn people-search plus auto-connect is a known account-restriction vector
and is this project's own red line ([[05-decisions]] D2, D12). `coverage.py` is code because
counting is identical every time. Judging whether a stranger is the right person to approach
is different every time, so it stays with an agent, and the send stays with Azam. Do not
"finish" this by writing a scraper.

---

## Step 0 — Get the gap list. Do not guess it.

```
py -3 -m apps.autopilot.coverage
```

Prints every application and which reached nobody. On 2026-08-14: **14 applications, 10
companies, 1 reached nobody** (Recro, Generative AI Engineer, applied 2026-07-29).

Work **one company at a time**. This list is short by design; if it is long, the problem is
upstream in `apply-all`, not here.

---

## Step 1 — Prove the company is real before spending anything on it

`search_companies` → pick the slug from `references`, then `get_company_employees`.

Two of eight submissions went to **Crossing Hurdles**, which had *zero findable employees*
(D36). A company you cannot find a human at is a company the whole outreach design cannot
serve, and the application slot is gone either way.

Record and check:

| Signal | Recro (good) | Crossing Hurdles (dead) |
|---|---|---|
| Employee band | 501-1K | — |
| Findable members | 24 | 0 |
| Verified page | yes | — |

⚠️ **The slug is not the display name.** Recro is `/company/recro-io/`, and the search
returned *nine* different "Recro" companies including a Cape Town accountancy and an
Albanian thrift shop. Take the slug from `references`, never from the name.

⚠️ **Heuristics may only deprioritize; only recorded evidence may block** (D36). Blocking a
real company costs an unrecoverable opportunity; letting a shell through costs ~15 seconds.

---

## Step 2 — Look for a genuinely warm path, and accept when there is none

D8 is warm-insider-first: shared region (especially J&K / Kashmir), university, or a real
mutual. `get_company_employees` returns a **demographics aggregate** — *where they live*,
*where they studied* — which is the cheapest possible test.

Recro: `24 India / 12 Bengaluru / 6 Greater Delhi`. **No J&K cluster.** So there is no warm
rung to stand on, and the honest label for the approach is *cold but well-targeted*.

Three traps, all seen for real:

- 🪤 **The PYMK sidebar is not a warm path.** "People you may know" suggestions have appeared
  in `references` on every profile fetched, ten times over. They are LinkedIn's
  recommendations, not connections.
- 🪤 **A shared mutual is not a referral.** Saksham Sandhu is a mutual with two Recro TA
  people. He has never replied to Azam and has offered nothing. Implying a referral that does
  not exist is the fastest way to burn a real one.
- 🪤 **Never infer someone's region or community from their name.** It is a guess about a real
  person and it is the kind of guess that is both wrong and offensive when wrong. Use the
  profile's stated location and education, which is what D8 actually meant.

---

## Step 3 — Shortlist by *role family*, not by seniority

Filter with `get_company_employees(company, keywords="talent acquisition recruiter")`, then
rank by how close their stated patch is to the role applied for.

Recro returned twelve TA-ish people. The pick was not the most senior; it was the only one
whose stated patch matched the application:

> **Arya Priyadarshini** — *"Talent Acquisition Specialist@Recro | **Data & AI** | Tech Product
> Hiring"* — against an application for **Generative AI Engineer**.

Her own posts advertise `#GenerativeAI #LLMs #PyTorch #NLP` roles. That is the desk the
application should have landed on. A "Lead - Talent Acquisition" with no stated domain is a
worse target than a specialist who posts your exact stack.

---

## Step 4 — ⚠️ Verify current employment from `experience`, never the headline

**The single most important verification step.** A headline is self-written and rots; people
leave jobs and update it late, or never.

```
get_person_profile(username, sections="experience")
```

Arya: *Talent Acquisition Specialist · Recro · Full-time · **Sep 2025 – Present*** — confirmed.

Contrast **Rishu Mishra**, who appeared in Recro's employee listing *and* in the experience-page
references, but whose **headline does not say Recro**. She is recorded as a backup with an
explicit "verify current employer first" flag, not promoted on the strength of a listing.

*Appearing in a company's people tab is not proof of current employment.*

---

## Step 5 — Write the packet. Send nothing.

Create `output/outreach/<company>/` (gitignored — it holds a real person's name, and this
repo is public):

- **`contact.md`** — the dossier: why this person, the evidence for it, ranked backups with
  what still needs verifying, and the honest warmth label.
- **`touch-2-linkedin.md`** — the message for **after** they accept.

Then add a row to `output/outreach/REVIEW-QUEUE.md` and post a Slack `draft_ready` card.

**Stage 1 is a bare connection request with no note** (D12): `connect_with_person` silently
sends nothing when a note is supplied while LinkedIn shows its quota banner, whatever the
length. Stage 2 is the message, after they accept.

### Message rules that are not style preferences

- **Absolute dates only.** "on 29 July", never "a couple of weeks ago". A draft can sit in the
  queue for days and relative time rots into a falsehood — it held Recruiter-B's message once
  (D22).
- **Lead with the application if one exists.** It is the one asset a cold approach lacks, and
  it is verifiable.
- **One specific claim, matched to their stated patch.** No flattery, no company-mission line.
- **No em-dashes, no AI-tells**, plain words.
- **Link the one general public CV.** Never publish a tailored variant. Check
  `output/pdf/FAMILY-*.pdf` first — if the family CV exists, **no packet build is needed**,
  which saves a whole `cv.py` Claude Code subprocess (D24/D30 territory).
- **One person per company at a time.** Two TA people at one company getting the same pitch in
  one week reads as a mail-merge, which is precisely what this project exists not to be.

---

## What "done" means

A row moves off the coverage gap list only when a **named human** has been contacted, not when
a packet exists. Re-run `py -3 -m apps.autopilot.coverage` after the invite is accepted and the
message sent.

Related: [[05-decisions]] D41 (count who reached nobody) · D36 (screen the row first) · D32
(volume without contact) · D12 (two-stage send) · D8 (warm-insider-first) · D22 (relative time)
· [[26-apply-at-volume]] · [[07-current-state]]
