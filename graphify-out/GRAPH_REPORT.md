# Graph Report - .  (2026-08-16)

## Corpus Check
- 110 files · ~0 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1179 nodes · 1776 edges · 90 communities detected
- Extraction: 62% EXTRACTED · 38% INFERRED · 0% AMBIGUOUS · INFERRED: 681 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## God Nodes (most connected - your core abstractions)
1. `LinkedInLoggedOut` - 48 edges
2. `fill_job()` - 16 edges
3. `render()` - 15 edges
4. `FillResult` - 12 edges
5. `Handler` - 12 edges
6. `connect_one()` - 11 edges
7. `build_packet()` - 11 edges
8. `_scan()` - 11 edges
9. `Candidate` - 11 edges
10. `_row()` - 11 edges

## Surprising Connections (you probably didn't know these)
- `Read the LinkedIn inbox and report threads where THEY spoke last.  WHY THIS EXIS` --uses--> `LinkedInLoggedOut`  [INFERRED]
  apps\autopilot\replies.py → apps\autopilot\fill.py
- `Decide who spoke last in one conversation row.      Pure, so the rule is testabl` --uses--> `LinkedInLoggedOut`  [INFERRED]
  apps\autopilot\replies.py → apps\autopilot\fill.py
- `(name, preview) for each conversation in the list.` --uses--> `LinkedInLoggedOut`  [INFERRED]
  apps\autopilot\replies.py → apps\autopilot\fill.py
- `Push waiting threads to Slack.      A scheduled task that only writes to a log f` --uses--> `LinkedInLoggedOut`  [INFERRED]
  apps\autopilot\replies.py → apps\autopilot\fill.py
- `Classify every live board row: Easy Apply, external ATS, or dead.  WHY --- Rough` --uses--> `LinkedInLoggedOut`  [INFERRED]
  apps\autopilot\triage.py → apps\autopilot\fill.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (67): Check, classify_profile(), main(), mark_accepted(), notify(), pending_invites(), Ask LinkedIn who has accepted, instead of asking our own notes.  WHY THIS EXISTS, (state, detail) for a profile we have an outstanding invite to. (+59 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (58): _append_monthly_log(), _apply(), _attach_resume(), _attr_q(), _capture_resume(), check_logged_in(), _close_modal(), Control (+50 more)

### Community 2 - "Community 2"
Cohesion: 0.05
Nodes (41): execute_iterative_architecture_hero(), Iterative Architecture Diagram & 3D Enrichment Studio Step 1: Renders a clean co, render_edge_screenshot(), execute_2step_pipeline(), 2-Step AI 3D Command Center Slide 1 Hero Studio Step 1: Render clean, readable 5, render_edge_screenshot(), Ultimate Cybernetic HUD Architecture Generator (FLUX.1 & Gemini Engine) Combines, generate_upgraded_4slide_carousel() (+33 more)

### Community 3 - "Community 3"
Cohesion: 0.07
Nodes (34): add_idea(), all_posts(), approve_post(), get_next_drafts(), _get_post(), get_posts_by_status(), get_todays_post(), _log() (+26 more)

### Community 4 - "Community 4"
Cohesion: 0.08
Nodes (35): by_base_url(), _chunk(), fake_openai(), Tests for the LLM entry point — specifically the corruption that has no symptom., A silent '' would be treated as an answer downstream. It must be loud instead., A reasoning model puts `thinking` first; content[0].text is not the answer., No text block at all is 'no answer', not an empty string., LLM_STREAM=false exists for providers whose streaming is broken (groq: the     g (+27 more)

### Community 5 - "Community 5"
Cohesion: 0.13
Nodes (23): BaseHTTPRequestHandler, _age(), all_zip(), bootstrap(), build_packets(), console(), _coverage_gaps(), cv_paths() (+15 more)

### Community 6 - "Community 6"
Cohesion: 0.08
Nodes (24): all_rows(), last_sync(), _parse_ts(), pending_notion(), Compatibility shim — the real module now lives in `database/board_db.py`.  WHY T, Parse an ISO timestamp, tolerating a trailing Z and dropping the timezone., Insert or update by Notion page id. Returns (inserted, updated, protected)., Change a job's status from the dashboard. Returns the updated row.      Record (+16 more)

### Community 7 - "Community 7"
Cohesion: 0.07
Nodes (18): _person(), The rules that decide who the owner is asked to connect with.  Every case below, The first live bug: a keyword match with no stated link to the company., A slug is not a comparison key: skillscapital vs Skills Capital., D8 as arithmetic. The single reply this project has had came from a shared-roots, Dropped on the live run: nothing in ROLE_KINDS matched "Team Lead"., check_approvals.py finds cards with `ref:<slug>`. No ref means the tick can neve, It was sent to Slack as though it were a surname: "Er. Faiqa Bilal Rah • 2nd". (+10 more)

### Community 8 - "Community 8"
Cohesion: 0.11
Nodes (27): build_many(), build_packet(), company_slug(), find_company_packet(), find_packet(), find_role_packet(), _key(), Packet (+19 more)

### Community 9 - "Community 9"
Cohesion: 0.09
Nodes (22): Tests for the never-resubmit ledger.  The load-bearing one is test_second_attemp, THE D33 test. Infosys: one linkedin-dm, weeks old, different role., The cap's actual job: Crossing Hurdles got two on consecutive days., Different channel = a different recruiter surface, and often a different team., Asymmetric failure: over-counting costs a skip, under-counting costs a duplicate, already_applied() must stay LIFETIME. Recency scoping applies to the CAP only —, THE test. Recro was submitted 2026-07-29 and must never be attempted again., Aggregators on this board repost the same req under fresh ids constantly. (+14 more)

### Community 10 - "Community 10"
Cohesion: 0.15
Nodes (26): FillResult, answers_today(), board_candidates(), Candidate, cmd_applyall(), cmd_fieldmap(), cmd_fill(), cmd_ledger() (+18 more)

### Community 11 - "Community 11"
Cohesion: 0.08
Nodes (14): _FakePage, _isolate(), The guards that replaced the human tick.  Azam removed the Slack approval gate o, Stands in for Playwright. Records whether the browser was touched at all., A guard refusal is not contact, and logging it would poison already_requested()., `ref:<slug>` is the approval gate's token. A receipt must not look like a reques, Never touch the real connect log — it is the record of who we have contacted., An error means nothing reached them, so the person is still worth contacting. (+6 more)

### Community 12 - "Community 12"
Cohesion: 0.12
Nodes (22): classify(), InboxReport, main(), notify(), Read the LinkedIn inbox and report threads where THEY spoke last.  WHY THIS EXIS, (name, preview) for each conversation in the list., Push waiting threads to Slack.      A scheduled task that only writes to a log f, Decide who spoke last in one conversation row.      Pure, so the rule is testabl (+14 more)

### Community 13 - "Community 13"
Cohesion: 0.19
Nodes (25): actions(), bars(), capabilities(), chartChannel(), chartFunnel(), chartKind(), chartTime(), esc() (+17 more)

### Community 14 - "Community 14"
Cohesion: 0.14
Nodes (20): ago(), api(), boot(), clear(), copy(), el(), esc(), fitCell() (+12 more)

### Community 15 - "Community 15"
Cohesion: 0.1
Nodes (18): _msg(), The message a recruiter actually reads.  `watch-accepts` sends the exact 2b text, A hand-written pitch with a real hook is strictly better and must survive a back, The single most recognisable AI tell in this project's own style rules. Two temp, D22: written now, sent hours later on a randomised delay. "Yesterday" rots in be, A detail is either researched or absent. This generator researches nothing., The highlight-reel guardrail: 140K stars belong to the project, never to him., Same inputs, same message — so what was reviewed is what gets sent. (+10 more)

### Community 16 - "Community 16"
Cohesion: 0.1
Nodes (22): all_values(), BankMissing, dump_field_map(), load_bank(), located_in_answer(), lookup(), match_field(), _norm_place() (+14 more)

### Community 17 - "Community 17"
Cohesion: 0.2
Nodes (24): cmd_add(), cmd_due(), cmd_expire(), cmd_list(), cmd_mark_accepted(), cmd_mark_failed(), cmd_mark_sent(), find() (+16 more)

### Community 18 - "Community 18"
Cohesion: 0.12
Nodes (18): _fake_run(), no_packet(), Tests for the Claude Code bridge — specifically the two rules that cost real day, Runbook §2 — rebuilding silently overwrites drafts the owner may have approved., The remaining jobs must NOT appear in `failed` — that is the D25 mistake., find_packet always returns None — i.e. Claude wrote no artifact., Regression, 2026-08-06 first real run.      The Energy Exemplar packet built com, A late limit stops the batch without throwing away the job that completed. (+10 more)

### Community 19 - "Community 19"
Cohesion: 0.1
Nodes (13): The freetext fallback must answer motivation prose and NOTHING else.  This is, The whitelist must short-circuit BEFORE any network call., The dangerous direction is SHORT, not long.      Measured 2026-08-15: at max_t, A too-small budget is indistinguishable from a bad model. Pin the default., A checkable fact must never reach the model., Any failure means BLANK. Blank beats wrong - the rule does not bend for convenie, Ignoring the length brief suggests the grounding rule was ignored too, and a tru, test_answer_returns_none_when_the_model_is_down() (+5 more)

### Community 20 - "Community 20"
Cohesion: 0.14
Nodes (18): _isolate(), Follow-up cadence, fed from records that are true rather than from zeros.  `tool, `check_approvals.py` greps for `ref:<slug>` and `flush-approved` SENDS what it f, Never let a test read or append to the real send record., The whole point: the count is READ, not assumed to be zero., Skills Capital" in the ledger and "SkillsCapital" in the send log are one compan, _row(), test_a_company_with_nobody_to_reach_is_not_chased() (+10 more)

### Community 21 - "Community 21"
Cohesion: 0.13
Nodes (18): _packet(), Tests for role-scoped packets (D34).  The deadlock being fixed: the runbook writ, Nothing must move. Eight packets already exist at output/outreach/<company>/., Same role asked twice must resolve to the same place, or builds duplicate foreve, The board row id and the packet's job_id need not agree; company+role is the rea, THE safety property. A CV tailored to one req must never be served for another., The second role must reuse the first's contact.md, so the sibling has to be find, Otherwise one role gets split across two folders and the first is orphaned. (+10 more)

### Community 22 - "Community 22"
Cohesion: 0.16
Nodes (18): already_applied(), company_role_key(), describe(), Entry, linkedin_job_id(), load(), _norm(), The never-resubmit ledger — the guard that must exist before submitting can.  "O (+10 more)

### Community 23 - "Community 23"
Cohesion: 0.2
Nodes (17): board_status(), Due, _engine(), main(), mark_sent(), _norm(), notified(), notify() (+9 more)

### Community 24 - "Community 24"
Cohesion: 0.18
Nodes (12): Action, busy_linkedin_run(), catalogue(), get(), linkedin_servers(), preflight(), Count real MCP servers (python only — each session also spawns 2 uvx wrappers)., What the owner needs to know before firing a LinkedIn action. (+4 more)

### Community 25 - "Community 25"
Cohesion: 0.19
Nodes (16): _contact(), Tests for the "did this application reach a human?" report.  The defect being lo, Crossing Hurdles has a contact.md whose content is 'no contact findable'.      T, A dead end is not an outstanding task. Reporting it forever would train the read, SkillsCapital took four slots. Four identical lines would bury the other gaps., Failing toward 'covered' would hide gaps. Fail toward reporting them., _row(), test_a_company_recorded_unreachable_is_not_reported_as_a_gap() (+8 more)

### Community 26 - "Community 26"
Cohesion: 0.21
Nodes (16): ask(), _ask_anthropic(), _ask_endpoint(), _ask_openai_compatible(), _Endpoint, _endpoints(), LLMError, The single LLM entry point for the whole app.  One function: ask(prompt, max_tok (+8 more)

### Community 27 - "Community 27"
Cohesion: 0.12
Nodes (9): Tests for pre-application sourcing screens.  The asymmetry under test is the who, THE test. Crossing Hurdles took two application slots and could never be followe, A real employer CAN post an hourly rate. Deprioritized is fine; dropped is not., A bare assertion must not be able to block a company., Fail toward applying. An unreadable list must not silently block every company., test_a_company_with_recorded_evidence_is_blocked(), test_a_corrupt_evidence_file_is_reported_and_blocks_nobody(), test_a_legitimate_contract_role_is_not_lost() (+1 more)

### Community 28 - "Community 28"
Cohesion: 0.23
Nodes (14): all_of(), build_card(), first(), first_blockquote(), load_env(), main(), post(), Role, score, recipient, the exact message the robot will send, marker. Nothing e (+6 more)

### Community 29 - "Community 29"
Cohesion: 0.21
Nodes (13): build_image_prompt(), dispatch_to_linkedin(), generate_hero_image(), _get_fallback_image(), load_templates(), main(), Post to LinkedIn via Playwright with persistent browser session., Send a Slack notification about the post status. (+5 more)

### Community 30 - "Community 30"
Cohesion: 0.21
Nodes (13): deduplicate_against_hub(), main(), Extract decisions from docs/knowledge/05-decisions.md and other files., Scan Claude Code JSONL transcripts for user problems and AI solutions., Scan Antigravity JSONL transcripts for user problems and solutions., Scan Brain 1 Obsidian vault for patterns and insights., Remove ideas that are already in the Content Hub (by fuzzy title match)., Extract post-worthy entries from graphify-out/log.md session log. (+5 more)

### Community 31 - "Community 31"
Cohesion: 0.24
Nodes (12): backfill(), _company_from_slug(), document(), first_name(), main(), message(), Write the message that gets sent when someone accepts.  WHY THIS EXISTS --------, The exact 2b text. Deterministic: same inputs, same message, and it is testable. (+4 more)

### Community 32 - "Community 32"
Cohesion: 0.15
Nodes (7): Tests for role-family routing.  The risk being tested: a job silently getting th, MLOps postings ask for model lifecycle work, not cluster work — even though the, Both families fit; DevOps leads with the better-evidenced half of the portfolio., No CV must never mean 'apply with whatever LinkedIn pre-filled'., test_ai_devops_hybrids_go_to_devops(), test_missing_family_cv_is_reported_not_silently_skipped(), test_mlops_goes_to_ai_not_devops()

### Community 33 - "Community 33"
Cohesion: 0.15
Nodes (7): Respect the field's character cap, or leave it blank. Never send a fragment.  Ca, Below roughly a third of the limit there is no answer left, only a stub - and a, The real case: the years fields cap at 20 and the prose answers are 200+., Every narrative answer must arrive as FINISHED prose in the common 300-char fiel, test_a_20_char_field_rejects_a_paragraph(), test_banked_prose_fits_a_300_char_field_whole(), test_refuses_rather_than_send_a_stub()

### Community 34 - "Community 34"
Cohesion: 0.3
Nodes (11): companies_with_a_named_human(), _company_matches(), Gap, gaps(), main(), _norm(), notify(), Which applications have reached a human, and which are sitting in a queue alone. (+3 more)

### Community 35 - "Community 35"
Cohesion: 0.26
Nodes (11): _api_key(), ask_once(), list_models(), main(), Find which OmniRoute models can be trusted to return an answer intact.  WHY THIS, True only if every probe round-trips exactly. Ambiguity counts as failure., Probe both transport modes. A model is usable if EITHER passes cleanly., A key, from the environment or .env. Never hardcoded (repo is public). (+3 more)

### Community 36 - "Community 36"
Cohesion: 0.27
Nodes (10): collect(), main(), plan(), Turn scraped LinkedIn job JSON into scored board rows.  ⚠️ THIS EXISTED ONLY AS, Merge every scrape file, keeping ONLY Easy Apply rows, deduped by LinkedIn job i, (rows_to_insert, already_known, below_threshold)., (fit, family). fit 0 with family None means "not one of his families at all"., score() (+2 more)

### Community 37 - "Community 37"
Cohesion: 0.25
Nodes (9): load_unreachable(), _norm(), Screen a board row before it consumes an application slot.  WHY THIS EXISTS ----, Decide whether this row deserves an application slot.      Pure enough to test:, Companies PROVEN to have nobody to follow up with. Keyed by normalised company n, Mark a company as having no findable human. Requires evidence, in words, on purp, record_unreachable(), screen() (+1 more)

### Community 38 - "Community 38"
Cohesion: 0.27
Nodes (9): board_rows(), main(), Question, Read Easy Apply forms and write down every question. Submit nothing.  WHY THIS E, Walk one wizard, recording questions. Always discards. Never submits., Record every control on this step. Reuses fill.py's scanner, so what we see here, _scan_step(), survey_job() (+1 more)

### Community 39 - "Community 39"
Cohesion: 0.42
Nodes (10): applyPanel(), buildPanel(), change(), cvPanel(), followBuild(), notionRow(), recount(), renderList() (+2 more)

### Community 40 - "Community 40"
Cohesion: 0.27
Nodes (9): answer(), _budget_line(), build_prompt(), is_llm_answerable(), Answer the genuinely per-company free-text question with the LLM. Nothing else., Return (answer, why). `answer` is None whenever the field must be left blank., Tell the model the character cap the FORM enforces, in characters, not words., True only for motivation prose. Deliberately a whitelist, not a blacklist. (+1 more)

### Community 41 - "Community 41"
Cohesion: 0.33
Nodes (9): _bash_path(), find_interpreter(), hook_status(), install(), main(), C:\\Foo\\python.exe -> /c/Foo/python.exe, which is what Git Bash needs., An interpreter that can actually import graphify. Prefer the one running this sc, (name, ok, detail) per hook. `ok` means it names an interpreter that has graphif (+1 more)

### Community 42 - "Community 42"
Cohesion: 0.44
Nodes (6): actionCard(), confirmPanel(), fire(), loadHistory(), renderRun(), watch()

### Community 43 - "Community 43"
Cohesion: 0.31
Nodes (8): delete_all_experience(), fill_position(), main(), navigate_to_add_position(), LinkedIn Experience Cleanup + Re-add v6 Step 1: Delete the 3 empty experience en, Add section -> Core -> Add position., Fill the experience form using POSITION-BASED field indexing., Delete all existing experience entries by navigating to the experience section.

### Community 44 - "Community 44"
Cohesion: 0.36
Nodes (7): CvChoice, family_for(), family_pdf(), pick_cv(), Role families — one reusable CV per family, instead of one per company.  WHY THI, Which family CV this role should receive., A company-tailored CV if one exists, otherwise the family CV. Never the generic

### Community 45 - "Community 45"
Cohesion: 0.52
Nodes (6): classify(), live_rows(), load(), main(), Classify every live board row: Easy Apply, external ATS, or dead.  WHY --- Rough, save()

### Community 46 - "Community 46"
Cohesion: 0.33
Nodes (6): _parse_errors(), Every pipeline script must at least PARSE.  WHY (2026-08-15) ---------------- `t, Empty string when the file parses. Uses the PowerShell parser itself, not a heur, A glob that quietly matches nothing would make every test below pass for the wro, test_script_parses(), test_there_are_scripts_to_check()

### Community 47 - "Community 47"
Cohesion: 0.52
Nodes (6): keywords_from_jd(), main(), norm(), present(), Keyword is present if it appears as a token/phrase in the CV text., read_text()

### Community 48 - "Community 48"
Cohesion: 0.57
Nodes (5): Enter-PipelineLock(), Get-PipelineLockOwner(), Read-PipelineLockText(), Remove-StalePipelineLock(), Write-LockLine()

### Community 49 - "Community 49"
Cohesion: 0.38
Nodes (6): add_skills(), check_and_cleanup(), main(), LinkedIn Profile Cleanup & Skills Add: 1. Scroll through experience section to c, Check the experience section for empty or duplicate entries., Add skills via Add section -> Core -> Add skills.

### Community 50 - "Community 50"
Cohesion: 0.6
Nodes (5): call(), load_env(), main(), Map user/bot ids to display names so the export is readable., resolve_users()

### Community 51 - "Community 51"
Cohesion: 0.6
Nodes (5): call(), find_ts(), load_env(), main(), Locate the newest card carrying `ref:<slug>`.

### Community 52 - "Community 52"
Cohesion: 0.7
Nodes (4): as_bool(), due_for(), main(), notify()

### Community 53 - "Community 53"
Cohesion: 0.6
Nodes (4): degree_of(), main(), poll(), Read-only accept-watch poll: degree + invite badge for each pending invite.  [[1

### Community 54 - "Community 54"
Cohesion: 0.7
Nodes (4): cap(), fmt(), load_env(), main()

### Community 55 - "Community 55"
Cohesion: 0.67
Nodes (3): board_rows(), main(), Applied rows with a real applied date, shaped for followups.py.

### Community 56 - "Community 56"
Cohesion: 0.67
Nodes (3): generate_upgraded_post1_carousel(), Upgraded Post 1 Carousel Generator — Job Hunt Autopilot Features ZERO AI gibberi, render_edge_screenshot()

### Community 57 - "Community 57"
Cohesion: 0.5
Nodes (3): HTML/CSS 3D Isometric Neon Architecture Infographic Generator, Renders HTML string into high-res PNG image via headless Edge., render_html_to_png()

### Community 58 - "Community 58"
Cohesion: 0.5
Nodes (3): auto_post_to_linkedin(), Automated Playwright LinkedIn Post Dispatcher Uses Playwright browser automation, Automates posting to LinkedIn using Playwright Chromium with persistent user pro

### Community 59 - "Community 59"
Cohesion: 0.67
Nodes (3): Distinct Slide 1 Hero Cover Generator Renders 2 distinct, highly detailed Slide, render_distinct_covers(), render_edge_screenshot()

### Community 60 - "Community 60"
Cohesion: 0.67
Nodes (3): Hybrid Vector Composite Slide 1 Cover Studio Combines pristine 3D Command Center, render_edge_screenshot(), render_hybrid_slide1_covers()

### Community 61 - "Community 61"
Cohesion: 0.67
Nodes (2): Release-BrowserProfile(), Say()

### Community 62 - "Community 62"
Cohesion: 0.83
Nodes (3): api(), load_env(), main()

### Community 63 - "Community 63"
Cohesion: 0.67
Nodes (0): 

### Community 64 - "Community 64"
Cohesion: 1.0
Nodes (2): load_env(), main()

### Community 65 - "Community 65"
Cohesion: 0.67
Nodes (1): Post 2 Packager — AI Visual Content Studio Packages the ALREADY-BUILT 4-slide ca

### Community 66 - "Community 66"
Cohesion: 0.67
Nodes (1): LinkedIn Profile Editor — Add About Section. The profile page shows "Write a sum

### Community 67 - "Community 67"
Cohesion: 0.67
Nodes (1): Quick check: scroll the profile to see the experience section.

### Community 68 - "Community 68"
Cohesion: 0.67
Nodes (1): LinkedIn Profile Editor v6 — TARGETED. The headline is a TipTap ProseMirror cont

### Community 69 - "Community 69"
Cohesion: 0.67
Nodes (1): Render High-Density, Ultra-Detailed Technical Architecture Visual (Slide 2 Upgra

### Community 70 - "Community 70"
Cohesion: 0.67
Nodes (1): Test LinkedIn Post Dispatch & Verification Script Packages the exact 4-slide vis

### Community 71 - "Community 71"
Cohesion: 1.0
Nodes (2): load_env(), main()

### Community 72 - "Community 72"
Cohesion: 1.0
Nodes (1): The board store: schema, access layer, and the SQLite file itself.

### Community 73 - "Community 73"
Cohesion: 1.0
Nodes (0): 

### Community 74 - "Community 74"
Cohesion: 1.0
Nodes (0): 

### Community 75 - "Community 75"
Cohesion: 1.0
Nodes (0): 

### Community 76 - "Community 76"
Cohesion: 1.0
Nodes (0): 

### Community 77 - "Community 77"
Cohesion: 1.0
Nodes (1): Moved. The server now lives at `backend/server.py`.  Kept as a redirect because

### Community 78 - "Community 78"
Cohesion: 1.0
Nodes (0): 

### Community 79 - "Community 79"
Cohesion: 1.0
Nodes (1): Evidence of no findable human -- the only state allowed to block a company (D36)

### Community 80 - "Community 80"
Cohesion: 1.0
Nodes (0): 

### Community 81 - "Community 81"
Cohesion: 1.0
Nodes (0): 

### Community 82 - "Community 82"
Cohesion: 1.0
Nodes (0): 

### Community 83 - "Community 83"
Cohesion: 1.0
Nodes (0): 

### Community 84 - "Community 84"
Cohesion: 1.0
Nodes (0): 

### Community 85 - "Community 85"
Cohesion: 1.0
Nodes (0): 

### Community 86 - "Community 86"
Cohesion: 1.0
Nodes (1): Bundles post copy and high-res image into a complete publishing package.

### Community 87 - "Community 87"
Cohesion: 1.0
Nodes (1): Simulates or executes publishing of the ready package to LinkedIn.         If Li

### Community 88 - "Community 88"
Cohesion: 1.0
Nodes (1): Dynamically generates post copy and custom image prompt tailored to the given to

### Community 89 - "Community 89"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **297 isolated node(s):** `The board store: schema, access layer, and the SQLite file itself.`, `The answer bank and the FIELD_MAP — the only legal source of form values.  THE`, `Read a dotted path out of the bank. Returns None for missing OR null — both mean`, `One mappable question.      patterns  regexes matched (case-insensitive) again`, `Answer 'Are you currently located in <city>?' by COMPARING, never by assuming.` (+292 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 72`** (2 nodes): `__init__.py`, `The board store: schema, access layer, and the SQLite file itself.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 73`** (2 nodes): `claude-free.ps1`, `Fail()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 74`** (2 nodes): `create_privatecloud_pdf_carousel.py`, `process_and_create_pdf()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 75`** (2 nodes): `generate_privatecloud_carousel.py`, `generate_slides()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 76`** (2 nodes): `post_privatecloud_to_linkedin.py`, `publish_privatecloud_bundle()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 77`** (2 nodes): `serve_dashboard.py`, `Moved. The server now lives at `backend/server.py`.  Kept as a redirect because`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 78`** (2 nodes): `sweep-packets.ps1`, `Say()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 79`** (1 nodes): `Evidence of no findable human -- the only state allowed to block a company (D36)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 80`** (1 nodes): `auto-apply.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 81`** (1 nodes): `build-packet.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 82`** (1 nodes): `check-replies.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 83`** (1 nodes): `daily-discovery.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 84`** (1 nodes): `flush-approved.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 85`** (1 nodes): `daily_post_scheduler.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 86`** (1 nodes): `Bundles post copy and high-res image into a complete publishing package.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 87`** (1 nodes): `Simulates or executes publishing of the ready package to LinkedIn.         If Li`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 88`** (1 nodes): `Dynamically generates post copy and custom image prompt tailored to the given to`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 89`** (1 nodes): `watch-accepts.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LinkedInLoggedOut` connect `Community 0` to `Community 1`, `Community 8`, `Community 10`, `Community 12`, `Community 45`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Why does `Candidate` connect `Community 0` to `Community 7`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **Why does `BankMissing` connect `Community 16` to `Community 8`?**
  _High betweenness centrality (0.010) - this node is a cross-community bridge._
- **Are the 45 inferred relationships involving `LinkedInLoggedOut` (e.g. with `check_logged_in()` and `Check`) actually correct?**
  _`LinkedInLoggedOut` has 45 INFERRED edges - model-reasoned connections that need verification._
- **Are the 14 inferred relationships involving `fill_job()` (e.g. with `FillResult` and `slug_for()`) actually correct?**
  _`fill_job()` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 14 inferred relationships involving `render()` (e.g. with `tick()` and `freshness()`) actually correct?**
  _`render()` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 11 inferred relationships involving `FillResult` (e.g. with `fill_job()` and `Candidate`) actually correct?**
  _`FillResult` has 11 INFERRED edges - model-reasoned connections that need verification._