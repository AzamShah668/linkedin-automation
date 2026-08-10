#!/usr/bin/env python3
"""Scan past agent session transcripts for post-worthy content.

Sources scanned:
  1. Brain 3 (graphify-out/log.md) — session log entries with problems/solutions
  2. Brain 2 (docs/knowledge/) — decision entries with real engineering reasoning
  3. Claude Code transcripts (~/.claude/projects/) — user/assistant JSONL conversations
  4. Antigravity transcripts (~/.gemini/antigravity-ide/brain/) — user input steps
  5. Brain 1 Obsidian vault (Patterns/, Sessions/, Daily/) — cross-project knowledge

Usage:
    py -3 tools/scan_sessions.py                       # scan all, show top 10 ideas
    py -3 tools/scan_sessions.py --add                 # scan + add to Content Hub
    py -3 tools/scan_sessions.py --source brain2       # scan only Brain 2
    py -3 tools/scan_sessions.py --source brain3       # scan only graphify log
    py -3 tools/scan_sessions.py --source claude       # scan Claude transcripts
    py -3 tools/scan_sessions.py --source antigravity  # scan Antigravity transcripts
    py -3 tools/scan_sessions.py --source obsidian     # scan Obsidian vault
    py -3 tools/scan_sessions.py --since 7             # only sessions from last 7 days

Stdlib only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from content_hub_db import connect, add_idea, stats, all_posts  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
HOME = Path(os.path.expanduser("~"))

# Paths
BRAIN3_LOG = PROJECT_ROOT / "graphify-out" / "log.md"
BRAIN2_DIR = PROJECT_ROOT / "docs" / "knowledge"
CLAUDE_PROJECTS = HOME / ".claude" / "projects"
ANTIGRAVITY_BRAIN = HOME / ".gemini" / "antigravity-ide" / "brain"
OBSIDIAN_VAULT = HOME / "Desktop" / "obsedian" / "AntigravityKnowledge"

# Keywords that signal a post-worthy moment
SIGNAL_WORDS = [
    "root cause", "fix", "fixed", "bug", "gotcha", "trap", "lesson",
    "discovered", "found", "caught", "proved", "proven", "verified",
    "the real", "the actual", "key insight", "key finding", "headline",
    "decision", "architecture", "built", "shipped", "deployed",
    "D[0-9]+",  # decision references like D13, D17
    "failed", "broke", "broken", "crash", "error", "silent",
    "trick", "workaround", "the cause", "the problem",
]
SIGNAL_PATTERN = re.compile("|".join(SIGNAL_WORDS), re.IGNORECASE)


def scan_brain3_log() -> list[dict]:
    """Extract post-worthy entries from graphify-out/log.md session log."""
    if not BRAIN3_LOG.exists():
        return []

    ideas = []
    text = BRAIN3_LOG.read_text(encoding="utf-8")

    # Parse session entries: ## [date] session | title\nBody
    entries = re.split(r"^## ", text, flags=re.MULTILINE)[1:]
    for entry in entries:
        lines = entry.strip().split("\n")
        header = lines[0] if lines else ""
        body = "\n".join(lines[1:]).strip()

        # Extract date and title
        match = re.match(r"\[([^\]]+)\]\s*session\s*\|\s*(.+)", header)
        if not match:
            continue
        date_str, title = match.group(1), match.group(2).strip()

        # Score: count signal words in the body
        score = len(SIGNAL_PATTERN.findall(body))
        if score < 2:
            continue  # skip trivial entries

        # Extract the most interesting sentence
        sentences = re.split(r"[.!]\s+", body)
        best_sentence = max(sentences, key=lambda s: len(SIGNAL_PATTERN.findall(s)), default="")

        ideas.append({
            "title": title,
            "insight": best_sentence[:300],
            "source": "brain3-log",
            "date": date_str,
            "score": score,
            "post_type": "daily-build",
        })

    return sorted(ideas, key=lambda x: x["score"], reverse=True)


def scan_brain2_decisions() -> list[dict]:
    """Extract decisions from docs/knowledge/05-decisions.md and other files."""
    ideas = []
    if not BRAIN2_DIR.exists():
        return ideas

    for md_file in BRAIN2_DIR.glob("*.md"):
        if md_file.name == "00-INDEX.md":
            continue

        text = md_file.read_text(encoding="utf-8", errors="replace")

        # Find decision blocks (D1, D2, ..., D36)
        decision_blocks = re.findall(
            r"(D\d+[:\s].{20,300})", text
        )
        for block in decision_blocks:
            # Extract the decision number and text
            match = re.match(r"(D\d+)[:\s]+(.+)", block)
            if match:
                d_num = match.group(1)
                d_text = match.group(2).strip()
                if len(d_text) > 30:
                    ideas.append({
                        "title": f"Engineering Decision {d_num}: {d_text[:80]}",
                        "insight": d_text[:300],
                        "source": f"brain2/{md_file.name}",
                        "date": "",
                        "score": 3,
                        "post_type": "lesson",
                    })

        # Find sections with strong signal words
        sections = re.split(r"^#{1,3}\s+", text, flags=re.MULTILINE)[1:]
        for section in sections:
            section_lines = section.strip().split("\n")
            section_title = section_lines[0].strip() if section_lines else ""
            section_body = "\n".join(section_lines[1:]).strip()

            score = len(SIGNAL_PATTERN.findall(section_body))
            if score >= 3 and len(section_body) > 50:
                best_sentence = max(
                    re.split(r"[.!]\s+", section_body),
                    key=lambda s: len(SIGNAL_PATTERN.findall(s)),
                    default=""
                )
                ideas.append({
                    "title": f"{section_title}",
                    "insight": best_sentence[:300],
                    "source": f"brain2/{md_file.name}",
                    "date": "",
                    "score": score,
                    "post_type": "lesson",
                })

    return sorted(ideas, key=lambda x: x["score"], reverse=True)


def scan_claude_transcripts(since_days: int = 30) -> list[dict]:
    """Scan Claude Code JSONL transcripts for user problems and AI solutions."""
    ideas = []
    linkedin_project = CLAUDE_PROJECTS / "d--linkdin-automation"

    if not linkedin_project.exists():
        return ideas

    cutoff = dt.datetime.now() - dt.timedelta(days=since_days)

    for jsonl_file in sorted(linkedin_project.glob("*.jsonl"),
                             key=lambda p: p.stat().st_mtime, reverse=True):
        file_date = dt.datetime.fromtimestamp(jsonl_file.stat().st_mtime)
        if file_date < cutoff:
            continue

        try:
            user_messages = []
            with open(jsonl_file, encoding="utf-8", errors="replace") as f:
                for line in f:
                    try:
                        obj = json.loads(line.strip())
                        if obj.get("type") == "user":
                            content = obj.get("message", {}).get("content", "")
                            if isinstance(content, list):
                                text = " ".join(
                                    c.get("text", "") for c in content
                                    if isinstance(c, dict) and c.get("type") == "text"
                                )
                            elif isinstance(content, str):
                                text = content
                            else:
                                text = ""
                            if text and len(text) > 20:
                                user_messages.append(text[:500])
                    except (json.JSONDecodeError, TypeError):
                        continue

            # Look for problem/solution patterns in user messages
            for msg in user_messages:
                score = len(SIGNAL_PATTERN.findall(msg))
                if score >= 2:
                    # Clean up the message for a title
                    title_words = msg.split()[:12]
                    title = " ".join(title_words)
                    if len(title) < 15:
                        continue

                    ideas.append({
                        "title": title,
                        "insight": msg[:300],
                        "source": f"claude/{jsonl_file.stem[:8]}",
                        "date": file_date.strftime("%Y-%m-%d"),
                        "score": score,
                        "post_type": "daily-build",
                    })
        except Exception:
            continue

    return sorted(ideas, key=lambda x: x["score"], reverse=True)


def scan_antigravity_transcripts(since_days: int = 30) -> list[dict]:
    """Scan Antigravity JSONL transcripts for user problems and solutions."""
    ideas = []
    if not ANTIGRAVITY_BRAIN.exists():
        return ideas

    cutoff = dt.datetime.now() - dt.timedelta(days=since_days)

    for session_dir in ANTIGRAVITY_BRAIN.iterdir():
        if not session_dir.is_dir() or session_dir.name == "tempmediaStorage":
            continue

        transcript = session_dir / ".system_generated" / "logs" / "transcript.jsonl"
        if not transcript.exists():
            continue

        file_date = dt.datetime.fromtimestamp(transcript.stat().st_mtime)
        if file_date < cutoff:
            continue

        try:
            user_inputs = []
            with open(transcript, encoding="utf-8", errors="replace") as f:
                for line in f:
                    try:
                        obj = json.loads(line.strip())
                        if obj.get("type") == "USER_INPUT" and obj.get("source") == "USER_EXPLICIT":
                            content = obj.get("content", "")
                            if content and len(content) > 30:
                                # Strip XML tags
                                clean = re.sub(r"<[^>]+>", " ", content)
                                clean = re.sub(r"\s+", " ", clean).strip()
                                if len(clean) > 30:
                                    user_inputs.append(clean[:500])
                    except (json.JSONDecodeError, TypeError):
                        continue

            for msg in user_inputs:
                score = len(SIGNAL_PATTERN.findall(msg))
                if score >= 2:
                    title_words = msg.split()[:12]
                    title = " ".join(title_words)
                    if len(title) < 15:
                        continue

                    ideas.append({
                        "title": title,
                        "insight": msg[:300],
                        "source": f"antigravity/{session_dir.name[:8]}",
                        "date": file_date.strftime("%Y-%m-%d"),
                        "score": score,
                        "post_type": "daily-build",
                    })
        except Exception:
            continue

    return sorted(ideas, key=lambda x: x["score"], reverse=True)


def scan_obsidian_vault() -> list[dict]:
    """Scan Brain 1 Obsidian vault for patterns and insights."""
    ideas = []
    if not OBSIDIAN_VAULT.exists():
        return ideas

    for md_file in OBSIDIAN_VAULT.rglob("*.md"):
        try:
            text = md_file.read_text(encoding="utf-8", errors="replace")
            score = len(SIGNAL_PATTERN.findall(text))

            if score >= 3:
                # Extract title from filename or first heading
                title = md_file.stem.replace("_", " ").replace("-", " ")
                first_heading = re.search(r"^#\s+(.+)", text, re.MULTILINE)
                if first_heading:
                    title = first_heading.group(1).strip()

                best_sentence = max(
                    re.split(r"[.!]\s+", text),
                    key=lambda s: len(SIGNAL_PATTERN.findall(s)),
                    default=""
                )

                ideas.append({
                    "title": title,
                    "insight": best_sentence[:300],
                    "source": f"obsidian/{md_file.parent.name}/{md_file.name}",
                    "date": "",
                    "score": score,
                    "post_type": "lesson",
                })
        except Exception:
            continue

    return sorted(ideas, key=lambda x: x["score"], reverse=True)


def deduplicate_against_hub(ideas: list[dict], conn) -> list[dict]:
    """Remove ideas that are already in the Content Hub (by fuzzy title match)."""
    existing = all_posts(conn)
    existing_titles = {p["title"].lower() for p in existing}

    unique = []
    for idea in ideas:
        title_lower = idea["title"].lower()
        # Simple overlap check
        is_dup = False
        for existing_title in existing_titles:
            words_a = set(title_lower.split())
            words_b = set(existing_title.split())
            if len(words_a & words_b) / max(len(words_a | words_b), 1) > 0.4:
                is_dup = True
                break
        if not is_dup:
            unique.append(idea)
    return unique


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan session transcripts for post ideas")
    parser.add_argument("--add", action="store_true", help="Add top ideas to Content Hub")
    parser.add_argument("--count", "-n", type=int, default=10, help="Max ideas to show/add")
    parser.add_argument("--since", type=int, default=30, help="Days to look back for transcripts")
    parser.add_argument(
        "--source", default="all",
        choices=["all", "brain2", "brain3", "claude", "antigravity", "obsidian"],
        help="Which source to scan"
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    all_ideas: list[dict] = []

    if args.source in ("all", "brain3"):
        b3 = scan_brain3_log()
        all_ideas.extend(b3)
        print(f"  Brain 3 (graphify log): {len(b3)} candidates")

    if args.source in ("all", "brain2"):
        b2 = scan_brain2_decisions()
        all_ideas.extend(b2)
        print(f"  Brain 2 (knowledge):    {len(b2)} candidates")

    if args.source in ("all", "claude"):
        cl = scan_claude_transcripts(since_days=args.since)
        all_ideas.extend(cl)
        print(f"  Claude transcripts:     {len(cl)} candidates")

    if args.source in ("all", "antigravity"):
        ag = scan_antigravity_transcripts(since_days=args.since)
        all_ideas.extend(ag)
        print(f"  Antigravity transcripts:{len(ag)} candidates")

    if args.source in ("all", "obsidian"):
        ob = scan_obsidian_vault()
        all_ideas.extend(ob)
        print(f"  Obsidian vault:         {len(ob)} candidates")

    # Sort by score, deduplicate
    all_ideas.sort(key=lambda x: x["score"], reverse=True)

    conn = connect()
    unique = deduplicate_against_hub(all_ideas, conn)[:args.count]

    if not unique:
        print("\n[Scanner] No new post-worthy ideas found.")
        return

    print(f"\n{'='*70}")
    print(f"  Top {len(unique)} post-worthy discoveries (not yet in Content Hub)")
    print(f"{'='*70}\n")

    for i, idea in enumerate(unique, 1):
        print(f"  {i}. [{idea['post_type']}] Score: {idea['score']}")
        print(f"     {idea['title'][:80]}")
        print(f"     Source: {idea['source']}  {idea.get('date', '')}")
        print(f"     Insight: {idea['insight'][:120]}...")
        print()

    if args.add:
        added = 0
        for idea in unique:
            row_id = add_idea(
                conn,
                title=idea["title"][:200],
                post_type=idea["post_type"],
                insight=idea["insight"],
                source=f"scan/{idea['source']}",
            )
            added += 1
            print(f"  Added #{row_id}: {idea['title'][:60]}")
        s = stats(conn)
        print(f"\nAdded {added} ideas. Hub now has {s['total']} post(s)")
    elif args.json:
        print(json.dumps(unique, indent=2, default=str))
    else:
        print(f"  Run with --add to add these to the Content Hub.")


if __name__ == "__main__":
    main()
