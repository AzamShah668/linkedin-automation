# Graph Report - .  (2026-07-26)

## Corpus Check
- Corpus is ~32,527 words - fits in a single context window. You may not need a graph.

## Summary
- 75 nodes · 125 edges · 14 communities detected
- Extraction: 50% EXTRACTED · 50% INFERRED · 0% AMBIGUOUS · INFERRED: 63 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## God Nodes (most connected - your core abstractions)
1. `build_card()` - 9 edges
2. `read_state()` - 8 edges
3. `now()` - 7 edges
4. `write_state()` - 7 edges
5. `replace()` - 7 edges
6. `cmd_mark_accepted()` - 7 edges
7. `cmd_mark_sent()` - 6 edges
8. `cmd_mark_failed()` - 6 edges
9. `cmd_expire()` - 6 edges
10. `main()` - 5 edges

## Surprising Connections (you probably didn't know these)
- `cmd_expire()` --calls--> `setting()`  [INFERRED]
  tools\invite_tracker.py → tools\invite_tracker.py  _Bridges community 3 → community 0_

## Communities

### Community 0 - "Two-Stage Invite Tracking"
Cohesion: 0.33
Nodes (16): cmd_add(), cmd_due(), cmd_expire(), cmd_list(), cmd_mark_accepted(), cmd_mark_failed(), cmd_mark_sent(), find() (+8 more)

### Community 1 - "Slack Job Cards"
Cohesion: 0.23
Nodes (14): all_of(), build_card(), first(), first_blockquote(), load_env(), main(), post(), Role, score, recipient, the exact message the robot will send, marker. Nothing e (+6 more)

### Community 2 - "ATS Keyword Audit"
Cohesion: 0.52
Nodes (6): keywords_from_jd(), main(), norm(), present(), Keyword is present if it appears as a token/phrase in the CV text., read_text()

### Community 3 - "Follow-Up Delay Scheduling"
Cohesion: 0.33
Nodes (6): Nudge a timestamp into waking hours. Nobody sends a CV pitch at 4am except a rob, Random 3-20h after the accept, then pulled into business hours., Read an int knob from .env, falling back to the documented default., schedule_followup(), setting(), shift_into_business_hours()

### Community 4 - "Slack Reaction Guard"
Cohesion: 0.6
Nodes (5): call(), find_ts(), load_env(), main(), Locate the newest card carrying `ref:<slug>`.

### Community 5 - "Follow-Up Nudges"
Cohesion: 0.7
Nodes (4): as_bool(), due_for(), main(), notify()

### Community 6 - "Send Queue & Caps"
Cohesion: 0.7
Nodes (4): cap(), fmt(), load_env(), main()

### Community 7 - "Slack File Upload"
Cohesion: 0.83
Nodes (3): api(), load_env(), main()

### Community 8 - "Slack Approval Gate"
Cohesion: 1.0
Nodes (2): load_env(), main()

### Community 9 - "Slack Notifications"
Cohesion: 1.0
Nodes (2): load_env(), main()

### Community 10 - "Reply-Check Task"
Cohesion: 1.0
Nodes (0): 

### Community 11 - "Daily Discovery Task"
Cohesion: 1.0
Nodes (0): 

### Community 12 - "Flush Approved Task (stage 1)"
Cohesion: 1.0
Nodes (0): 

### Community 13 - "Accept Watch Task (stage 2)"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **10 isolated node(s):** `Keyword is present if it appears as a token/phrase in the CV text.`, `Read an int knob from .env, falling back to the documented default.`, `Return a new state with one invite swapped out — no in-place mutation.`, `Nudge a timestamp into waking hours. Nobody sends a CV pitch at 4am except a rob`, `Random 3-20h after the accept, then pulled into business hours.` (+5 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Reply-Check Task`** (1 nodes): `check-replies.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Daily Discovery Task`** (1 nodes): `daily-discovery.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Flush Approved Task (stage 1)`** (1 nodes): `flush-approved.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Accept Watch Task (stage 2)`** (1 nodes): `watch-accepts.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `replace()` connect `Two-Stage Invite Tracking` to `Follow-Up Delay Scheduling`?**
  _High betweenness centrality (0.009) - this node is a cross-community bridge._
- **Why does `schedule_followup()` connect `Follow-Up Delay Scheduling` to `Two-Stage Invite Tracking`?**
  _High betweenness centrality (0.009) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `build_card()` (e.g. with `read()` and `first()`) actually correct?**
  _`build_card()` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `read_state()` (e.g. with `cmd_add()` and `cmd_mark_accepted()`) actually correct?**
  _`read_state()` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `now()` (e.g. with `cmd_add()` and `cmd_mark_accepted()`) actually correct?**
  _`now()` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `write_state()` (e.g. with `replace()` and `cmd_add()`) actually correct?**
  _`write_state()` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `replace()` (e.g. with `write_state()` and `shift_into_business_hours()`) actually correct?**
  _`replace()` has 5 INFERRED edges - model-reasoned connections that need verification._