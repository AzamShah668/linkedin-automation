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
from pathlib import Path

GATEWAY = "http://localhost:20128/v1"
TIMEOUT_SECONDS = 90

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


def _api_key() -> str:
    """The gateway key, from the environment or .env. Never hardcoded (repo is public)."""
    key = os.getenv("LLM_API_KEY")
    if key:
        return key.strip()
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("LLM_API_KEY=") and not line.startswith("#"):
                return line.split("=", 1)[1].strip()
    return "local"


def ask_once(model: str, prompt: str, *, stream: bool) -> tuple[str, str]:
    """Return (answer, model_actually_used). Raises on transport/protocol failure.

    Tests BOTH modes because the gateway breaks in both directions, per provider:
    felo eats the first token when not streaming; groq streams nothing but keepalives.
    Certifying only one mode would bless a model that fails in the mode you deploy.
    """
    request = urllib.request.Request(
        f"{GATEWAY}/chat/completions",
        data=json.dumps(
            {
                "model": model,
                "max_tokens": PROBE_MAX_TOKENS,
                "stream": stream,
                "messages": [{"role": "user", "content": prompt}],
            }
        ).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {_api_key()}"},
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


def test_mode(model: str, *, stream: bool) -> tuple[bool, list[str]]:
    """True only if every probe round-trips exactly. Ambiguity counts as failure."""
    notes: list[str] = []
    ok = True
    for prompt, expected in PROBES:
        try:
            answer, used = ask_once(model, prompt, stream=stream)
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


def test_model(model: str) -> dict[str, tuple[bool, list[str]]]:
    """Probe both transport modes. A model is usable if EITHER passes cleanly."""
    return {
        "stream": test_mode(model, stream=True),
        "non-stream": test_mode(model, stream=False),
    }


def list_models() -> list[str]:
    request = urllib.request.Request(
        f"{GATEWAY}/models", headers={"Authorization": f"Bearer {_api_key()}"}
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return [m["id"] for m in payload.get("data", [])]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", action="append", dest="models", help="model id (repeatable)")
    parser.add_argument("--all", action="store_true", help="sweep every model the gateway lists")
    args = parser.parse_args()

    if args.all:
        try:
            models = list_models()
        except Exception as exc:  # noqa: BLE001
            print(f"cannot reach {GATEWAY}/models - is the gateway running? ({exc})")
            return 2
    else:
        models = args.models or DEFAULT_CANDIDATES

    print(f"Probing {len(models)} model(s) in both transport modes.\n")
    passed: list[tuple[str, str]] = []
    for model in models:
        results = test_model(model)
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
