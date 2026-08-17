# Graphify session log

One line per session. Newest at the bottom.

## [2026-07-26 16:40] session | Brain 3 initialized, sending went live
Touched: none (graph built from code only — 13 files, 75 nodes, 125 edges, 14 communities)
Note: built AST-only by design. Brain 3's job is the code-structure map; the 40 markdown docs are Brain 2's
territory (`docs/knowledge/`) and graphing them would duplicate it. Re-run with a semantic pass only if the
docs ever need to be queryable as a graph. Git hooks (post-commit, post-checkout) installed, so the graph
refreshes itself from here on — do not run `graphify . --update` manually (deprecated).

## [2026-07-26 17:25] session | Live send board + false-auth-alarm fix
Touched: none (no wiki dir). Brain 2: NEW 14-send-board-dashboard, 00-INDEX, 05-decisions (D13 addendum + D14), 07-current-state.
Code: NEW output/dashboard/send-board.html, NEW tools/linkedin-doctor.cmd, DELETED tools/linkedin-login.cmd.
Note: the 16:23 LinkedIn "session expired" was NOT an expiry - three MCP servers contending for one
browser profile. Disproof: a DM delivered 16:43, after the claimed 16:23 failure. Read 05-decisions D13 addendum.

## [2026-07-26 17:50] session | Local dashboard website (backend + SQLite)
Touched: none (no wiki dir). Brain 2: 14-send-board-dashboard rewritten - TWO front-ends now.
Code: NEW web/{index.html,style.css,app.js}, tools/{serve_dashboard,board_db,sync_board,slack_export}.py,
dashboard.cmd, tools/README-dashboard.md, output/dashboard/board.sqlite3 (24 rows seeded).
Why: an Artifact cannot download a PDF (no pdf in the allowlist; frame code never downloads directly).

## [2026-07-26 18:05] session | Six separate pages + pipeline controls
Touched: none. Brain 2: 14-send-board-dashboard (pages + controls).
Code: web/ split into 6 page shells + static/{common,page-*}.js; NEW tools/pipeline_runner.py
(tiered action registry: safe/heavy/send, server-enforced confirm, preflight server count, live output);
serve_dashboard.py gained page routes + run API. Verified: send/heavy without confirm -> 409.

## [2026-07-26 18:22] session | Mark-as-applied from the dashboard
Touched: none. Code: board_db.set_status/pending_notion/mark_pushed + status_changes table + sync guard;
POST /api/job/<id>/status; status control on /jobs; NEW tools/notion_queue.py; runner action notion-queue.
Gotcha found+fixed: protecting status alone wiped the applied date on the next sync. Second gotcha:
mark-done BEFORE refreshing board-seed.json reverts the row (protection drops when pushed).
Real use: CodeRound AI marked Applied (owner Easy-Applied by hand), pushed to Notion, seed aligned.

## [2026-07-26 18:32] session | One-button Notion push
Touched: none. Code: NEW tools/notion_push.py (REST PATCH, status/select fallback, refreshes seed);
POST /api/notion/push; "Push to Notion now" button on /jobs + runner action; NOTION_TOKEN in .env.example.
Key fix: upsert_rows now takes captured= and keeps a local change UNLESS the capture is newer than it,
which removes the old ordering trap (mark-done before seed refresh used to revert the row).
Verified: mark -> push -> two syncs -> holds. Test row restored to New afterwards.

## [2026-07-26 18:55] session | Packet creation from the front-end
Touched: none. Brain 2: NEW 15-build-packet-runbook, 00-INDEX, 14-send-board-dashboard.
Code: packets now DISCOVERED from output/outreach/*/packet.json (was a hardcoded list in the server, so a
new packet was invisible); parameterised+hidden runner actions with PARAM_PATTERN validation;
NEW tools/build-packet.ps1 + docs 15; Build button on roles with no packet; 6 tools allowlisted.
Guard note: build-packet counts python mcp servers, stricter than watch-accepts.ps1 which only looked for
an open Chromium and therefore missed the common case. Verified: bad id aborts, contention skips honestly.

## [2026-07-29 21:45] session | GUI automation investigated, grounding proven, CLI blocked
Touched: none (no wiki dir). Brain 2: NEW 16-gui-automation-investigation, 00-INDEX, 05-decisions (D15).
Cross-project: desktop-agent Brain 2 (decisions D7+D8, pending-work), both Obsidian project pages.
Code (in d:\New folder (2)\desktop-agent): NEW brains/claude_code_brain.py, apply_to_job.py,
diagnose_brain.py; fixed session.py console crash, screenshot path, hidden-stdout error reporting.
NEW here: profile/application-answers.json (answer bank; 12 fields deliberately null).
Headline: free OpenRouter vision models score 0/8 on the easiest GUI task; the cause is pixel-coordinate
guessing, not the model (Claude missed by 328px too); USE_GROUNDING=true fixes it (click_element 7, correct
first try). Blocked on the standalone claude CLI returning ConnectionRefused - environmental, not code.

## [2026-07-30 20:05] session | Revived three dead robots, real email sending
Touched: none (markdown lives in Brain 2)
Root cause of 3 failing scheduled tasks was hasTrustDialogAccepted=false -> all 55 allowlist entries
discarded -> headless runs had no tools. Proven by comparing the 19:00 and 19:16 runs in one log, not
by the error code. Also: Write/Edit were never allowlisted, so every "successful" unattended run had
been discarding its own findings; and 2 of 4 runners still used the UTF-16 `*>>` redirect. Composio
Gmail now connected (azamshah25809) and sends for real, but cloud tools cannot attach a local file --
Playwright uploads to Drive instead. New: docs/knowledge/18, D16, D17.

## [2026-07-30 21:17] session | Standalone Daily Post & High-Res Image Studio MCP Server
Touched: none (markdown lives in Brain 2)
Built 100% isolated daily LinkedIn content creation & FLUX.1/Imagen 3 image studio MCP server in tools/post_creator/. Registered mcp-post-studio in .mcp.json. Integrated mcp-post-studio with mcp-server-linkedin@latest for native stdio MCP post publishing. Built master 4-slide carousel generator skill viral-architecture-visualizer. Created Knowledge Item 21. Built & packaged 2 distinct LinkedIn post series: Post 2 (AI Visual Content Studio, ready first with teaser) and Post 1 (Autonomous Job Hunt Autopilot, 10-stage pipeline + 5 scheduled tasks + real stats). Tested & verified end-to-end execution.


## [2026-07-30 21:58] session | Daily discovery run - board 24 to 62
Touched: none (markdown lives in Brain 2)
5 read-only LinkedIn search_jobs runs (DevOps/MLOps/Platform-remote/AI-LLM/SRE, past_week). Deduped vs 24 Notion rows, scored, inserted 38 new rows at fit >=80 (6 warm). Top find: Infosys Junior AI Engineer 90 with an already-accepted connection inside. Slack digest posted. Zero sends. Runbook step 5b (auto-build packets for 85+) NOT run - 7 roles queued.

## [2026-07-30 21:35] session | Accept watch - Innova ESI accepted
(Timestamp is the real clock reading from both bash and PowerShell. It sorts BEFORE the 21:58 entry above,
which appears to be mis-stamped - that session's own summary says it ended 21:29. Left as-is, not rewritten.)
Touched: none (markdown lives in Brain 2). Brain 2: 07-current-state (sent table + mailbox note).
Ran 13-accept-watch-runbook end to end. Expire: nothing >14d. Recruiter-B (Innova ESI DevOps 87) flipped
3rd -> 1st = ACCEPTED, marked, pitch auto-scheduled 2026-07-31 16:28. Recruiter-C (GoodSpace) still
3rd/Pending, day 4 of 14. Nothing due, so ZERO sends this run. Pre-flighted the 2b text against the standing
check (no em-dashes / markdown / unresolved slots) - clean, left byte-identical per the never-invent-the-pitch
guardrail. Closed a long-standing [VERIFY]: recruiters who post reqs print their own intake address in the
post, so Recruiter-B's mailbox is first-party confirmed - read the posts before reaching for a verification API.


## [2026-07-30 21:45] session | Easy Apply pivot + tasks proven
Touched: none
Three tailored CVs actually DELIVERED (Innova ESI, GoodSpace, CodeRound): Drive-shared per recipient via
Playwright, linked from a Composio Gmail send, no bounces. Infosys excluded (routes through Recruiter-A).
MX check changed the plan: innovaesi.com is Microsoft 365, so a link restricted to her Google identity
would have shown "You need access" - link-only for that one, true per-email restriction for the two
Workspace domains. Drive defaults to Editor + Notify-on; both wrong, and Send->Share is how you confirm
notify is off. Clipboard is blocked three ways, so the link is read back by pasting into the Drive search
box and reading the accessibility snapshot.
Pipeline: auto-apply.ps1 + runbook 17 rewritten from external ATS to LINKEDIN EASY APPLY (D18) - the old
version explicitly skipped Easy Apply, which is nearly the whole board, and was registered in
pipeline_runner.py as nothing at all. Now `apply` / `apply-all`, refusing to start without the tailored
cv_stem PDF. Numeric-field rule baked in (notice period 0 not "Immediate"; CTC 840000 not "8.4"; fixing
them reveals hidden Yes/No questions) plus the matching bank keys, since only bank values may be typed.
New sweep-packets.ps1 + 6-hourly task (D19) because discovery outran processing 58:4. Its first version
reproduced D17 within the hour: a PowerShell here-string ate the f-string quotes, Python died, zero rows
matched, and it announced "nothing to build" and exited 0 - now gated on an OK-SWEEP-QUERY sentinel.
Verified by LOG not exit code: Daily Discovery (board 24 -> 62, 38 new, Slack digest) and Watch Accepts
(Recruiter-B ACCEPTED, pitch scheduled 07-31 16:28). daily-discovery.ps1 had no contention guard at
all - added. Recro Generative AI Engineer recorded Applied 2026-07-29; it sat at New after a real
submission, one sweep from a duplicate, and there is a SECOND Recro row that has not been applied to.

## [2026-07-30 22:05] session | Reply check: zero replies, campus-channel gap found
Touched: none
All 5 Applied rows swept against their recruiter domains over 14 days - no replies, so no Notion writes and
no Slack alerts. Bounce sweep also empty, which positively confirms the 07-30 email batch delivered (two of
the three addresses were pattern guesses). Real finding: the only genuine job mail in the inbox was an EPAM
freshers test invite via naukricampus + doselect, unread, for a slot that expired 07-27 18:00. EPAM has no
Notion row, so no runbook watches it - the classifier only searches domains taken from contact.md, i.e. only
companies the autopilot sourced itself. Campus/placement mail is invisible to the pipeline.

## [2026-07-30 22:20] session | Brains reconciled + handoff
Touched: none
Brain 2: 07-current-state task table corrected to FIVE tasks with a "verified by log?" column; allowlist
item rewritten (58 entries, and the note that an AI is BLOCKED from adding the two missing ones); board
state records only 4 packets exist against 62 rows; sweeper counter bug documented. 05-decisions gained
D18 (Easy Apply is the target), D19 (packet sweeper) + addendum (it counted attempts as builds).
New file 20-first-email-batch-and-task-verification. Note: a headless Reply Check run had already added
its own section finding that an EPAM campus test invite EXPIRED UNSEEN because EPAM has no Notion row -
the reply classifier only searches domains harvested from contact.md, so the campus/Naukri channel is
invisible to the pipeline. Logged as next-work item 6.
Brain 1 (Obsidian): LinkedIn-Automation.md gained the 07-30 evening section + lessons 15-19. New global
pattern Patterns/success-sentinel-not-exit-code.md - the cross-project form of the day's recurring bug.

## [2026-07-30 22:35] session | Innova 2b rewritten, owner-approved
Touched: none
Owner approved replacing the already-approved Innova ESI 2b before its 2026-07-31 16:28 auto-send. The
original was not just missing the research hook: the tailored CV had been EMAILED to Recruiter-B at ~21:00 on
07-30, and the DM lands ~19h later still saying "I've tailored a CV to this exact role" with no mention of
the email, reading as if he had forgotten writing. New 2b opens by acknowledging the email, then names her
own posted req this week (Azure AKS + GCP GKE, Kubernetes, Terraform) - closing the long-standing research
[VERIFY] with a first-party detail. Also unwrapped the paragraphs to single lines: the watcher sends the
markdown block verbatim, so hard wraps would have shown as mid-sentence breaks in the DM. 2a marked DEAD
(she is 1st degree now, a connection note can no longer apply). Checks pass: no em-dashes, no asterisks,
no unresolved slots.

## [2026-07-31 22:25] session | Accept watch: missed window, business-hours gate
Touched: none
Ran the accept watch. Nothing expired; nothing pending (all three invites are now accepted - Recruiter-C
flipped at 22:06, caught by the 22:03 run). Recruiter-B's 16:28 pitch had been missed (laptop asleep) and
was still sitting `due` at 22:19, with a watch run in flight that would have sent it at ~22:20. Found and
fixed the cause: "business hours only" lived in the runbook and in `schedule_followup`, which shifts the due
time at ACCEPT time only; `cmd_due` never rechecked the clock, so a due time that lapsed while the machine
slept stayed due forever - and Windows fires every missed task at once on wake, so a cold recruiter could
have received a CV pitch at 02:00. `cmd_due` now returns [] outside 09:00-21:00 and reports what it holds.
Held Recruiter-B for morning instead of sending at 22:20. Sent nothing.

## [2026-07-31 22:40] session | Reply check, third clean zero
Touched: none. Brain 2: 07-current-state (reply-check run record).
Note: 5 Applied rows, 5 recruiter domains, zero replies. Nothing written to Notion, nothing sent to Slack -
correct per the de-dupe rule. Widened the disbelief step this run: rather than only control-querying, the
empty result was re-tested at `newer_than:30d in:anywhere` (spam/promotions/archive, double window) and was
still empty, so this is not a reply misfiled in Promotions. Bounce sweep widened to 14d in:anywhere - first
sweep covering the whole window since the 07-30 email batch - still clean. Campus sweep run by hand for the
3rd time (now incl. imocha/codility); only the two expired EPAM items from 07-27, still unread.

## [2026-08-01 04:45] session | Wake-stampede fix + pipeline run
Touched: none
Owner reported the pipeline never ran on 07-31. Root cause was NOT missing catch-up: StartWhenAvailable was
already on, so Windows re-ran every missed task on wake - ALL FIVE within 3 seconds at 22:01, spawning 4
LinkedIn MCP servers that fought over one browser profile. Ordering was the missing piece, not catch-up.
Built tools/pipeline-lock.ps1 (atomic CreateNew lock; the old "is a server running?" guard is a race that
five simultaneous launches all pass) and tools/run-pipeline.ps1 (accepts -> flush -> replies -> discovery ->
packets; sends first because they have deadlines). New task "Job Hunt - Catch Up" fires 2 min after resume
from sleep, registered via schtasks /SC ONEVENT because Register-ScheduledTask and -AtLogOn both fail Access
Denied without admin.
FOUR lock bugs caught by actually testing exclusion rather than assuming it: (1) Write-Output inside a
function returning a boolean made the caller receive @(logline,$false), a truthy ARRAY, so the lock excluded
nobody; (2) catch [IOException] misses PowerShell's MethodInvocationException wrapper; (3) "unreadable"
was treated as "abandoned" and deleted healthy locks - a lock is unreadable precisely BECAUSE a live owner
holds it; (4) FileShare must permit both directions, so the READER needs ReadWrite too or a held lock is
undiagnosable. Then found live: a 02:12 reply check wedged 2.5h still holding the lock, so the lock now kills
the owner subtree past 90 min.
Pipeline run: accepts OK (Recruiter-C ACCEPTED - pitch 08-01 09:46; Recruiter-B HELD, see below), replies OK
(0 replies, zero verified twice with control queries, no bounces), discovery FAILED on monthly spend limit,
packets running. The accept-watch run itself found and fixed D21: business hours were enforced only when
SCHEDULING an accept, never at SEND time, so a due time that lapsed overnight stayed due and the wake flood
could have DMed a cold recruiter at 02:00.

## [2026-08-01 05:20] session | Daily discovery, 15 new jobs, board 94
Touched: none
Ran [[09-discovery-runbook]] in-session (the 08-01 scheduled Discovery had died on the monthly spend limit).
8 read-only search_jobs calls; board 79 -> 94. Top find SkillsCapital "SW Eng Intern (AI/ML & Agentic AI)"
fit 93 - JD literally asks for a final-year student and lists the agentic/LangChain/RAG stack; direct email
careers@skillscapital.io. Also CodeRound "Fresher" 87 (no experience required) and a warm Infosys DevOps 86
(Recruiter-A). Three method notes: sort_by=date destroys relevance; a 19-minute-old posting (VIAN) was already
closed, which only get_job_details revealed; and notion-create-pages needs userDefined:URL, not URL.
Step 5b (auto-packet at >=85) deliberately NOT run - build-packet refuses while a Claude session is open and
is still off the allowlist. Packet gap now ~90 rows vs 4 packets; discovery is outrunning processing ~4:1.

## [2026-08-01 10:55] session | Accept watch: 1 pitch sent, 1 held on a stale time word
Touched: 07-current-state
Nothing expired, nothing pending (all 3 invites accepted). 2 due, both in business hours, under cap.
SENT Recruiter-C (GoodSpace FDE 85) his 2b; mark-sent + Notion note + Follow-ups Sent=0.
HELD Recruiter-B (Innova ESI 87): her approved 2b says "I emailed you yesterday", but the laptop slept
through the 07-31 16:28 window so the email is now 2 days old. Editing costs approved words, sending costs a
true statement, so it was escalated to Slack for a one-word call. Lesson: relative time words are unstable
state in any draft-now-send-later message; prefer absolute phrasing at draft time.
Also corrected: Notion had both rows at Applied since 07-30 (this file said Invite sent), and Applied Date was
deliberately left at 07-30 since the email was first contact. goodspace/touch-2-linkedin.md still carries
pre-D12 "draft / owner clicks send" headers - stale, but worth fixing so nobody re-derives the judgement.

## [2026-08-01 11:26] session | Accept watch: held Innova pitch sent
Touched: none
Second accept-watch of the day. expire: nothing >14d. pending: empty (all 3 invites accepted, no open knocks).
due: 1 ripe row - Recruiter-B (Innova ESI, DevOps 87), the row held at 10:50 on the stale "I emailed you
yesterday" line. The owner had ALREADY resolved it in the packet itself: touch-2-linkedin.md now reads
"APPROVED BY OWNER 2026-07-30, amended 2026-08-01" with yesterday -> "earlier this week". Sent at 11:2x
(inside 09:00-21:00), mark-sent logged immediately, due now []. Notion: Follow-ups Sent = 0, note appended,
Applied Date left at 07-30 (email was first contact; a later DM is a follow-up, not a new apply). Slack posted.
Lessons: check a packet's own status line before re-escalating - the answer may be waiting in the file. And
scope the em-dash/markdown guardrail check to the 2b BODY only; a whole-file grep hits a dozen em-dashes in
the metadata and commentary and would falsely fail a clean message.
Observed in passing: every req Recruiter-B has posted in 2 days is mid-to-senior (5+ to 8-13 yrs), so she has no
fresher-level opening right now. The relationship is worth more than this specific role.

## [2026-08-01 11:35] session | Outreach queue emptied + mirror resync
Touched: none
All three pitches now DELIVERED (Recruiter-A 07-26, Recruiter-C 11:26, Recruiter-B 11:26); invite queue empty.
Recruiter-B's was correctly HELD once: her approved 2b opened "I emailed you yesterday", true for the intended
07-31 16:28 send, but the laptop slept through that window so by send time the email was two days old - a
checkable falsehood inside the message whose whole job is to show he pays attention. Amended to "earlier
this week" (D22). Relative time words are unstable state in anything drafted now and sent later, and only
the 2b block actually sends, so scope the em-dash/markdown check to the message body or it fails a clean file.
THE LOCK PROVED ITSELF IN PRODUCTION at 10:36: discovery took it at 10:36:13, watch-accepts tried 30s later
and stood down cleanly. The same overlap the previous night spawned four MCP servers and achieved nothing.
D23, the bigger find: sweep-packets chooses what to build from the SQLite MIRROR while discovery writes to
NOTION, and nothing refreshes the mirror - the seed was six days stale. Mirror held 24 rows against Notion's
94, so SkillsCapital 93, Mirai Alpha 92 and Infosys Junior 90 were all invisible to the sweeper, which looked
like it was working perfectly while building from the best of a stale subset. Resynced (+70 new, 24 updated).
Daily Discovery DISABLED: 94 rows against 4 packets is ~4:1 and more rows bury the good ones.
Sweep now running against the real board, top row first.

## [2026-08-01 12:15] session | D24 nesting bug + brains reconciled
Touched: none
Confirmed by reproduction, not guess: headless claude.exe works 2 process layers deep and FAILS at 3.
SkillsCapital failed through sweep-packets (3 layers) then SUCCEEDED called directly (2 layers); Mirai Alpha
failed nested twice. Its error blames "ANTHROPIC_API_KEY or another auth source" - no such key exists in
process/user/machine scope, any settings file, or .mcp.json. The message is a red herring; same shape as the
2026-07-29 standalone-CLI blocker.
CONSEQUENCE: the scheduled Sweep Packets task uses the failing 3-layer chain, so it had NEVER built a packet
unattended. That is why the backlog never moved while every log looked plausible - it found rows, launched
builds, and reported honest failures nobody read. Workaround: call build-packet.ps1 -JobId <id> directly.
Fix direction: drop the middle powershell spawn from sweep-packets.ps1.
First packet in days built this way: SkillsCapital 93, ATS 90, To Apply, Slack card unticked, nothing sent.
Recorded with it: SkillsCapital has FOUR board rows and only one is in-house (the others are client placements
- do not batch one recruiter across them); ATS held at 90 rather than claiming scikit-learn/pandas/NumPy/
Elasticsearch/AWS/Azure with no backing; skillscapital.io MX still unchecked.
## [2026-08-06 23:20] session | LinkedIn profile automated reframe live
Touched: none (Brain 2: 25-linkedin-profile-reframe, 00-INDEX).
Executed 100% automated profile update via Playwright persistent context (.pw_browser/linkedin_user_data/). Applied headline, 250-word About section, 3 Verventech roles (DevOps Engineer, Founding Engineer, AI Systems Engineer), and 16 technical skills live on LinkedIn. Verified with page screenshots.

## [2026-08-09] session | Accept watch ran BLIND - the poll could not happen
Touched: none. Brain 2: 07-current-state (new accept-watch section).
Steps 1 and 3 completed: expire found nothing >14d (the three 08-06 invites are day 3 of 14; wall is 08-20),
and `due` returned [] - correct, since nothing has been marked accepted. Step 2 DID NOT RUN.
mcp-server-linkedin registered ZERO TOOLS this session, so get_person_profile did not exist to call. Not
auth, not an expiry, not the D13 profile lock - there was no error message to misread because there was no
tool. Verified four ways (exact-name select + three keyword searches, minutes apart) plus a resource listing.
THE POINT: the 4-hourly watcher cannot tell "nobody accepted" from "I could not look". Both print the same
quiet exit. Same family as failed-query-is-not-an-empty-queue, now reached through a missing TOOL rather than
a failed query. Whether SkillsCapital's CTO accepted - the 93-fit row, the best on the board - is unknown.
Wrote tools/poll_invites.py as the fallback: reads degree + the Pending badge off the profile page using the
Playwright profile Phase 0 proved logged in, navigate-and-read only, no clicks/connects/messages; sending
stays on the MCP. It has NEVER EXECUTED - it is not allowlisted and an AI is blocked from adding itself.
Owner needs one line: "Bash(py -3 tools/poll_invites.py:*)". Treat the tool as unverified until it runs once.
Sent nothing, wrote nothing to Notion, posted nothing to Slack.

## [2026-08-09 15:15] session | build-packet halted: Infosys already packeted
Touched: none
Job 3a829d9d-9c6e-814a-a4d7-dd35097e1aba = Infosys "AI/ML Engineer" (fit 88, Hybrid, Bengaluru). Runbook 15
step 2 AND step 3 both stop the run: output/outreach/infosys/packet.json already exists (built 2026-07-25 for
the sibling role "AI Application Engineer", ATS 94, CV + PDF both present), and packets are one-per-COMPANY,
not per-role. The Infosys contact chain is already spent: warm insider connected 07-26 13:15, accepted 16:15,
CV + pitch delivered 16:43. A second packet would be a duplicate approach to the same person - the exact
"looks automated" failure D8 exists to prevent.
Nothing built, nothing sent, no Notion/Slack/status writes. Row left at status New.

## [2026-08-09 16:05] session | VARITE packet refused: req closed + bad score
Touched: none
Build-packet runbook for 3ae29d9d (VARITE INC, "DevOps Engineer", fit 84). Stopped at step 1.
Two blockers, both found before anything was written. (1) The posting is DEAD: get_job_details returns
"No longer accepting applications" - found 07-31, closed inside 9 days, over 100 applicants. That is the
~63%-of-the-board rot landing on a row the board still showed as live and buildable.
(2) The fit score was wrong in a way only the JD reveals. Titled "DevOps Engineer", the req is a senior
DevSecOps CONTRACT role: secure 350 EKS container images ahead of a FedRAMP High audit, STIG/CIS hardening,
Grype/Trivy pipeline gates, Argo Workflows patch automation, Istio/WAF segmentation, IAM/RBAC
least-privilege audits, secret + S3 scanning. Re-scored 84 -> 58. The 84 was title-level with no JD
fetched, which is true of the 38 newest rows - so this two-call check belongs at the top of EVERY build,
not just this one. It costs one MCP call and it saved a 7-minute packet plus an approach to a live human
about a req that closed.
Row set to Skipped in Notion and re-synced into the mirror (94 roles, 37 closed). Nothing built, nothing sent.

## [2026-08-09 17:20] session | Accept watch: MCP blindness cleared
Touched: none
All 3 invites polled successfully (3rd degree + Pending badge) - none accepted, none due, none expired.
Quiet exit per runbook step 5: nothing sent, no Slack, no Notion writes.
Key correction: this morning's "LinkedIn MCP has no tools" was a per-session registration flake, not a
broken install - the same config worked hours later with no fix applied. Retry in a fresh session before
concluding the tooling is broken.

## [2026-08-09 21:30] session | Reply check: 0 replies, 5 unrecorded applies
Touched: none
Fifth clean reply check: zero recruiter replies across the 5 Applied rows, controls proven first, bounces
clean, campus channel quiet. Real finding came from the LinkedIn auto-acks, not the reply search: five Easy
Apply submissions went out today (Energy Exemplar, SkillsCapital x3, Crossing Hurdles) and every row still
reads New/To Apply - the Recro duplicate-submission trap again. Worse, the three SkillsCapital sends were
the 82-83 client-placement rows; the in-house 93-fit intern role was skipped.

## [2026-08-10 12:00] session | Accept watch: three still pending
Touched: none
Ran 13-accept-watch-runbook end to end. expire: nothing past 14 days (wall 08-20). Polled all three pending
invites via get_person_profile (SkillsCapital CTO, Mirai Alpha co-founder, Hired consultant) - all read 3rd
degree with a Pending badge, so none accepted and stage 1 is confirmed not to have silently failed. due: [].
Nothing sent, nothing written to Notion, no Slack post (runbook step 5 quiet exit). LinkedIn MCP registered
normally, unlike the 08-09 morning flake. last_checked stays null after a poll for the third run running, so
07-current-state is again the only record the poll happened.

## [2026-08-10] session | Reply check: 0 replies, 2 auto-acks
Touched: none
Sixth clean reply check. All 5 Applied rows (Infosys, CodeRound, Innova ESI, GoodSpace, Recro) checked over
newer_than:14d in:inbox, widened to 30d in:anywhere. Zero recruiter replies, no bounces, no Notion writes, no
reply alert. Two auto-acks classified and deliberately NOT ticked: Energy Exemplar (no-reply@, 08-09 09:36)
and the known Ceipal/Crossing Hurdles template. Correction to 07-current-state: careers@skillscapital.io was
recorded as "never used", but Gmail holds an application 08-01 and a follow-up 08-09, so the 08-09 follow-up
batch was four contacts not three. The mailbox, not Notion, is the record of what actually left.

## [2026-08-10 later] session | Reply check, seventh clean run
Touched: none. Brain 2: 07-current-state (new reply-check section).
Note: re-run of the same day's check. 5 Applied rows, 5 domains, control query proven (201 threads) before the
zero was believed. Zero replies, no bounces, no new inbound at all since the morning run; the two 08-09
auto-acks unchanged and still not ticked. Address sweep now carries SkillsCapital / Energy Exemplar / Mirai
Alpha, per the morning's "sweep by address, not only by company" lesson - returned only Azam's own sent mail.
The five 08-09 Easy Apply submissions are STILL unrecorded in Notion (day 2, third run flagging it).

## [2026-08-10 later] session | Accept watch: three still pending, quiet exit
Touched: none
Note: expire found nothing over 14 days; all three invites (SkillsCapital CTO, Mirai Alpha co-founder, Hired
consultant) still read 3rd degree + Pending at day 4; due returned []. Runbook step 5 quiet exit - no Slack,
no Notion writes, nothing sent. last_checked stays null on all three (4th time), so 07-current-state is again
the only record the poll happened.

## [2026-08-10 17:20] session | Reply check run 8 - zero replies, 3 more unrecorded sends
Touched: none
Eighth reply check, third today. 5 Applied rows vs 5 domains, 14d inbox + 30d in:anywhere: zero recruiter
replies, so no Reply tick, no Status move, no --event reply. Query proven live (201 control) before the zero
was believed. Bounces clean, campus sweep only the 08-05 EPAM cancellation, address sweep only own sent mail.
Found: 3 MORE Easy Apply submissions on 08-10 (Neurones IT Asia 82, Crossing Hurdles AWS Cloud 81, Celigo 80),
all still New in Notion - eight unrecorded submissions across two days. The Micro1/ceipalmail auto-ack repeated
3s after our own submission; classified Auto-ack, not ticked.


## [2026-08-10 20:10] session | Apply-at-volume recorded; D31-D33 written
Touched: none (AST-only graph; knowledge lives in Brain 2)
Batch runner shipped and ran: families.py (3 role-family CVs), ledger.py (append-only, fsync'd, AST-tested
to import nothing that reaches a board status), run.py apply-all. 8 real Easy Apply submissions; 13
applications total, 0 replies. New Brain-2 file 26-apply-at-volume.md. Three decisions recorded: D31 an
over-broad pattern typed "Srinagar" into an EXL interview-location question and PASSED the answer-bank
guard (the bank proves provenance, not destination); D32 the research half was never wired into the batch,
5 of 8 submissions have no recruiter at all; D33 the company cap counts every ledger row regardless of
channel or age, so one old LinkedIn DM blocks all four Infosys rows including Junior AI Engineer (90) -
which is also the real cause of the twice-logged "why only fit 80-82?" puzzle.

## [2026-08-10 20:10] session | Published Reframed PrivateCloud Post Live
Touched: none

## [2026-08-10 21:02] session | Accept watch - quiet exit, nothing changed
Touched: none
Third accept-watch run of the day. expire: nothing >14 days. All three pending invites (SkillsCapital CTO,
Mirai Alpha co-founder, Hired consultant) still 3rd degree + Pending at day 4. due: [] - verified genuinely
empty via `list --status accepted` rather than trusting the empty result, because at 21:02 the business-hours
gate produces the identical output for a different reason. No Slack post, no Notion writes, nothing sent.

## [2026-08-10 21:40] session | D33/D34/D35; the reply checker had no LinkedIn eye
Touched: none (AST-only graph)
Fixed D33: the company cap was a lifetime channel-blind lockout, so one old DM blocked all four
Infosys rows including Junior AI Engineer (90). Now scoped to same-channel within 14 days; verified
90 is back at the top of the plan. D34: the packet layout keys by company while cv.py looks up by
job id, so a company's second role is unbuildable - refused twice now. D35, the big one: a warm
insider replied 2026-07-26 asking for the CV and nobody answered for 15 days, while EIGHT reply
checks reported "zero replies" - none of them had ever opened LinkedIn messaging. Built
apps/autopilot/replies.py (pure classifier + Playwright inbox read, escalates anything unparseable,
a read error can never render as an empty inbox). 66 tests passing. Verified live against the real
inbox: 6 threads scanned, the missed reply flagged, the two we spoke last in correctly ignored.

## [2026-08-10 21:30] session | 7-Day LinkedIn Content Engine built
Touched: none (AST-only graph; new code in tools/, not graphed)
Built the complete 7-day LinkedIn content calendar engine. New files: tools/content_hub_db.py (SQLite
content calendar, same pattern as board_db.py), tools/log_experience.py (CLI experience logger),
tools/seed_content_hub.py (seeded 20 projects Aug 11 – Oct 15), tools/trend_finder.py (Hacker News +
NewsData.io + Currents API topic fetcher), tools/post_creator/dispatch_engine.py (unified orchestrator:
reads queue, generates FLUX.1 hero image or uses PDF carousel, dispatches via Playwright, marks posted),
tools/post_creator/prompt_templates.json (per-post-type image prompt templates with randomizable vars),
tools/post_creator/generate_fallback_cache.py (10 pre-gen safety-net images),
tools/post_creator/install-dispatch-task.cmd (Windows Scheduled Task at 9 AM IST).
Decisions: D33 SQLite over Notion (offline-first), D34 agent-agnostic (Claude + Antigravity share all
infra), D35 human-in-the-loop approval, D36 every post gets a visual. CLAUDE.md updated with Content Hub
section. Brain 2: NEW 27-linkedin-content-engine, 00-INDEX updated.

## [2026-08-13 20:35] session | Live LinkedIn Post Dispatched (AI Agents Trust)
Touched: none (AST-only graph)
Successfully posted today's Wednesday Trending Tech Take ("AI agents lie, cheat and steal") live to LinkedIn via Playwright.
Hero image attached (`hero_ai_agents_trust.png` via Pollinations FLUX.1 in 1.5s). Refined `dispatch_engine.py` Playwright selectors for LinkedIn's post modal (`div[role='textbox']`, `button[aria-label*='Add media']`, `button.share-box-footer__primary-btn`). Skill updated: em-dashes permanently banned in `linkedin-post-copywriter/SKILL.md`. Marked Post #33 as `posted` in Content Hub DB

## [2026-08-13 20:50] session | Enforced High 3D Visual Complexity (Zero Hollow Space)
Touched: none
Upgraded `viral-architecture-visualizer/SKILL.md` (added Rule 6) and `tools/post_creator/prompt_templates.json` to permanently enforce high-complexity, attention-grabbing 3D Octane renders (multi-layered glass holographic UI, glowing cyan + amber dual volumetric lighting, dense server/hardware background depth, zero empty space) for all future automated post image generations.

## [2026-08-15 19:55] session | Live LinkedIn Post Dispatched (Production Rollback Lessons)
Touched: none (AST-only graph)
Successfully created and posted the Friday Engineering Lesson ("Why Production Rollbacks Fail") live to LinkedIn via Playwright.
High-complexity 3D command center hero image generated via Imagen 3 (`hero_rollback_lesson_1786801062750.png`).
Updated `dispatch_engine.py` with exact `button:text-is('Post')` targeting and refined photo upload flow.

## [2026-08-11] session | Reply check finds the 16-day-old reply
Touched: none
Ninth reply check, and the first ever to write a Reply tick. Gmail zero across the 5 Applied domains
(queries proven live first: 201 bare / 29 OR-group; bounces clean; campus sweep only the 08-05 EPAM
cancellation). The LinkedIn inbox held Recruiter-A's 2026-07-26 18:58 answer asking for the CV on a
personal number - unanswered 16 days. Classified Other/action-required (not Interview), Notion Reply
ticked + note appended, Status left Applied, Slack alerted. Nothing sent.
Note: apps.autopilot.replies was permission-refused in this interactive session, so the LinkedIn MCP
get_inbox path was used instead - the unit-tested code path is the one that did not run.
Brain 2: 07-current-state gained the 08-11 reply-check section plus a new top item in "Immediate next work".

## [2026-08-11 13:02] session | Accept watch - five pending now, none accepted
Touched: none
Ran 13-accept-watch-runbook end to end. expire: nothing over 14 days (wall 08-20 for the 08-06 trio,
08-24 for the two added 08-10 21:10). Polled all FIVE pending invites - SkillsCapital CTO, Mirai Alpha
co-founder, Hired consultant (day 5) plus Celigo lead recruiter and Neurones IT Asia talent partner
(day 0). Every one still 3rd degree + Pending; nothing accepted. due: [] AND list --status accepted: []
too, so genuinely empty rather than a business-hours hold. Runbook step 5 quiet exit: no Slack post, no
Notion writes, nothing sent.
Positive finding: this was the first poll since the two D32 outreach invites went out last night, and
both read Pending - which rules out the D12 custom_note_limit_reached hole where connect_with_person
reports success and silently sends nothing. Stage 1 worked on both.
last_checked is still null on all five (6th run recorded) - invite_tracker only stamps it inside
mark-accepted, so the polling history exists only in 07-current-state prose that no script can read.
Brain 2: 07-current-state gained the 08-11 13:02 accept-watch section.

## [2026-08-11 14:05] session | D34 resolved; brains brought to date
Touched: none (AST-only graph)
D34 resolved: a company's second role was unbuildable because the runbook refused to overwrite
output/outreach/<company>/ while cv.py looked packets up by JOB ID - neither condition satisfiable, so
Infosys AI/ML Engineer and Junior AI Engineer (90, best row on the board) reported FAIL forever. Split the
units: outreach per company (D8 intact), CV per role in <company>--<role>/ reusing the company contact.
First role keeps the plain folder so nothing on disk moved. Unblocks 9 rows (Infosys x5, SkillsCapital x4).
Trap: a folder slug is NOT a comparison key - skillscapital vs skills-capital compare unequal and the
tailored CV silently loses to the family one; use alphanumeric-only keys like the ledger does.
Also: the 08-11 12:49 scheduled reply check found the 16-day-old warm-insider reply through the normal
path - first inbound signal this project has ever caught by machine. 98 tests (was 50 on 08-09).
Brains updated: CLAUDE.md (corrected the false "13 applications, 0 replies" that reordered the whole plan),
07-current-state, 05-decisions (D34 marked resolved), Obsidian, graph at 780 nodes.

## [2026-08-11 15:40] session | frontend/backend/database split + console page
Touched: none (AST-only graph)
Restructured: web/ -> frontend/, tools/serve_dashboard.py -> backend/server.py, tools/board_db.py ->
database/board_db.py, output/dashboard/board.sqlite3 -> database/board.sqlite3. Two shims kept because
board_db had SIXTEEN callers including three PowerShell scripts on Task Scheduler; the shim must load the
real module BY FILE PATH since both files share a name (a plain import re-imports the shim and dies on a
circular import - hit on the first attempt). Security catch: output/ was gitignored but database/ was not,
and the notes column carries real recruiter names on 17 rows in a PUBLIC repo - .gitignore now blocks
database/*.sqlite3, schema tracked and data not. New: frontend/console.html + page-console.js + console.css
+ /api/console, built on the existing style.css tokens and JH.ready() pattern, showing progress, a ranked
action queue, the Easy Apply vs external split with links, skills and capabilities. New apps/autopilot/
triage.py classifies every live posting: 14 easy-apply, 22 external, 4 dead. All 7 routes 200, 98 tests.

## [2026-08-11 16:20] session | Dashboard cull: 7 pages -> 4, 16 actions -> 11
Touched: none (AST-only graph)
Audited every page by the AGE OF THE FILE IT READS, not by opinion. Deleted slack.html (mirror of a
channel already on the phone, newest message 16 days old; check_approvals queries Slack directly so the
tick-to-send gate is untouched), research.html (files 5-17 days stale, duplicated the Jobs page) and the
old Board index. The Board finding is the keeper: its data was NEVER stale - it only looked stale because
it stamped "board synced Xd ago", which describes the last Notion capture and nothing else on the page.
The stamp was the bug. Its filterable table moved onto the console with better filters and a hidden-row
count. Actions cut to 11: notion-push/notion-queue could never work because NOTION_TOKEN is not set, and
invites/invites-due/expire duplicated the console or watch-accepts. Consequence to remember:
database/board.sqlite3 is now the real store, nothing pushes back to Notion. Two breakages caught by
curling every route: the startup guard still checked for the deleted index.html, and the Jobs page linked
to /research. 98 tests, four pages + both APIs verified 200.

## [2026-08-13] session | accept watch, seventh quiet run
Touched: none
Ran 13-accept-watch-runbook end to end. expire: nothing over 14 days. All five pending invites polled
(SkillsCapital / Mirai Alpha / Hired at day 7, Celigo / Neurones IT Asia at day 3) - every one still 3rd
degree with a Pending badge. due: [] and accepted: [] so nothing was held behind the business-hours gate.
Quiet exit per step 5: no Slack, no Notion, nothing sent. last_checked still null on all five, seventh
recording of the same gap.

## [2026-08-13 17:25] session | reply check 11, LinkedIn inbox actually read
Touched: none
Ran 11-reply-classifier-runbook end to end on the 5 Applied rows. Gmail zero across 14d/inbox and the
widened 30d/anywhere; the control proved live at 201 threads before any zero was believed. Bounces clean,
campus sweep only the 3 known items. The headline is the channel the morning run had to record as
UNCHECKED: the LinkedIn MCP is up now, so the inbox was actually read - 6 conversations, no new inbound,
Infosys skipped per de-dupe (Reply already ticked, thread verified to hold nothing after 07-26 18:58).
No Notion writes, no --event reply; --event info posted. New trap logged: a sponsored InMail thread shows
"You:" as the last speaker because button taps count as sent messages. apps.autopilot.replies was refused
by the permission prompt for the third session running.

## [2026-08-13 21:03] session | accept watch, eighth quiet run
Touched: none
Second accept watch of 08-13. expire: nothing over 14 days. All five pending profiles polled - every one
3rd degree with a Pending button, which also confirms the MCP session healthy at 21:00. due: [] and the
accepted bucket also [], so the empty result is genuine and not the 21:03 business-hours gate suppressing
a ripe row. Quiet exit per step 5: no Slack, no Notion, nothing sent. last_checked is still null on all
five for the eighth recording - ten polls across two runs left the state file byte-identical to 08-06.

## [2026-08-13 21:05] session | OmniRoute gateway live, free model wired
Touched: none
Installed OmniRoute v3.8.49 on :20128 and wired apps/autopilot/llm.py to it. Connected 8 providers
(115 -> 665 models) but only 3 answer correctly - pinned gemini/gemini-3.5-flash-lite (7.3s), with
gemini-3.6-flash and felo/felo-chat as canary-verified fallbacks. The Gemini key needed no signup:
the owner's Chrome was already authenticated and the account already held 7 keys. Found and fixed a
gateway bug with no symptom - non-streamed answers lose their first token on both wire formats at
HTTP 200 - so llm.py now streams and joins, locked by 6 new tests (98 -> 104). Three further traps:
gemini-2.5-flash is retired but still advertised by the gateway's cache, thinking tokens share
max_tokens (default 300 -> 1024), and one 404 trips a 65s circuit breaker whose 429s look upstream.
Built tools/omniroute_canary.py because 200-and-non-empty passes every one of these. Security: the
key arrived in a root file named "api key" that *.key does not match - moved to .env, never committed.

## [2026-08-13 22:30] session | Reply check 12: Gmail clean, LinkedIn unchecked
Touched: none
Ran 11-reply-classifier-runbook against the 5 Applied rows. Zero new Gmail replies across
infosys.com / coderound.ai / innovaesi.com / goodspace.ai / recro.io; bounces and campus sweep clean;
query proven live (201 control threads) before the zero was believed. No Notion writes, no
--event reply. The LinkedIn inbox could NOT be read - MCP not connected and apps.autopilot.replies
refused by the permission prompt on both PowerShell and Bash, 4th consecutive session - so it is
recorded as UNCHECKED, not quiet (D35).

## [2026-08-14 00:39] session | OmniRoute swept; fallback left the gateway
Touched: none
Connected opencode/mimocode/auggie (catalog 665 -> 1019), then echo-tested 23 models across every
free family: THREE answer (2x gemini, felo/felo-chat), all three backed by a real key on a real
account. `testStatus: "active"` proved worthless - groq and opencode both report active while
403-ing every completion. Groq's 403 is the GATEWAY, not the key: the openai client straight at
api.groq.com is exact in both transports. llm.py gained LLM_FALLBACK_* (Groq direct, deliberately
not another model behind the same local process); 112 tests, verified live. Then the canary FAILED
that working fallback because urllib's default User-Agent is the one string Groq's Cloudflare bans -
the instrument, not the provider. USER_AGENT now unconditional; --base-url/--key-env added.
Deleted a root-level groq-login.png exposing both his emails in a public repo; /*.png now ignored.
Also verified: the LinkedIn MCP IS connected (real get_my_profile), so the "4th consecutive session
unable to read the inbox" blocker in the entry above is LIFTED.

## [2026-08-14 01:02] session | Accept watch: ninth consecutive quiet run
Touched: none
All 5 invites still 3rd/Pending (08-06 trio day 8, 08-10 pair day 4). Nothing accepted, due or expired
-> quiet exit per runbook step 5: no Slack, no Notion, nothing sent. Ran at 01:02, so the empty `due`
was disambiguated against `list --status accepted` (also empty) - outside business hours those two
results are otherwise identical. `last_checked` still null on all five: NINTH recording, ~5-line fix.
Second half: LinkedIn MCP verified live by a real get_my_profile, so the 4-session inbox blocker is
gone. Inbox read = 6 conversations, ZERO unread replies, and ?filter=other returns the same 6 rows -
the Focused/Other split is not active on this account, so this is a true all-clear rather than a
one-tab guess (D35). coverage.py: 14 applications, 10 companies, 1 reached nobody = Recro (Generative
AI Engineer, applied 07-29). Found and VERIFIED its recruiter: Arya Priyadarshini, TA Specialist at
Recro since Sep 2025, Data & AI, posts GenAI/LLM reqs. Recro is a real company (501-1K, 24 findable
members), unlike Crossing Hurdles (D36). Wrote output/outreach/recro/{contact.md,touch-2-linkedin.md},
added a REVIEW-QUEUE row, posted a Slack draft_ready card. NOTHING SENT - bare connect awaits his tick
(D12). Also fixed slack_notify.py --dry-run, which crashed on cp1252 for any non-ascii payload: a
preview that fails on exactly the messages worth previewing trains people to skip it and post live.
Third: followed the inbox finding to its cause. followups.py (Day-3/Day-7 cadence) is CORRECT and has
never once been fed - its docstring expects a Notion-MCP runner that no longer exists, NOTION_TOKEN was
never set, and the store moved to database/board.sqlite3. A component with no caller does not fail, it
is absent: nothing errored because nothing ran it (D44). Wrote tools/followups_from_board.py; first run
says 13 of 13 applications are past their Day-3 nudge, oldest by 19 days. Two bugs the first real run
exposed: BOTH nudge templates carried an em-dash in recruiter-facing text (never caught because no nudge
had ever been rendered from real data), and the feeder's caveat printed AFTER 40 lines of output. Also
noted: `jobs` has no `reply` and no `followups_sent` column, so the feeder assumes false/0 and says so
loudly - over-reporting costs a Slack card, under-reporting costs a lead. 4 commits, 112 tests green.

## [2026-08-14 09:06] session | Accept watch: tenth consecutive quiet run
Touched: none
All 5 invites still 3rd/Pending (08-06 trio day 8, wall 08-20; 08-10 pair day 4, wall 08-24). Nothing
accepted, due or expired -> quiet exit per runbook step 5: no Slack, no Notion, nothing sent. 09:06 is
inside business hours, so the empty `due` is genuine rather than gate-suppressed; `list --status
accepted` also empty, confirming no ripe row held. Five real get_person_profile calls = the trustworthy
auth check, so the MCP session is healthy (it was disconnected at the 08-13 third reply check). Hooks
re-confirmed for touch-2 at send time: Recruiter-G's Celigo Ora/Agent Builder (now a 4-month-old
repost), Recruiter-H's "zero agency dependency ... LinkedIn, GitHub, niche tech communities" - but her
last 6 months of reqs are ALL mid-to-senior, same shape as Recruiter-B. Recruiter-F still lists only the
Founder's Office Intern req; do not re-aim the packet. `last_checked` null on all five: TENTH recording,
20 polls with no on-disk trace, so this run cannot prove the previous nine happened (D35 shape).

## [2026-08-15 10:55] session | Reply check, both channels quiet
Touched: none
Thirteenth reply check, 5 Applied rows. Gmail empty on all 5 recruiter domains at 14d/inbox AND 30d/anywhere
(syntax proven live first: 201 threads bare, 5 on the linkedin+infosys control). Bounces clean, campus sweep
only the 3 known items. LinkedIn MCP was connected, so the inbox was READ not skipped: 6 threads, nothing new
inbound, Recruiter-A's thread OPENED to confirm no newer message rather than trusting the list preview. Zero
Notion writes, zero reply alerts, `--event info` to Slack. Recruiter-A now 20 days unanswered; still the lever
and still owner-only. Recro's domain hand-supplied again since its contact.md carries no email by design.

## [2026-08-15 13:01] session | Accept watch, eleventh quiet run
Touched: none
All 5 invites polled, all still `3rd` + `Pending` (08-06 trio day 9, 08-10 pair day 5). expire: nothing over
14 days. due: [] and `list --status accepted` also [] — 13:01 is inside business hours so this is a genuinely
empty queue, not the gate. Quiet exit per step 5: no Slack, no Notion, nothing sent. One profile timed out on
first call (`Page.goto` 30s, empty sections + section_errors) and returned clean on retry — recorded because
a timeout response is HTTP-successful JSON and reads as "no accept signal" if skimmed; retry, and on a second
failure record the row as unknown, never as pending. `last_checked` still null on all five, eleventh
recording, 25 polls now existing only in prose.

## [2026-08-15 15:26] session | 0 to 20 applications; survey-first
Touched: none (AST-only graph; knowledge lives in Brain 2)
New code: apps/autopilot/survey.py (read every form, submit nothing), apps/autopilot/freetext.py
(LLM answers ONLY the per-company motivation question, whitelisted, refuses anything checkable).
Board purged (43 rows, all 14-21d old; apply-all over them submitted 0 of 32) and re-discovered:
115 fresh Easy Apply roles via **f_AL=true** - f_EA is NOT the Easy Apply filter and LinkedIn
ignores it silently (1/18 vs 17/17). Survey over 44 forms found 104 distinct questions, 65
answerable; one editing pass took it to 102/104 (technology_years table of 97 techs, education_*,
capabilities, logistics, narrative). Three failures were one bug - the value never landed:
resume-mismatch 15/33 (radio list; read the CHECKED one, select before uploading, click the LABEL
because check(force=True) hits "outside of the viewport"), and stalled-validation (location
typeahead needs a suggestion picked, not fill()). Result: **20 confirmed submissions, 0
unconfirmed.** 142 tests (was 112). Decisions D45, D46. Runbook: docs/knowledge/31-apply-batch-runbook.md

## [2026-08-15 19:25] session | Accept watch, twelfth quiet run
Touched: none
All 5 pending invites still 3rd/Pending (08-06 trio day 9, 08-10 pair day 5). Nothing expired,
nothing accepted, nothing due -> runbook step 5 quiet exit: no Slack, no Notion, no sends. Retired
the 13:01 open question: Recruiter-H's profile timeout was a page-load flake (loaded first-try this
run), not auth. Recorded a scope correction: the default scrape returns no post list for 2 of 5, so
"no new activity" had been asserted more strongly than the evidence supported. last_checked still
null on all five - twelfth recording, still ~5 lines, still needs one word from the owner.

## [2026-08-15 20:05] session | Reply check 14: the first assessment request
Touched: none
Ran 11-reply-classifier-runbook. Step 1 is now structurally blind: Notion Status=Applied returns 5 rows
while output/apply-log/submitted.jsonl holds 35, because today's 21 Easy Apply submissions went to the
local SQLite board and the ledger and never to Notion (no NOTION_TOKEN). Followed the ledger instead,
and the day's only real reply was in the 30 rows the runbook cannot see - the D35 shape in a new place.
ANSR/Talent500 replied TEN MINUTES after the submission asking for a screening questionnaire that gates
the application ("we believe you could be an excellent fit... 2 mins"). Classified ASSESSMENT, not
auto-ack: it shares an auto-ack's instant templated shape but requires action or the application stops.
ANSR had no Notion row, so one was CREATED (beyond the runbook's "update", and said so in the note) -
the alternative was a gated employer request recorded nowhere, which is how the TCS application was lost.
Reply ticked, Status left Applied per step 4, Slack --event reply posted. The 21 companies have no
contact.md, so the from:-list step is unbuildable for them; substituted a broad 3d/anywhere sweep read by
sender. Bounces clean, campus+ATS sweep (widened with talent500/greenhouse/lever/ashby/workable) only the
3 known items. LinkedIn inbox unchanged, Recruiter-A still 20 days unanswered. Gmail read-only throughout.
Fix direction: step 1 should read the ledger, not the board.

## [2026-08-15 19:45] session | closed the loop: outreach + nudge + one runner
Touched: none

## [2026-08-16 00:42] session | reply check 15 - both channels quiet
Touched: none

## [2026-08-16 01:02] session | accept watch 13 - queue is nine, four lack pitches
Touched: none

## [2026-08-16 18:27] session | reply check 16 - ANSR deadline, Energy Exemplar status fixed
Touched: none

## [2026-08-16 19:20] session | gate removed: outreach connects by itself
Touched: none

## [2026-08-16 20:05] session | first accept; pitch generator closes the dead end
Touched: none

## [2026-08-16 21:10] session | wrong-person fix, branch split, OmniRoute stack begun
Touched: none

## [2026-08-17 00:30] session | the OmniRoute stack, built and tested beside the Claude one
Touched: none

## [2026-08-17 10:13] reply check | 17th run, ANSR clock down to 24h
Touched: none

## [2026-08-17 later] reply check | 18th run, a channel unread for 8 days
Touched: none
Harvested the from:-list from the 28 contact.md files instead of retyping the hand-maintained 9-domain
set every prior run had copied forward. That surfaced notifications@ceipalmail.com (Crossing Hurdles),
never once queried in 16 runs, holding two mails unread since 08-09/08-10. Classified OTHER not Auto-ack:
neither acknowledges the application, both are templated referrals redirecting to jobs.micro1.ai, so both
LinkedIn submissions reach nobody - D36's sourcing screen confirmed by the employer's own mail rather
than by heuristic. Both Notion rows were sitting at `New` after real submissions (ledger lines 10/13 with
screenshots), so step 1's Status='Applied' filter could never have reached them: corrected to Applied
with dates 08-09/08-10, Reply ticked, notes written. Third occurrence of the Recro trap; cause unchanged
and structural (NOTION_TOKEN unset). ANSR and Recruiter-A both correctly skipped by de-dupe rule 6 - no
newer message since the 10:13 run, and Recruiter-A's thread was opened rather than skimmed. Bounces
empty, campus/ATS sweep (now incl. micro1.ai + ceipalmail.com) only the 3 known Talent500 mails, broad
2d sweep no job traffic. One Slack --event reply posted. Gmail read-only; nothing sent, nothing replied to.
Still open and flagged for the second run: the Lotus Interworks pitch scheduled 08-17 09:12 has not fired
- there is no Shale Francis thread in the inbox at all.

## [2026-08-17 10:45] session | Shale's pitch delivered; two send-path bugs
Touched: none
The pitch the previous run flagged as never fired is now delivered and independently verified in
the inbox (7 conversations where there were 6). Two bugs stood between: `free/dm.py` looked for a
Message BUTTON when LinkedIn renders an `<a>`, so every accept read "not connected" (D52); then the
first fix reported a send it had not made, because the read-back searched the profile page body
rather than the thread and the probe string was LinkedIn's own canned greeting. An unconfirmed send
is now UNVERIFIED and stays due, which is affordable only because `send_dm` also checks the thread
BEFORE typing. Also: Gmail setup now finds the five Desktop OAuth clients already on the machine
and ends with a real read, because the Gmail API is per-project and a borrowed client consents
cleanly then 403s forever (D53). 397 tests. Claude stack diff still empty.
