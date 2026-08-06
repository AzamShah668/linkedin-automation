# 01 — Vision & Goals

Back to [[00-INDEX]].

## The problem

Job hunting is slow and repetitive: finding fresh openings, researching each company, rewriting the
CV, writing outreach, and following up. The owner wants that pipeline automated so effort goes only
into the decisions a human should make (which jobs, final approval of what's sent).

## The 6-step vision (owner's words, expanded)

1. **Find** companies that are actively hiring — freshly posted roles, weighted to recency.
2. **Store** them in a queryable database (jobs, companies, contacts, application status).
3. **Process one-by-one** — a ranked work queue, best-fit first.
4. **Focus on genuine recruiting** — filter out ghost jobs / stale posts; prioritize roles posted <48h.
5. **Research deeply** — AI briefs on the company: what they do, recent news, tech stack, values,
   and what they're clearly looking for in this role.
6. **Tailor the CV per company** — a customized résumé + cover letter matched to the job description,
   so the application reads as purpose-built (because it is).

## The extra asks

- **Slack notifications** for every meaningful event: new match found, draft ready to review,
  message sent, reply received, follow-up due.
- **A separate recruiter "Highlight Reel"** — a short, punchy, recruiter-facing message that leads
  with quantified achievements matched to the role. Distinct from the formal CV; it's the hook that
  earns the read. This is a strong idea and gets its own generator in [[02-architecture]].

## Success metrics

- **Speed:** first tailored application out the door within hours of a matching role appearing.
- **Response rate:** % of outreach that gets a reply (target: beat the ~2–5% cold baseline via
  personalization + timing).
- **Interviews booked** per week.
- **Effort:** minutes of human time per application (target: review-and-approve only).

## Non-goals (explicitly out of scope)

- Headless scraping of LinkedIn or bulk automated DMs (ban risk — see [[05-decisions]]).
- Sending anything without human approval (at least until response quality is proven).
- Fabricating experience or credentials in any generated document. Tailoring emphasizes real,
  existing achievements — it never invents them.
