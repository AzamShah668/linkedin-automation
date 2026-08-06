# Dual-touch templates — the two messages

> **CV delivery (decision D12):** Touch 1 links the **single general CV** at
> `https://github.com/AzamShah668/AzamShah668/blob/main/Azam-Shah-CV.pdf`. Never attach (the Gmail API
> can't) and never publish the tailored variants — a recruiter could browse the repo root and see every
> other role being pitched. Tailored CVs stay local in `output/pdf/` for LinkedIn/portal uploads.
>
> **House style:** no em-dashes (—), no dash-bullets, no "·" separators. They read as AI-written. Use plain
> sentences and commas.
>
> **Always include the CV link in the LinkedIn message too** (owner's instruction, 2026-07-26), not just in
> the email: `CV: https://github.com/AzamShah668/AzamShah668/blob/main/Azam-Shah-CV.pdf`. The connect note
> is capped at **300 characters** and that link costs ~68, so cut the body copy to make room rather than
> dropping the link. In the DM (no cap) include the GitHub profile as well.

Two messages per job, to two channels, never copy-pasted. Fill only the `{{slots}}`; everything else is
structure. Every filled slot must trace to `output/cv/achievement-bank.md`, `profile/master-profile.md`,
the tailored CV, or verified company research. Unknowns stay as `[VERIFY]` — never guessed.

---

## Touch 1 — Formal email (Gmail)

**File:** `output/outreach/<slug>/touch-1-email.md`
**Attachment:** the matching `output/cv/tailored/<n>-<Company>-<Role>.html` (export to PDF on approval)

```
To:       {{recruiter_email | role_inbox}}
Subject:  {{Role}} — {{one-line hook}} (Azam Rizwan Shah)

Hi {{FirstName | "Hiring team"}},

I'm applying for the {{Role}} role at {{Company}}. {{one hook sentence: who I am + the single
metric that matches this role's biggest stated need}}.

A few things that map directly to what you're hiring for:
- {{proof bullet 1 — metric + outcome, from the achievement bank}}
- {{proof bullet 2 — different capability the JD asks for}}
- {{proof bullet 3 — a differentiator or reliability/scale point}}

Tailored CV attached. It's all verifiable — code is public:
- Tailored CV: {{link or "attached"}}
- GitHub: github.com/AzamShah668  ·  {{one flagship repo link}}

Would you be open to a quick call this week? Happy to walk through any of the above.

Best,
Azam Rizwan Shah
azamshah25809@gmail.com · +91 <YOUR-PHONE>
linkedin.com/in/azam-shah-4ba6752ba · github.com/AzamShah668
```

**Rules for Touch 1**
- Subject: exact role title + a short differentiator; no clickbait.
- ≤ 150 words body. One hook, three bullets, one ask. No wall of text.
- The hook metric must match the JD's top need (DevOps→CI/CD & K8s; AI→RAG/agents; FDE→build+deploy).
- Always attach the tailored CV; always give at least one public link they can click to verify.
- One ask only: a quick call. Don't stack multiple requests.

---

## Touch 2 — Personal recruiter message (LinkedIn)

**File:** `output/outreach/<slug>/touch-2-linkedin.md`
Two variants; pick by degree. **Connection note hard limit: 300 characters.**

### 2a — Connection request note (2nd/3rd degree) — ≤300 chars
```
Hi {{FirstName}} — {{single strongest quantified win from the Highlight Reel}}. Saw {{Company}} is
hiring a {{Role}}; {{one specific, researched detail about the company}} is exactly what I've been
building toward. Would love to connect and share how I'd contribute.
```

### 2b — Direct message (1st degree, or after they accept) — **this is the one that actually gets sent**
```
Hi {{FirstName}}, {{THE WARM LINE — shared roots / alumni / mutual connections, if any}}, thanks for
connecting!

I saw {{Company}}'s {{Role}} opening. Quick reason I reached out directly: {{one researched detail
about the company/product/team}} lines up with what I do — {{strongest quantified win}}, and
{{second proof point relevant to them}}.

I've tailored a CV to this exact role — happy to send it over, or grab 15 minutes whenever suits you.

CV: https://github.com/AzamShah668/AzamShah668/blob/main/Azam-Shah-CV.pdf
GitHub: github.com/AzamShah668

Cheers,
Azam
```

> ⚠️ **The warm line MUST live here, not in 2a.** Since [[05-decisions]] D12 the connection request goes out
> **bare** — 2a is written for the record and for the owner's 3 hand-sent notes a month, but the robot never
> delivers it. If the "fellow Kashmiri / fellow CUK grad / we share connections" hook only appears in 2a, it
> reaches nobody. Owner, 2026-07-26: *"when Recruiter-A accepts the request, after that you need to put that
> request about being a fellow Kashmiri and providing the CV."* Put the shared-roots opener in the FIRST LINE
> of 2b, before the role, and include the CV link in the body.

**Rules for Touch 2**
- Lead with the **win**, not "I hope this finds you well." First 8 words carry it.
- Exactly **one** researched company detail — real and specific (a product, a recent launch, the team's
  focus, an alumni/warm tie). This is the anti-spam signal; a generic note gets ignored or flagged.
- First-person, warm, no corporate boilerplate. Sound like a person, not a mail-merge.
- Never attach files on LinkedIn; give the **CV link** in the body of 2b (a link, not an attachment).
- If there's a warm-intro/alumni path (from `contact.md` notes), lead **2b** with it instead of a cold hook —
  first line, before the role. That hook is the single highest-value sentence in the whole packet and 2b is
  now the only message that reaches the person.
- If no named contact exists, **do not send Touch 2** — leave it staged as `HOLD (no named contact)`.

---

## The fill-in contract (what the engine must supply per job)
| Slot | Source |
|---|---|
| `Role`, `Company` | job row |
| `recruiter_email`, `FirstName`, degree | `contact.md` |
| hook metric / proof bullets | `output/cv/achievement-bank.md` + tailored CV |
| strongest quantified win | `output/outreach/highlight-reel.md` |
| researched company detail | verified research (JD, careers page, news) — else `[VERIFY]` |
| tailored CV attachment | `output/cv/tailored/<n>-<Company>-<Role>.html` |

Any slot that can't be filled from a real source is emitted as a visible `[VERIFY: …]` marker for the human.
