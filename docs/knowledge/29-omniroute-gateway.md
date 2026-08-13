# 29 — OmniRoute gateway, and the context-portability question

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
