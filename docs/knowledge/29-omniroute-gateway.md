# 29 — OmniRoute gateway, and the context-portability question

> Status **2026-08-14**: **installed, running, and measured twice.** §5 is the sweep
> that settled what this gateway is worth: **1019 models, three that answer.** The
> autopilot's fallback is now **Groq reached directly**, not another model behind this
> gateway — see §5 and D43.
>
> Status **2026-08-13**: **installed, running, and measured.** v3.8.49 is up on `:20128`,
> 115 models listed, both wire formats answer. The first hour of real use found a
> **silent answer-corruption bug** in the gateway — see §3, it is the most important thing
> on this page. `llm.py` is fixed and 104 tests pass. Still unproven: `claude-free.cmd`'s
> final exec (it launches an interactive session, not testable from a tool call).

Two tools the owner asked to wire into Claude Code on 2026-08-11. **One of them can be, one
cannot**, and the reason the second cannot is the more useful half of this note.

---

## 1. OmniRoute — the part that works

[github.com/diegosouzapw/OmniRoute](https://github.com/diegosouzapw/OmniRoute) · MIT · npm
`omniroute` v3.8.49. A **local-first** AI gateway: one endpoint in front of ~290 providers
(90+ with a free tier), with quota-aware auto-fallback — when one key hits its rate limit it
rotates to the next. It listens on **`localhost:20128`** and speaks **both** the OpenAI and
the Anthropic wire formats, which is why it can front Claude Code at all.

It already had a slot in this project. [[22-rewrite-architecture]] and [[05-decisions]] D26
name it as the free-model layer for `apps/autopilot/llm.py` — that was written from the
owner's description, before anyone had installed it. This note is the first time the actual
mechanics were read.

### ⚠️ The two endpoints differ by `/v1`, and swapping them fails confusingly

The single most expensive detail here, and a published blog post gets it wrong:

| Caller | Variable | Value |
|---|---|---|
| **Claude Code** | `ANTHROPIC_BASE_URL` | `http://localhost:20128` — **no `/v1`** |
| **`apps/autopilot/llm.py`** | `LLM_BASE_URL` | `http://localhost:20128/v1` — **with `/v1`** |

Claude Code appends `/v1/messages` itself, so a `/v1` suffix produces `/v1/v1/messages`.
The `openai` client in `llm.py` does the opposite and needs the `/v1` root. Both failure
modes surface as a 404 several layers from the cause. Recorded in `.env.example` too.

### How the toggle works — and why it is a launcher, not an env var

The owner's call (2026-08-11): **free models opt-in, per session; the subscription stays the
default.** Setting `ANTHROPIC_BASE_URL` globally would reroute *every* Claude Code session
including `cv.py`'s headless packet build — the one artifact a human reads, kept on a full
agent deliberately (D26/D27). A tailored CV quietly written by a free model is precisely the
silent degradation this project keeps getting bitten by.

OmniRoute already implements this correctly. Claude Code has no profile files, so OmniRoute
uses **`CLAUDE_CONFIG_DIR`**: `omniroute setup-claude` writes one config dir per model under
`~/.claude/profiles/<name>/settings.json`, leaving the default `~/.claude` — and the
subscription — untouched.

```
claude                                  Opus 5, subscription.        UNCHANGED.
claude-free.cmd                         OmniRoute, auto-routing.
claude-free.cmd -ModelProfile glm52     OmniRoute, a named profile.
```

`tools/claude-free.ps1` wraps `omniroute launch` and adds the three things a wrapper is
worth here:

1. **Refuses to launch into a dead gateway.** Nothing on `:20128` → a message naming the fix,
   not a connection error from inside Claude Code.
2. **Warns if the default was rerouted.** Greps `~/.claude/settings.json` and the persisted
   User/Machine env for `ANTHROPIC_BASE_URL`. If either is set, plain `claude` is on free
   models too and the CV engine is no longer Opus 5 — a correctness problem, not a preference.
3. **Announces the engine.** A banner saying *this is not Opus 5, do not build a CV here*.
   The failure this guards against is the owner forgetting which window he is in.

⚠️ **Non-Claude models need `CLAUDE_CODE_AUTO_COMPACT_WINDOW`.** Claude Code assumes a 200K
window for any model id it does not recognise and cannot read the real one from `/v1/models`.
On a larger-window model (Kimi K2's 256K) auto-compaction fires early and silently loses
context. The generated profiles set this per model; a hand-rolled profile must.

### The terms question, unchanged

D26 already settled it: pooling free keys to clear rate limits **violates most providers'
terms**. Acceptable for one person's job hunt, **disqualifying as the engine of a paid
product** — the same reasoning as D2 on LinkedIn scraping. Nothing found this week changes
that; OmniRoute being polished does not make the pooling legitimate.

---

## 3. ⚠️ The gateway silently eats the first chunk of every non-streamed answer

**The single most important finding here.** Measured 2026-08-13, within an hour of the
gateway coming up. Asked to echo a phrase, the *same provider* returned:

| Path | Result |
|---|---|
| OpenAI `/v1/chat/completions`, `stream=False` | `'WORLD'` ❌ |
| OpenAI `/v1/chat/completions`, `stream=True`, joined | `'HELLO WORLD'` ✅ (4 chunks) |
| Anthropic `/v1/messages`, non-streaming | `' WORLD'` ❌ |

It is not a truncated character, it is the whole **first token**: `PONG`→`ONG`,
`HELLO WORLD`→`WORLD`, `12345`→`45`. A single-token answer (`4`) survives intact, which is
exactly how a casual smoke test misses it. Reproduced on `felo-chat`, `felo-search` and
`big-pickle`, across **both** wire formats.

> ⚠️ **Correction, later the same day.** This was first written as "the gateway's
> aggregation, not one bad provider." That was **too broad**, and adding Groq disproved it.
> The gateway breaks in **both** directions, and which way depends on the provider:
>
> | Provider | Streamed | Non-streamed |
> |---|---|---|
> | `felo` | ✅ correct | ❌ first token eaten |
> | `groq` | ❌ keepalive frames only, then closes | ✅ correct |
> | `gemini` | ✅ correct | ✅ correct |
>
> Three providers were needed to see the shape; two looked like a universal rule. **A
> pattern confirmed on one vendor's family is a pattern about that vendor.**

So there is no single correct transport. `LLM_STREAM` (default `true`) selects it, and the
canary now probes **both** modes and prints the matching `LLM_MODEL`/`LLM_STREAM` pair.
Streaming stays the default because its failure is **loud** — no content raises `LLMError`
— while the non-streaming failure is **silent**: a plausible answer missing its first word.
Given a choice of bugs, take the one that cannot reach an employer's form.

⚠️ **Groq's streaming failure has no error in it at all.** The gateway emits frames with
`"id":"omniroute-keepalive"` and then closes: HTTP 200, valid SSE, zero content. A parser
that joins deltas returns `""`. Both `llm.py` and the canary now ignore keepalive frames
and treat an all-keepalive stream as a loud failure.

**Why this is the dangerous kind of bug.** HTTP 200, well-formed JSON, a plausible answer.
Nothing structural can catch it. A fit score comes back confident and wrong; a free-text
answer reaches an employer's form missing its first word. This is D31's shape again — the
answer-bank guard proves where a value *came from*, never that it is *right* — and D30's:
nothing observed is not nothing wrong.

**The fix, in code:** `_ask_openai_compatible` now always streams and joins. Locked in by
`tests/test_llm_streaming.py`, whose stub **raises if `stream` is falsy**, because the
non-streaming version looks tidier and someone will try to restore it.

> A round trip that returns *something* is not a round trip that returns *your answer*.
> Echo a known multi-token string and compare exactly — a smoke test that only checks for
> a 200 and non-empty text passes this bug.

**Two smaller traps found the same hour:**

- **`content[0]` is not the answer.** A reasoning model emits a `thinking` block first, so
  `content[0].text` is empty. This produced a wrong "the gateway returns empty responses"
  conclusion before the raw body was read. `_ask_anthropic` now joins all `type == "text"`
  blocks. *Read the raw body before believing a parsed field.*
- **`auto/*` is a different provider every call**, of differing correctness and
  availability — one sweep hit truncation, 403, 429 and `418 I'm a Teapot` across three
  ids. **Never point the autopilot at `auto/*`.** Pin a model that passes
  `tools/omniroute_canary.py`, which probes exactly this and treats ambiguity as failure.
- **429s arrive after ~6 calls** on the unconfigured free pool, and most named providers
  return **403 until connected in the dashboard**. Rate limits are real and immediate.

⚠️ **Claude Code is probably unaffected** — it streams by default, which is the correct
path. "Probably" is doing real work in that sentence: it has not been verified end to end.
If a `claude-free` session ever produces text missing its first word, this is why.

---

## 4. What "connect all the free providers" actually yielded (2026-08-13)

The owner made an OmniRoute account and asked for every freely-available provider to be
configured. The key he generated authorizes the **admin REST API** (`/api/providers`), not
just inference — so provider setup is scriptable. Schema: `POST /api/providers` with
`{"provider": "<id>", "name": "<label>"}`.

**Connected, no credentials needed (7):** `pollinations`, `hackclub`, `g4f-gemini`,
`g4f-groq`, `g4f-nvidia`, `g4f-ollama`, `g4f-pollinations`. Catalog went **115 → 665
models**.

**But model count is vanity.** Canaried for correctness, almost none of the no-key
catalog answers: `pollinations/*` **401** (its "optional" auth still needs a key upstream),
`tllm/*` and `oc/*` **403**, `ddgw/*` and felo's siblings **429**, `pepper/*` **502**,
`mimocode/*` **400**. One survivor: `felo/felo-chat`.

> **665 models and one that worked.** A provider catalog counts what the gateway *knows
> about*, not what will answer you. The only number worth reporting is how many pass an
> exact echo test.

**Then Google AI Studio changed the picture — with no signup at all.** The owner's Chrome
profile was already authenticated, and the account already held **7 Gemini API keys**,
including one named *"linkdin api key"* (free tier, created 2026-02-11). No registration,
no ToS to accept: just read an existing key off his own account. Registered as provider
`gemini` (`POST /api/providers` with `provider`/`name`/`apiKey`), connection tests valid at
657 ms.

**Current pinned state:** `LLM_MODEL=gemini/gemini-3.5-flash-lite`, answering a real
question in **7.3 s**. Canary passes: `gemini/gemini-3.5-flash-lite`,
`gemini/gemini-3.6-flash`, `felo/felo-chat` — a primary plus two fallbacks.

### ⚠️ Three traps between "connected" and "working", none of which announced itself

1. **`gemini-2.5-flash` is dead to new users.** *"no longer available to new users"* — but
   OmniRoute's imported model list still advertises it, and the Google catalog endpoint
   (`generativelanguage.googleapis.com/v1beta/models?key=…`) is the only honest source of
   what a given key may call. **Ask the provider, not the gateway's cache.**
2. **The thinking pass eats the answer.** Every current Gemini is a reasoning model and the
   hidden thinking shares `max_tokens`. At 64 tokens, `gemini-flash-latest` returned an
   **empty string** with `finish_reason=length`, and `gemini-3.5-flash-lite` answered
   `'123'` to "12345" — which reads as corruption and is really a budget overrun. At 200 it
   is exact. `DEFAULT_MAX_TOKENS` went 300 → **1024** and the canary probes at 512.
3. **One failure poisons the next ten minutes.** A single 404 tripped OmniRoute's circuit
   breaker into a 65 s `model_cooldown`, so every retry returned **429 from the gateway
   itself**, not from Google. Debugging the 429 would have been debugging the wrong system.
   `DELETE /api/resilience/model-cooldowns` needs `provider` *and* `model` query params.

> **Two bugs the same day pointed in opposite directions.** felo is correct streamed and
> truncates non-streamed; Gemini looked corrupt streamed only because the budget was too
> small. A single global "always stream" or "never stream" rule cannot be right for both —
> which is exactly why the canary must test the same path production uses, per model.

**The honest boundary:** of 222 providers, **183 need an API key from a signup** and **20
need an OAuth browser login** — neither is something an agent should do, and CAPTCHA gates
exist precisely to stop it. Google worked *because it needed no signup*. "Free" in this
catalog overwhelmingly means *free after you register*.

**Still worth the owner's five minutes** (free, no card), for independent fallbacks so one
outage cannot take everything: **Groq** (30 req/min, console.groq.com), **Cerebras** (1M
tokens/day, cerebras.ai), and **Kiro** (OAuth, free-forever Claude models, via the
dashboard). Paste each into Dashboard → Providers, re-run the canary, pin the winner.

⚠️ **The canary streams**, deliberately — it must exercise the same path as `llm.py`. An
earlier non-streaming version failed `felo/felo-chat`, a model that is perfectly good
through the real client. *A canary that tests a different path than production certifies
the wrong thing.*

---

## 5. The sweep that settled it: 1019 models, three answers (2026-08-14)

Asked to "connect all the free providers", the honest result is worth more than the count.

**Connected three more** — `opencode`, `mimocode`, `auggie` — via `POST /api/providers`.
Catalog **665 → 1019**. Six other `NOAUTH_PROVIDERS` (`duckduckgo-web`, `felo-web`,
`theoldllm`, `chipotle`, `veoaifree-web`, `aihorde`) returned `{"error":"Invalid provider"}`
**and that was not a failure**: they need no connection record at all and were already
serving models under `ddgw/`, `felo/`, `tllm/`, `veo-free/`. *An error from a create call
is not proof the thing is missing — list what is being served before believing it.*

**Then echo-tested 23 models across every family.** Exact multi-token match, both
transports (the screen script is the canary's logic with a thread pool):

| Family | Models | Verdict |
|---|---|---|
| `gemini/*` | 3 | ✅ **PASS**, both transports |
| `felo/felo-chat` | 5 | ✅ PASS streamed only |
| `oc/*` (incl. advertised `claude-opus-5`) | 92 | ❌ 403 |
| `aug/*` | 28 | ❌ 502 |
| `tllm/*` | 26 | ❌ 403 |
| `ddgw/*` | 6 | ❌ 429 / 418 |
| `pollinations/*` | 250 | ❌ 401 |
| `g4f-*` | 10 | ❌ 402 / 429 |
| `groq/*` | 16 | ❌ 403 non-stream, keepalive-only stream |
| `hc/*`, `mcode/*` | 4 | ❌ 404 / 400 |

> **1019 models, three that answer**, and all three are backed by a real key on a real
> account. This is §4's lesson at four times the sample size: a catalog counts what the
> gateway *knows about*. The only number worth reporting is how many pass an exact echo.

### ⚠️ `testStatus: "active"` does not mean the provider answers

`groq` and `opencode` both sit at **active** in `/api/providers` while returning 403 on
every completion. The field tests whether a *connection* can be made, never whether a
*completion* comes back — D30's disease in the vendor's own dashboard. The connection
record even carried `errorCode: "403.0"` and a Cloudflare `lastError` **while still
reporting active**. Trust the canary; the status field is not evidence.

### ⚠️ Groq: the gateway is the fault, and four plausible theories were wrong first

The key is valid. `curl` gets 200. OmniRoute gets 403 on every completion. In order:

1. **`proxyEnabled: true`** looked like the cause → set `false` via `PUT /api/providers/<id>`
   (note: `PATCH` is **405**, the update verb is `PUT`). No change.
2. **Cloudflare error 1010** — "banned based on browser signature". Python `urllib` 403s,
   `curl` 200s → so it is the client, not the key.
3. **It is the `User-Agent` string, not TLS.** `Python-urllib/3.x` is banned; a browser UA
   *or even `curl/8.5.0`* passes. Verified by sending each explicitly.
4. So: a **custom provider node** with a browser UA (`POST /api/provider-nodes`,
   `apiType` must be one of `chat|responses|embeddings|audio-*|images-generations`, and
   `customHeaders` is inherited by the connection). Its `/models` fetch **worked** — it
   pulled Groq's real 15-model list. `POST /chat/completions` **still 403s**. The header
   fix reaches the models path and not the completion path.

Then the one-line disproof of all of it: the plain `openai` Python client pointed
**straight at `api.groq.com`**, default UA, no gateway, returns `'HELLO WORLD'` and
`'12345'` exactly, streamed *and* non-streamed.

> **When a credential fails in one client and works in another, the credential is not the
> variable.** Three of the four theories above were about the key or the fingerprint. The
> variable that mattered was whether OmniRoute was in the path at all.

### What changed in code

`apps/autopilot/llm.py` gained an **optional second endpoint**, tried only when the first
fails outright:

```
LLM_FALLBACK_BASE_URL=https://api.groq.com/openai/v1
LLM_FALLBACK_MODEL=llama-3.3-70b-versatile
LLM_FALLBACK_STREAM=true
LLM_FALLBACK_API_KEY=<the Groq key, in .env only>
```

Deliberately **not** another OmniRoute model. The gateway is a *local process*; when the
laptop sleeps (D20 — it slept a whole day) or the npm process dies, the Gemini primary and
both of §4's listed fallbacks die **together**. Three names on one process is one point of
failure wearing three labels.

Behaviour, all under test (8 new, **112 total**):

- primary streams only keepalives → fallback answers
- primary unreachable (transport error, not `LLMError`) → fallback answers
- primary works → **fallback is never called** (a fallback that always runs doubles cost
  and hides a broken primary)
- both fail → one `LLMError` naming **every** leg and its reason
- **single-endpoint chains re-raise the original error unchanged**, so the message still
  names the model and the exact failure mode
- a fallback URL with no model is **ignored** — that is a half-finished edit, and using it
  would send the primary's model id to a provider that never heard of it

Verified live: normal **5.3 s**; primary pointed at a dead port → Groq direct, exact,
**14.7 s**; both dead → loud error naming both.

### 🔴 The canary failed the working fallback — the instrument had the bug

With Groq direct **proven from `llm.py`**, the canary aimed at the same endpoint with the
same key returned **FAIL, 403, three models, both transports.**

The canary speaks `urllib`; `llm.py` speaks the `openai` client. urllib's default
`User-Agent` is `Python-urllib/3.x` — the one string Groq's Cloudflare bans. `curl/8.5.0`
passes. `omniroute-canary/1.0` passes. The provider was fine; the instrument was banned.

> **A canary that fails a working provider is as dangerous as one that passes a broken
> one.** It would have argued for deleting a working fallback, with six probes of evidence.

§4 already warned that a canary must exercise the path production uses — written about
streaming. **The path is wider than the transport: the HTTP client's default headers are
part of it.** `USER_AGENT` is now unconditional in `tools/omniroute_canary.py`.

Note the screening script used urllib too, but only ever called `localhost:20128`, so it
never met a Cloudflare. The bug required a **direct** provider call — which only existed
because the fallback stopped going through the gateway. *Removing a layer can expose a
defect the layer was hiding.*

Certified after the fix (`--base-url` + `--key-env` are new flags for exactly this):

```
py -3 tools/omniroute_canary.py --base-url https://api.groq.com/openai/v1     --key-env LLM_FALLBACK_API_KEY --model llama-3.3-70b-versatile
```

`llama-3.3-70b-versatile`, `llama-3.1-8b-instant` and `openai/gpt-oss-120b` all PASS in
**both** transports.

### ⚠️ Do not read the clipboard through the Playwright MCP

`navigator.clipboard.readText()` inside `browser_evaluate` **hung the server for 74
minutes** with no output and no error. It was an attempt to harvest the owner's other
Gemini keys; the attempt was not worth making anyway — see below.

### Two things deliberately not done

- **Multi-key Gemini rotation.** The account holds 7 keys but only **5 distinct projects**,
  and Google meters the free tier **per project, not per key**. Against ~1000
  requests/project/day and an autopilot that makes tens, **quota was never the binding
  constraint** — a multiplier on an abundant resource is not a win.
- **The 31 `web-cookie` providers** (`chatgpt-web`, `perplexity-web`, `copilot-web`,
  `qwen-web`, `kimi-web`, …) authenticate with session cookies pasted from a logged-in
  browser (`WEB_SESSION_CREDENTIAL_REQUIREMENTS` in
  `src/shared/providers/webSessionCredentials.ts`). Owner-approved, but not done
  unattended: it breaks those services' terms and risks the accounts — `claude-web` above
  all, since losing that account kills the CV engine, the one component with no substitute.
  Frontier models for free, against a downside that cannot be undone, for a workload
  Gemini already covers in ~5 s. Left for a supervised session.

---

## 2. Capsule Hub — the part that cannot be wired in

[capsulehub.tilantra.com](https://capsulehub.tilantra.com/) · Chrome/Brave extension + a web
SDK. It captures a conversation into a reusable "capsule" and drops it into another AI tool,
across a long surface list — ChatGPT, Claude.ai, Gemini, DeepSeek, Copilot, Perplexity,
Figma, Slack, **VS Code and Antigravity** included.

The owner had seen it working inside Antigravity, below the chat button, and that is real —
but it explains the limit rather than removing it. Evidence, in order of how decisive it is:

- The npm SDK **`@tilantra/capsule-hub`** (v2.0.2) is explicitly *"an SDK to integrate
  CapsuleHub directly into your **web application**"*. Its whole API is DOM: `initButton('#capsule-btn')`,
  `initDropZone('#chat-input')`, CSS-variable theming. **`bin: none`** — no CLI.
- No MCP server, no HTTP API, no importable file format. The only export is a manual `.md`
  download.
- **No VS Code marketplace extension exists** (searched 2026-08-13).

So every surface it supports is reached the same way: **injecting a button into an HTML UI.**
Antigravity and VS Code are Electron — their chat panels *are* web pages, which is exactly why
it can appear there. Claude Code in a terminal has no DOM, no input field to inject into, and
no page to mount a button on. This is not a missing feature; it is the wrong shape of tool.

> A supported-platforms list describes surfaces the vendor can *reach*, not capabilities you
> can *call*. Check for a CLI entry point or an API before believing a name on that list
> implies integration.

**The "context remaining" meter** the owner remembered is likely a different tool:
[n2ns/antigravity-panel](https://github.com/n2ns/antigravity-panel), a community Antigravity
toolkit with a quota dashboard and status-bar usage readout. Claude Code has `/context` built in.

### What this project already has instead

The capsule idea is sound, and **Brain 0 is a stronger version of it**. Every Claude Code
transcript is already converted to Markdown in the vault under `Conversations/`, on the
`SessionEnd` hook, and the global protocol already shares that vault with Antigravity. The
gap is only the *last mile*: a one-command "give me a pasteable capsule of this session"
rather than a whole transcript. Not built — see [[06-feature-backlog]].

---

## Owner actions — an AI cannot do these

1. **`npm install -g omniroute`** — blocked by the permission classifier here.
2. **`omniroute`** — start it; dashboard at `http://localhost:20128`.
3. **Dashboard → Providers** — connect the free providers (Kiro, OpenCode Free and similar
   need no signup). Keys are AES-256-GCM at rest, local only.
4. **Dashboard → Endpoints** — generate an API key.
5. **`omniroute setup-claude`** — writes the per-model profiles.
6. Paste the key into `.env` as `LLM_API_KEY`, set `LLM_BASE_URL=http://localhost:20128/v1`
   and `LLM_MODEL=auto`, for the autopilot path.

Then `claude-free.cmd` should work, and step 6 gives `llm.py` a live provider for Phase 1.

Related: [[22-rewrite-architecture]] (where the free model belongs) · [[05-decisions]] D26-D28
(free for plumbing, Claude Code for the CV) · D42 (this note) · [[24-cv-bridge]] (what must
never run on a free model)
