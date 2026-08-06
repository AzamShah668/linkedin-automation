# Graph Report - .  (2026-08-06)

## Corpus Check
- 60 files · ~0 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 443 nodes · 678 edges · 50 communities detected
- Extraction: 59% EXTRACTED · 41% INFERRED · 0% AMBIGUOUS · INFERRED: 277 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## God Nodes (most connected - your core abstractions)
1. `fill_job()` - 12 edges
2. `Handler` - 12 edges
3. `LinkedInLoggedOut` - 10 edges
4. `_scan()` - 9 edges
5. `build_card()` - 9 edges
6. `FillResult` - 8 edges
7. `read_state()` - 8 edges
8. `el()` - 8 edges
9. `build_packet()` - 7 edges
10. `_fill_step()` - 7 edges

## Surprising Connections (you probably didn't know these)
- `Candidate` --uses--> `LinkedInLoggedOut`  [INFERRED]
  apps\autopilot\run.py → apps\autopilot\fill.py
- `CLI entry point for the autopilot.      py -3 -m apps.autopilot.run fieldmap` --uses--> `LinkedInLoggedOut`  [INFERRED]
  apps\autopilot\run.py → apps\autopilot\fill.py
- `Best-fit-first board rows, already-done excluded.` --uses--> `LinkedInLoggedOut`  [INFERRED]
  apps\autopilot\run.py → apps\autopilot\fill.py
- `Probe candidates until `wanted` postings actually show an Easy Apply button.` --uses--> `LinkedInLoggedOut`  [INFERRED]
  apps\autopilot\run.py → apps\autopilot\fill.py
- `Open the profile and wait for the OWNER to sign in by hand.      This is not an` --uses--> `LinkedInLoggedOut`  [INFERRED]
  apps\autopilot\run.py → apps\autopilot\fill.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (27): execute_iterative_architecture_hero(), Iterative Architecture Diagram & 3D Enrichment Studio Step 1: Renders a clean co, render_edge_screenshot(), execute_2step_pipeline(), 2-Step AI 3D Command Center Slide 1 Hero Studio Step 1: Render clean, readable 5, render_edge_screenshot(), Ultimate Cybernetic HUD Architecture Generator (FLUX.1 & Gemini Engine) Combines, generate_upgraded_4slide_carousel() (+19 more)

### Community 1 - "Community 1"
Cohesion: 0.1
Nodes (37): _apply(), _attach_resume(), _attr_q(), _capture_resume(), check_logged_in(), _close_modal(), Control, _current_value() (+29 more)

### Community 2 - "Community 2"
Cohesion: 0.08
Nodes (23): all_rows(), last_sync(), _parse_ts(), pending_notion(), Insert or update by Notion page id. Returns (inserted, updated, protected)., Change a job's status from the dashboard. Returns the updated row.      Record, Dashboard edits Notion has not been told about — one row per job, latest state., Notes say warm/alumni but the checkbox is unticked — a real data gap that     s (+15 more)

### Community 3 - "Community 3"
Cohesion: 0.18
Nodes (16): BaseHTTPRequestHandler, all_zip(), bootstrap(), build_packets(), cv_paths(), discover_packets(), Handler, main() (+8 more)

### Community 4 - "Community 4"
Cohesion: 0.14
Nodes (20): ago(), api(), boot(), clear(), copy(), el(), esc(), fitCell() (+12 more)

### Community 5 - "Community 5"
Cohesion: 0.2
Nodes (24): cmd_add(), cmd_due(), cmd_expire(), cmd_list(), cmd_mark_accepted(), cmd_mark_failed(), cmd_mark_sent(), find() (+16 more)

### Community 6 - "Community 6"
Cohesion: 0.12
Nodes (18): _fake_run(), no_packet(), Tests for the Claude Code bridge — specifically the two rules that cost real day, Runbook §2 — rebuilding silently overwrites drafts the owner may have approved., The remaining jobs must NOT appear in `failed` — that is the D25 mistake., find_packet always returns None — i.e. Claude wrote no artifact., Regression, 2026-08-06 first real run.      The Energy Exemplar packet built com, A late limit stops the batch without throwing away the job that completed. (+10 more)

### Community 7 - "Community 7"
Cohesion: 0.23
Nodes (18): FillResult, LinkedInLoggedOut, The persistent profile is not signed in. Abort the WHOLE run; never attempt a lo, board_candidates(), Candidate, cmd_fieldmap(), cmd_fill(), cmd_login() (+10 more)

### Community 8 - "Community 8"
Cohesion: 0.17
Nodes (15): build_many(), build_packet(), find_packet(), Packet, PacketBuildFailed, The bridge to Claude Code — the one step that keeps a full agent session.  Every, Run Claude Code against the packet runbook for one job. Sends nothing.      Rais, Build several packets. Returns (built, [(job_id, error)], usage_limit_message). (+7 more)

### Community 9 - "Community 9"
Cohesion: 0.18
Nodes (12): Action, busy_linkedin_run(), catalogue(), get(), linkedin_servers(), preflight(), Count real MCP servers (python only — each session also spawns 2 uvx wrappers)., What the owner needs to know before firing a LinkedIn action. (+4 more)

### Community 10 - "Community 10"
Cohesion: 0.16
Nodes (13): BankMissing, dump_field_map(), load_bank(), lookup(), match_field(), The answer bank and the FIELD_MAP — the only legal source of form values.  THE, First FIELD_MAP entry whose pattern appears in the label wins. Order = priority., Turn a Spec into the literal string to type, or None meaning LEAVE BLANK. (+5 more)

### Community 11 - "Community 11"
Cohesion: 0.23
Nodes (14): all_of(), build_card(), first(), first_blockquote(), load_env(), main(), post(), Role, score, recipient, the exact message the robot will send, marker. Nothing e (+6 more)

### Community 12 - "Community 12"
Cohesion: 0.42
Nodes (10): applyPanel(), buildPanel(), change(), cvPanel(), followBuild(), notionRow(), recount(), renderList() (+2 more)

### Community 13 - "Community 13"
Cohesion: 0.33
Nodes (9): _bash_path(), find_interpreter(), hook_status(), install(), main(), C:\\Foo\\python.exe -> /c/Foo/python.exe, which is what Git Bash needs., An interpreter that can actually import graphify. Prefer the one running this sc, (name, ok, detail) per hook. `ok` means it names an interpreter that has graphif (+1 more)

### Community 14 - "Community 14"
Cohesion: 0.42
Nodes (8): ask(), _ask_anthropic(), _ask_openai_compatible(), LLMError, The single LLM entry point for the whole app.  One function: ask(prompt, max_tok, Any failure to get usable text out of a provider. Always carries the raw respons, Send one prompt, get one string back. Raises LLMError rather than returning junk, _require_env()

### Community 15 - "Community 15"
Cohesion: 0.44
Nodes (6): actionCard(), confirmPanel(), fire(), loadHistory(), renderRun(), watch()

### Community 16 - "Community 16"
Cohesion: 0.29
Nodes (2): inviteUnit(), leg()

### Community 17 - "Community 17"
Cohesion: 0.52
Nodes (6): keywords_from_jd(), main(), norm(), present(), Keyword is present if it appears as a token/phrase in the CV text., read_text()

### Community 18 - "Community 18"
Cohesion: 0.57
Nodes (5): Enter-PipelineLock(), Get-PipelineLockOwner(), Read-PipelineLockText(), Remove-StalePipelineLock(), Write-LockLine()

### Community 19 - "Community 19"
Cohesion: 0.6
Nodes (5): call(), load_env(), main(), Map user/bot ids to display names so the export is readable., resolve_users()

### Community 20 - "Community 20"
Cohesion: 0.6
Nodes (5): call(), find_ts(), load_env(), main(), Locate the newest card carrying `ref:<slug>`.

### Community 21 - "Community 21"
Cohesion: 0.7
Nodes (4): as_bool(), due_for(), main(), notify()

### Community 22 - "Community 22"
Cohesion: 0.7
Nodes (4): cap(), fmt(), load_env(), main()

### Community 23 - "Community 23"
Cohesion: 0.67
Nodes (3): generate_upgraded_post1_carousel(), Upgraded Post 1 Carousel Generator — Job Hunt Autopilot Features ZERO AI gibberi, render_edge_screenshot()

### Community 24 - "Community 24"
Cohesion: 0.5
Nodes (3): HTML/CSS 3D Isometric Neon Architecture Infographic Generator, Renders HTML string into high-res PNG image via headless Edge., render_html_to_png()

### Community 25 - "Community 25"
Cohesion: 0.5
Nodes (3): auto_post_to_linkedin(), Automated Playwright LinkedIn Post Dispatcher Uses Playwright browser automation, Automates posting to LinkedIn using Playwright Chromium with persistent user pro

### Community 26 - "Community 26"
Cohesion: 0.67
Nodes (3): Distinct Slide 1 Hero Cover Generator Renders 2 distinct, highly detailed Slide, render_distinct_covers(), render_edge_screenshot()

### Community 27 - "Community 27"
Cohesion: 0.67
Nodes (3): Hybrid Vector Composite Slide 1 Cover Studio Combines pristine 3D Command Center, render_edge_screenshot(), render_hybrid_slide1_covers()

### Community 28 - "Community 28"
Cohesion: 0.83
Nodes (3): api(), load_env(), main()

### Community 29 - "Community 29"
Cohesion: 1.0
Nodes (2): load_env(), main()

### Community 30 - "Community 30"
Cohesion: 0.67
Nodes (1): Post 2 Packager — AI Visual Content Studio Packages the ALREADY-BUILT 4-slide ca

### Community 31 - "Community 31"
Cohesion: 0.67
Nodes (1): Render High-Density, Ultra-Detailed Technical Architecture Visual (Slide 2 Upgra

### Community 32 - "Community 32"
Cohesion: 0.67
Nodes (1): Test LinkedIn Post Dispatch & Verification Script Packages the exact 4-slide vis

### Community 33 - "Community 33"
Cohesion: 1.0
Nodes (2): load_env(), main()

### Community 34 - "Community 34"
Cohesion: 0.67
Nodes (0): 

### Community 35 - "Community 35"
Cohesion: 1.0
Nodes (1): Job Hunt Autopilot — the Python runtime that replaces the Claude-Code-as-server

### Community 36 - "Community 36"
Cohesion: 1.0
Nodes (0): 

### Community 37 - "Community 37"
Cohesion: 1.0
Nodes (0): 

### Community 38 - "Community 38"
Cohesion: 1.0
Nodes (0): 

### Community 39 - "Community 39"
Cohesion: 1.0
Nodes (0): 

### Community 40 - "Community 40"
Cohesion: 1.0
Nodes (0): 

### Community 41 - "Community 41"
Cohesion: 1.0
Nodes (0): 

### Community 42 - "Community 42"
Cohesion: 1.0
Nodes (0): 

### Community 43 - "Community 43"
Cohesion: 1.0
Nodes (0): 

### Community 44 - "Community 44"
Cohesion: 1.0
Nodes (0): 

### Community 45 - "Community 45"
Cohesion: 1.0
Nodes (0): 

### Community 46 - "Community 46"
Cohesion: 1.0
Nodes (1): Bundles post copy and high-res image into a complete publishing package.

### Community 47 - "Community 47"
Cohesion: 1.0
Nodes (1): Simulates or executes publishing of the ready package to LinkedIn.         If Li

### Community 48 - "Community 48"
Cohesion: 1.0
Nodes (1): Dynamically generates post copy and custom image prompt tailored to the given to

### Community 49 - "Community 49"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **91 isolated node(s):** `Job Hunt Autopilot — the Python runtime that replaces the Claude-Code-as-server`, `The answer bank and the FIELD_MAP — the only legal source of form values.  THE`, `Read a dotted path out of the bank. Returns None for missing OR null — both mean`, `One mappable question.      patterns  regexes matched (case-insensitive) again`, `First FIELD_MAP entry whose pattern appears in the label wins. Order = priority.` (+86 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 35`** (2 nodes): `__init__.py`, `Job Hunt Autopilot — the Python runtime that replaces the Claude-Code-as-server`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 36`** (2 nodes): `run-pipeline.ps1`, `Say()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 37`** (2 nodes): `sweep-packets.ps1`, `Say()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 38`** (2 nodes): `page-research.js`, `render()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 39`** (2 nodes): `page-slack.js`, `render()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 40`** (1 nodes): `auto-apply.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 41`** (1 nodes): `build-packet.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 42`** (1 nodes): `check-replies.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 43`** (1 nodes): `daily-discovery.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 44`** (1 nodes): `flush-approved.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 45`** (1 nodes): `daily_post_scheduler.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 46`** (1 nodes): `Bundles post copy and high-res image into a complete publishing package.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 47`** (1 nodes): `Simulates or executes publishing of the ready package to LinkedIn.         If Li`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 48`** (1 nodes): `Dynamically generates post copy and custom image prompt tailored to the given to`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 49`** (1 nodes): `watch-accepts.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LinkedInLoggedOut` connect `Community 7` to `Community 8`, `Community 1`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Why does `BankMissing` connect `Community 10` to `Community 8`?**
  _High betweenness centrality (0.013) - this node is a cross-community bridge._
- **Why does `LLMError` connect `Community 14` to `Community 8`?**
  _High betweenness centrality (0.008) - this node is a cross-community bridge._
- **Are the 10 inferred relationships involving `fill_job()` (e.g. with `FillResult` and `slug_for()`) actually correct?**
  _`fill_job()` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `LinkedInLoggedOut` (e.g. with `check_logged_in()` and `Candidate`) actually correct?**
  _`LinkedInLoggedOut` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `_scan()` (e.g. with `Control` and `_group_label()`) actually correct?**
  _`_scan()` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `build_card()` (e.g. with `read()` and `first()`) actually correct?**
  _`build_card()` has 7 INFERRED edges - model-reasoned connections that need verification._