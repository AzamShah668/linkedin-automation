# Message rules — anti-spam, humanization, throttle, follow-up

The rules that keep outreach *effective* and the account *safe*. Applied to every draft before it enters
the review queue. Extends `~/.claude/rules/common/security.md` and the project's ban-safe rule.

## Anti-spam (the reply-rate rules)
- **One real researched detail per Touch 2.** No detail → no personal message. Generic = ignored/flagged.
- **Front-load a number.** Lead with a quantified win in the first sentence, matched to the JD's top need.
- **One ask per message.** A quick call *or* a connect — not a list of demands.
- **No mass identical sends.** Each message is unique to the company + role. If two drafts read the same,
  they're both wrong.
- **Match freshness to effort.** Prioritize roles posted <48h; be in the first wave, personally.

## Humanization (no AI-tells) — see `../cv-architect/references/humanization.md`
- Plain words. No "I am writing to express my keen interest", "leverage synergies", "I am confident that".
- No em-dash-stuffed cadence, no tricolon everywhere, vary sentence length.
- Contractions are fine (I'm, I've). Sound like Azam, not a template.
- Never open with "I hope this email finds you well."
- One light, specific compliment max — earned by the researched detail, not flattery.

## Throttle & caps (from `.env`)
| Setting | Meaning | Default |
|---|---|---|
| `DAILY_OUTREACH_CAP` | Max outreach *sends* per day (both touches count) | 15 |
| `MIN_SECONDS_BETWEEN_SENDS` | Min gap between two sends | 45 |
| `OUTREACH_JITTER_SECONDS` | Random extra delay added to every send | 0–120 |
| `LINKEDIN_CONNECTS_DAILY_CAP` | Max LinkedIn connection requests/day | 5 |

- Randomized jitter on **every** timed action. Never burst.
- LinkedIn connects are the scarcest budget — spend them on warm/high-fit only.
- Caps are enforced at send, after human approval — approval does not bypass the cap.

## Human-in-the-loop (the send gate)
- The engine drafts and stages. **The owner approves each item.** Nothing sends on its own.
- LinkedIn MCP is used to **find and draft**, never to auto-`connect_with_person` or auto-`send_message`.
- Approve → send via Gmail (Touch 1) / owner clicks send in LinkedIn app (Touch 2) → log event → Slack confirm.
- Reject/edit is one move in `REVIEW-QUEUE.md`; edits are re-grounded, not free-text overrides of facts.

## Follow-up cadence (on no reply)
| When | Action | Tone |
|---|---|---|
| **Day 3** | One short nudge on the same channel | "Circling back — still keen; happy to send anything useful." |
| **Day 7** | Final polite nudge, then stop | "Last note from me — I'll assume timing isn't right. Door open." |
| After Day 7 | Stop. Mark `closed-no-reply`. | — |
- Each nudge is queued for approval like any other message. Never auto-fire.
- A reply at any point cancels the remaining nudges and flips status to `replied`.

## Logging (audit trail)
Every state change (`draft → approved → sent → replied / closed`) is an event with timestamp, channel,
and job id — the same feed Slack reads from. Nothing is sent without a corresponding logged, approved event.
