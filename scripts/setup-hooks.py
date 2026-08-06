#!/usr/bin/env python3
"""Install the graphify git hooks with an interpreter path that actually works.

WHY THIS EXISTS (2026-08-06). `.git/hooks/` is not version-controlled, so hook fixes do not
survive a clone. Worse, the default install picks its interpreter with `command -v python3`,
and on Windows that finds the **Windows Store App Execution Alias stub** in
`.../Microsoft/WindowsApps/python3`. The stub is a real executable, so `command -v` succeeds and
the hook selects it — but it has no site-packages, so `import graphify` fails on every commit.

The result was eleven days of silence: every commit printed "No module named 'graphify'" while
`graphify hook status` cheerfully reported both hooks installed. Both statements were true; they
described different environments. `graph.json` sat at 75 nodes while the code moved on.

    py -3 scripts/setup-hooks.py            install / repair
    py -3 scripts/setup-hooks.py --check    verify only, non-zero exit if broken

Judge the result by `graphify-out/graph.json`'s mtime after a commit, never by a status line.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HOOKS = REPO / ".git" / "hooks"
HOOK_NAMES = ("post-commit", "post-checkout")

OLD_SELECTOR = re.compile(
    rb"if command -v python3 [^\r\n]*\r?\n"
    rb"elif command -v py [^\r\n]*\r?\n"
    rb"else PY=python; fi"
)


def _bash_path(exe: Path) -> str:
    """C:\\Foo\\python.exe -> /c/Foo/python.exe, which is what Git Bash needs."""
    text = exe.as_posix()
    if len(text) > 1 and text[1] == ":":
        text = f"/{text[0].lower()}{text[2:]}"
    return text


def _selector(exe: Path) -> bytes:
    return (
        "# Absolute path, installed by scripts/setup-hooks.py.\n"
        "# git runs hooks in Git Bash, where `command -v python3` finds the Windows Store\n"
        "# App Execution Alias stub - a real executable with no site-packages. Selecting it\n"
        "# made every rebuild die with \"No module named 'graphify'\" while `hook status`\n"
        "# reported the hooks installed. Both were true; they described different shells.\n"
        f'GRAPHIFY_PY="{_bash_path(exe)}"\n'
        "if [ ! -x \"$GRAPHIFY_PY\" ]; then\n"
        "    if command -v py >/dev/null 2>&1; then GRAPHIFY_PY=\"py\"; else GRAPHIFY_PY=\"python\"; fi\n"
        "fi"
    ).encode()


def find_interpreter() -> Path | None:
    """An interpreter that can actually import graphify. Prefer the one running this script."""
    candidates = [Path(sys.executable)]
    for probe in (["py", "-3"], ["python3"], ["python"]):
        try:
            out = subprocess.run(
                [*probe, "-c", "import sys; print(sys.executable)"],
                capture_output=True, text=True, timeout=30,
            )
            if out.returncode == 0 and out.stdout.strip():
                candidates.append(Path(out.stdout.strip()))
        except (OSError, subprocess.SubprocessError):
            continue

    seen: set[Path] = set()
    for exe in candidates:
        if exe in seen or not exe.exists():
            continue
        seen.add(exe)
        check = subprocess.run(
            [str(exe), "-c", "import graphify"], capture_output=True, text=True, timeout=60
        )
        if check.returncode == 0:
            return exe
    return None


def hook_status() -> list[tuple[str, bool, str]]:
    """(name, ok, detail) per hook. `ok` means it names an interpreter that has graphify."""
    out = []
    for name in HOOK_NAMES:
        path = HOOKS / name
        if not path.exists():
            out.append((name, False, "not installed"))
            continue
        body = path.read_bytes()
        if OLD_SELECTOR.search(body):
            out.append((name, False, "uses `command -v python3` - will pick the WindowsApps stub"))
            continue
        match = re.search(rb'GRAPHIFY_PY="([^"]+)"', body)
        if not match:
            out.append((name, False, "no GRAPHIFY_PY defined"))
            continue
        out.append((name, True, match.group(1).decode()))
    return out


def install(exe: Path) -> int:
    patched = 0
    for name in HOOK_NAMES:
        path = HOOKS / name
        if not path.exists():
            print(f"  {name}: absent — run `py -3 -m graphify hook install` first, then re-run this")
            continue
        body = path.read_bytes()
        new = OLD_SELECTOR.sub(_selector(exe), body)
        new = re.sub(rb'GRAPHIFY_PY="[^"]+"', f'GRAPHIFY_PY="{_bash_path(exe)}"'.encode(), new)
        new = new.replace(b"$RUN $PY -c ", b'$RUN "$GRAPHIFY_PY" -c ').replace(
            b"$PY -c ", b'"$GRAPHIFY_PY" -c '
        )
        if new != body:
            path.write_bytes(new)
            patched += 1
            print(f"  {name}: patched -> {_bash_path(exe)}")
        else:
            print(f"  {name}: already correct")
    return patched


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify only; non-zero exit if broken")
    args = parser.parse_args()

    if not HOOKS.exists():
        print(f"no .git/hooks at {HOOKS} — is this a git clone?")
        return 1

    if args.check:
        ok = True
        for name, good, detail in hook_status():
            print(f"  {'OK  ' if good else 'BAD '} {name}: {detail}")
            ok &= good
        graph = REPO / "graphify-out" / "graph.json"
        if graph.exists():
            print(f"\n  graph.json last written: {graph.stat().st_mtime}")
            print("  (compare that to your last commit — the artifact is the only real proof)")
        return 0 if ok else 1

    exe = find_interpreter()
    if exe is None:
        print("No interpreter found that can `import graphify`.")
        print("Install it first:  py -3 -m pip install graphify")
        return 1
    print(f"interpreter with graphify: {exe}")
    install(exe)
    print("\nDone. Verify by committing, then checking graphify-out/graph.json's mtime.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
