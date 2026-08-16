"""Find which OmniRoute models can be trusted to return an answer intact.

WHY THIS EXISTS (measured 2026-08-13, first hour of using the gateway)
----------------------------------------------------------------------
`auto/best-fast` routes to a different free provider on each call, and they are NOT
uniformly correct. Asked to reply "PONG", three providers answered:

    felo-chat    -> 'ONG'     first token dropped
    big-pickle   -> 'ONG'     first token dropped
    hy3-free     -> 'PONG'    correct

It is not a truncated character, it is the whole first token: 'HELLO WORLD' came back
'WORLD', '12345' came back '45'. The HTTP status is 200 and the JSON is well formed, so
nothing downstream can tell a mangled answer from a real one.

That is the dangerous shape this project already knows: a wrong value that passes every
structural check (D31 - the answer bank proves where a value came from, not that it is
right; D30 - nothing observed is not nothing wrong). A silently truncated fit score is
merely wrong; a silently truncated free-text answer on an employer's form is worse.

So: never point the autopilot at `auto/*`. Pin a model this canary passes.

    py -3 tools/omniroute_canary.py                 # test the default candidates
    py -3 tools/omniroute_canary.py --model hy3-free --model glm/glm-5.2
    py -3 tools/omniroute_canary.py --all           # sweep every model the gateway lists

Related: docs/knowledge/29-omniroute-gateway.md, decision D42.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

GATEWAY = "http://localhost:20128/v1"
TIMEOUT_SECONDS = 90

# ⚠️ SET UNCONDITIONALLY, and never remove it.
#
# urllib's default User-Agent is `Python-urllib/3.x`, and Groq's Cloudflare BANS that exact
# string with a 403 (error 1010, "banned based on browser signature"). Any other UA passes
# - `curl/8.5.0` and this one both do. Measured 2026-08-14.
#
# This bit the canary itself: it reported FAIL for all three Groq models at the very moment
# `apps/autopilot/llm.py` was answering correctly against the same endpoint with the same
# key, because the `openai` client sends its own UA and urllib did not. A canary that fails
# a WORKING provider is exactly as dangerous as one that passes a broken one - it would
# have argued for deleting a fallback that works. This file's own docstring says a canary
# must exercise the path production uses; the HTTP client's default headers are part of
# that path.
USER_AGENT = "omniroute-canary/1.0"

# Generous on purpose. Reasoning models (every current Gemini, and several others here)
# spend tokens on a hidden thinking pass BEFORE the answer, and the budget is shared. At
# max_tokens=64, gemini-3.5-flash-lite returned '123' for "12345" and gemini-flash-latest
# returned an empty string with finish_reason=length - the thinking had consumed it all.
# Measured 2026-08-13; at 200 tokens the same model answers exactly. A canary must not
# fail a model for a budget it set too low, or it condemns the good models.
PROBE_MAX_TOKENS = 512

# Each probe is (instruction, exact expected answer). The answers are deliberately
# multi-token so that losing the first token is visible; a single-token answer like "4"
# survives the bug and would report a false PASS.
PROBES = [
    ("Reply with exactly this and nothing else: PONG", "PONG"),
    ("Reply with exactly this and nothing else: HELLO WORLD", "HELLO WORLD"),
    ("Reply with exactly this and nothing else: 12345", "12345"),
]

DEFAULT_CANDIDATES = ["auto/best-fast", "auto/best-coding", "auto/best-reasoning"]


def _api_key(env_name: str = "LLM_API_KEY") -> str:
    """A key, from the environment or .env. Never hardcoded (repo is public)."""
    key = os.getenv(env_name)
    if key:
        return key.strip()
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        prefix = f"{env_name}="
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith(prefix) and not line.startswith("#"):
                return line.split("=", 1)[1].strip()
    return "local"


def ask_once(
    model: str, prompt: str, *, stream: bool, base_url: str = GATEWAY, key_env: str = "LLM_API_KEY"
) -> tuple[str, str]:
    """Return (answer, model_actually_used). Raises on transport/protocol failure.

    Tests BOTH modes because the gateway breaks in both directions, per provider:
    felo eats the first token when not streaming; groq streams nothing but keepalives.
    Certifying only one mode would bless a model that fails in the mode you deploy.

    `base_url` exists because the fallback endpoint (D43) does NOT go through the gateway
    at all - it talks straight to api.groq.com. A canary that can only probe :20128
    certifies the primary and leaves the thing that runs when the primary dies untested,
    which is the failure this file's own docstring warns about.
    """
    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(
            {
                "model": model,
                "max_tokens": PROBE_MAX_TOKENS,
                "stream": stream,
                "messages": [{"role": "user", "content": prompt}],
            }
        ).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {_api_key(key_env)}",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        if not stream:
            body = json.loads(response.read().decode("utf-8"))
            choices = body.get("choices")
            if not choices:
                raise RuntimeError(f"no choices in response: {str(body)[:120]}")
            content = (choices[0].get("message") or {}).get("content")
            if not content:
                raise RuntimeError("response contained no content")
            return content.strip(), body.get("model") or "?"

        chunks: list[str] = []
        used = "?"
        for raw in response:
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data:"):
                continue
            payload = line[5:].strip()
            if payload == "[DONE]":
                break
            try:
                event = json.loads(payload)
            except json.JSONDecodeError:
                continue
            # OmniRoute emits `omniroute-keepalive` frames; a stream can be nothing but
            # those and then close, with HTTP 200 and no error. Do not count them.
            if event.get("id") == "omniroute-keepalive":
                continue
            used = event.get("model") or used
            for choice in event.get("choices") or []:
                piece = (choice.get("delta") or {}).get("content")
                if piece:
                    chunks.append(piece)

    if not chunks:
        raise RuntimeError("stream produced no content at all (keepalives only?)")
    return "".join(chunks).strip(), used


def test_mode(
    model: str, *, stream: bool, base_url: str = GATEWAY, key_env: str = "LLM_API_KEY"
) -> tuple[bool, list[str]]:
    """True only if every probe round-trips exactly. Ambiguity counts as failure."""
    notes: list[str] = []
    ok = True
    for prompt, expected in PROBES:
        try:
            answer, used = ask_once(
                model, prompt, stream=stream, base_url=base_url, key_env=key_env
            )
        except urllib.error.HTTPError as exc:
            notes.append(f"HTTP {exc.code} ({exc.reason})")
            ok = False
            continue
        except Exception as exc:  # noqa: BLE001 - report anything, never guess
            notes.append(f"{type(exc).__name__}: {str(exc)[:90]}")
            ok = False
            continue

        if answer == expected:
            notes.append(f"ok via {used}")
        else:
            ok = False
            if expected.endswith(answer):
                notes.append(f"TRUNCATED via {used}: {answer!r} (lost the first token)")
            else:
                notes.append(f"WRONG via {used}: {answer!r} != {expected!r}")
    return ok, notes


def test_model(
    model: str, *, base_url: str = GATEWAY, key_env: str = "LLM_API_KEY"
) -> dict[str, tuple[bool, list[str]]]:
    """Probe both transport modes. A model is usable if EITHER passes cleanly."""
    return {
        "stream": test_mode(model, stream=True, base_url=base_url, key_env=key_env),
        "non-stream": test_mode(model, stream=False, base_url=base_url, key_env=key_env),
    }


def list_models(base_url: str = GATEWAY, key_env: str = "LLM_API_KEY") -> list[str]:
    request = urllib.request.Request(
        f"{base_url}/models",
        headers={"Authorization": f"Bearer {_api_key(key_env)}", "User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return [m["id"] for m in payload.get("data", [])]


def certify() -> int:
    """Probe the tiers this project is actually configured to use, and record the verdict.

    WHY THIS IS NOT `--all`. The catalog listed **1019 models and three answered** (D43), and
    `testStatus: "active"` answers the wrong question entirely — `groq` and `opencode` both
    reported active while 403-ing every completion. Sweeping the catalog tells you about the
    gateway; this tells you whether the four settings the pipeline will actually load are sound.

    The fallback is probed on **its own endpoint**, never through the gateway. It exists precisely
    for when the gateway is dead, so certifying it through the gateway would certify nothing (D43).
    """
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, repo)
    from apps.autopilot import env as envfile

    envfile.load()

    tiers = [
        ("fast  (LLM_MODEL)", os.getenv("LLM_MODEL"), GATEWAY, "LLM_API_KEY"),
        ("heavy (LLM_CV_MODEL)", os.getenv("LLM_CV_MODEL"), GATEWAY, "LLM_API_KEY"),
        ("fallback (LLM_FALLBACK_MODEL)", os.getenv("LLM_FALLBACK_MODEL"),
         os.getenv("LLM_FALLBACK_BASE_URL"), "LLM_FALLBACK_API_KEY"),
    ]

    report: dict[str, dict] = {}
    problems: list[str] = []

    for label, model, base_url, key_env in tiers:
        if not model:
            print(f"SKIP  {label}: not configured")
            report[label] = {"model": None, "status": "unconfigured"}
            continue
        if not base_url:
            print(f"FAIL  {label}: {model} has no base URL configured")
            problems.append(f"{label}: no base URL")
            report[label] = {"model": model, "status": "no-base-url"}
            continue
        # An `auto/*` id is a different provider every call, so certifying one certifies nothing.
        if model.startswith("auto/"):
            print(f"FAIL  {label}: {model} is an auto/* id - a different provider every call (D43)")
            problems.append(f"{label}: auto/* must never be pinned")
            report[label] = {"model": model, "status": "auto-id-refused"}
            continue

        results = test_model(model, base_url=base_url, key_env=key_env)
        modes = [mode for mode, (ok, _notes) in results.items() if ok]
        ok = bool(modes)
        print(f"{'PASS' if ok else 'FAIL'}  {label}: {model}  ({base_url})")
        for mode, (passed, notes) in results.items():
            print(f"    {'ok  ' if passed else 'fail'}  {mode}")
            for note in notes:
                print(f"            {note}")
        if not ok:
            problems.append(f"{label}: {model} returned nothing usable")
        report[label] = {"model": model, "base_url": base_url,
                         "status": "pass" if ok else "fail", "modes": modes}

    out_dir = os.path.join(repo, "output", "llm")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "verified-models.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump({"checked_at": datetime.now().isoformat(timespec="seconds"),
                   "tiers": report}, handle, indent=2, ensure_ascii=False)
    print(f"\nwritten: {os.path.relpath(out_path, repo)}")

    if problems:
        print("\nNOT READY:")
        for line in problems:
            print(f"  - {line}")
        return 1
    print("\nEvery configured tier answered an exact multi-token echo.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", action="append", dest="models", help="model id (repeatable)")
    parser.add_argument("--all", action="store_true", help="sweep every model the gateway lists")
    parser.add_argument(
        "--base-url",
        default=GATEWAY,
        help="endpoint to probe (default the local gateway). Use the provider's own URL to "
        "certify the FALLBACK, which does not go through the gateway at all - see D43.",
    )
    parser.add_argument(
        "--key-env",
        default="LLM_API_KEY",
        help="env/.env name holding the key for --base-url (e.g. LLM_FALLBACK_API_KEY)",
    )
    parser.add_argument(
        "--certify",
        action="store_true",
        help="probe the tiers actually configured in .env (LLM_MODEL, LLM_CV_MODEL, and the "
        "fallback on its OWN endpoint) and write output/llm/verified-models.json",
    )
    args = parser.parse_args()

    if args.certify:
        return certify()

    if args.all:
        try:
            models = list_models(args.base_url, args.key_env)
        except Exception as exc:  # noqa: BLE001
            print(f"cannot reach {args.base_url}/models - is it running? ({exc})")
            return 2
    else:
        models = args.models or DEFAULT_CANDIDATES

    print(f"Probing {len(models)} model(s) at {args.base_url} in both transport modes.\n")
    passed: list[tuple[str, str]] = []
    for model in models:
        results = test_model(model, base_url=args.base_url, key_env=args.key_env)
        verdict = "PASS" if any(ok for ok, _ in results.values()) else "FAIL"
        print(f"{verdict}  {model}")
        for mode, (ok, notes) in results.items():
            print(f"    {'ok  ' if ok else 'fail'}  {mode}")
            for note in notes:
                print(f"            {note}")
            if ok:
                passed.append((model, mode))

    print()
    if passed:
        print("Safe to pin (set LLM_MODEL, and LLM_STREAM to match the mode):")
        for model, mode in passed:
            flag = "true" if mode == "stream" else "false"
            print(f"  LLM_MODEL={model}   LLM_STREAM={flag}")
    else:
        print("NOTHING PASSED. Do not point the autopilot at this gateway yet.")
        print("An `auto/*` id is a different provider every call - re-run before concluding.")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
