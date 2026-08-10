#!/usr/bin/env python3
"""Fetch trending tech topics and add them to the Content Hub as post ideas.

    py -3 tools/trend_finder.py                    # fetch & add 3 trends
    py -3 tools/trend_finder.py --count 5          # fetch 5
    py -3 tools/trend_finder.py --dry-run          # show what would be added
    py -3 tools/trend_finder.py --query "AI agents" # custom search focus

Uses web search (free, no API key) to find trending tech discussions,
then filters for LinkedIn-worthy topics. Stdlib + urllib only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from content_hub_db import connect, add_idea, stats  # noqa: E402

# Curated search queries that surface engineering-relevant trending topics
DEFAULT_QUERIES = [
    "trending software engineering topics this week 2026",
    "AI developer tools trending today",
    "cloud computing platform engineering news this week",
    "DevOps automation trending discussions",
    "machine learning infrastructure new developments",
]

# Day mapping for non-project posts
DAILY_SLOTS = {
    0: "mon",   # Monday    → Daily Build
    2: "wed",   # Wednesday → Trend
    4: "fri",   # Friday    → Lesson
    5: "sat",   # Saturday  → Reflection
    6: "sun",   # Sunday    → Reflection
}


def fetch_trending_via_newsdata(query: str, count: int = 5) -> list[dict]:
    """Fetch headlines from NewsData.io (free tier, 200 credits/day, no key needed for basic)."""
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://newsdata.io/api/1/latest?q={encoded}&language=en&category=technology&size={count}"
        req = urllib.request.Request(url, headers={"User-Agent": "ContentHub/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results = []
            for article in data.get("results", [])[:count]:
                results.append({
                    "title": article.get("title", ""),
                    "description": article.get("description", ""),
                    "source": article.get("source_name", "web"),
                    "url": article.get("link", ""),
                })
            return results
    except Exception:
        return []


def fetch_trending_via_currents(query: str, count: int = 5) -> list[dict]:
    """Fetch from Currents API (free, ~1000 req/day)."""
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://api.currentsapi.services/v1/search?keywords={encoded}&language=en&category=technology"
        req = urllib.request.Request(url, headers={"User-Agent": "ContentHub/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results = []
            for article in data.get("news", [])[:count]:
                results.append({
                    "title": article.get("title", ""),
                    "description": article.get("description", ""),
                    "source": article.get("author", "web"),
                    "url": article.get("url", ""),
                })
            return results
    except Exception:
        return []


def fetch_trending_via_hacker_news(count: int = 5) -> list[dict]:
    """Fetch top stories from Hacker News API (free, no key, no limits)."""
    try:
        url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        req = urllib.request.Request(url, headers={"User-Agent": "ContentHub/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            story_ids = json.loads(resp.read().decode("utf-8"))[:count * 2]

        results = []
        for sid in story_ids:
            if len(results) >= count:
                break
            try:
                surl = f"https://hacker-news.firebaseio.com/v0/item/{sid}.json"
                sreq = urllib.request.Request(surl, headers={"User-Agent": "ContentHub/1.0"})
                with urllib.request.urlopen(sreq, timeout=5) as sresp:
                    story = json.loads(sresp.read().decode("utf-8"))
                    title = story.get("title", "")
                    # Filter: only tech/engineering stories with decent engagement
                    score = story.get("score", 0)
                    if score >= 50 and title:
                        results.append({
                            "title": title,
                            "description": f"HN score: {score} | {story.get('descendants', 0)} comments",
                            "source": "Hacker News",
                            "url": story.get("url", f"https://news.ycombinator.com/item?id={sid}"),
                        })
            except Exception:
                continue
        return results
    except Exception:
        return []


def deduplicate_topics(topics: list[dict]) -> list[dict]:
    """Remove near-duplicate titles."""
    seen_words: list[set] = []
    unique = []
    for t in topics:
        words = set(t["title"].lower().split())
        is_dup = False
        for sw in seen_words:
            overlap = len(words & sw) / max(len(words | sw), 1)
            if overlap > 0.5:
                is_dup = True
                break
        if not is_dup:
            seen_words.append(words)
            unique.append(t)
    return unique


def determine_post_type(title: str) -> str:
    """Heuristic to classify a trending topic into a post type."""
    lower = title.lower()
    if any(w in lower for w in ["how", "built", "fixed", "debugged", "learned"]):
        return "daily-build"
    if any(w in lower for w in ["trend", "rising", "future", "shift", "new"]):
        return "trend"
    if any(w in lower for w in ["lesson", "mistake", "tip", "practice", "rule"]):
        return "lesson"
    return "trend"


def generate_hashtags(title: str) -> str:
    """Generate relevant hashtags based on topic keywords."""
    hashtag_map = {
        "ai": "#AI", "llm": "#LLM", "gpt": "#GPT", "ml": "#MachineLearning",
        "devops": "#DevOps", "cloud": "#CloudComputing", "kubernetes": "#Kubernetes",
        "docker": "#Docker", "python": "#Python", "rust": "#Rust",
        "typescript": "#TypeScript", "react": "#React", "api": "#API",
        "database": "#Database", "security": "#CyberSecurity",
        "startup": "#Startups", "engineering": "#SoftwareEngineering",
        "agent": "#AIAgents", "automation": "#Automation",
        "infrastructure": "#Infrastructure", "open source": "#OpenSource",
    }
    lower = title.lower()
    tags = ["#TechTrends"]
    for keyword, tag in hashtag_map.items():
        if keyword in lower and tag not in tags:
            tags.append(tag)
    # Always include base tags
    if "#SoftwareEngineering" not in tags:
        tags.append("#SoftwareEngineering")
    return " ".join(tags[:6])


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch trending tech topics for LinkedIn posts")
    parser.add_argument("--count", "-n", type=int, default=3, help="Number of topics to fetch")
    parser.add_argument("--query", "-q", help="Custom search focus")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be added")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument(
        "--source", default="hacker-news",
        choices=["hacker-news", "newsdata", "currents", "all"],
        help="News source (default: hacker-news — free, no key)"
    )
    args = parser.parse_args()

    print(f"[Trend Finder] Fetching {args.count} trending topics...")

    all_topics: list[dict] = []

    if args.source in ("hacker-news", "all"):
        hn = fetch_trending_via_hacker_news(count=args.count * 2)
        all_topics.extend(hn)
        print(f"  Hacker News: {len(hn)} stories")

    if args.source in ("newsdata", "all"):
        query = args.query or "software engineering AI cloud"
        nd = fetch_trending_via_newsdata(query, count=args.count)
        all_topics.extend(nd)
        print(f"  NewsData.io: {len(nd)} articles")

    if args.source in ("currents", "all"):
        query = args.query or "technology AI programming"
        cu = fetch_trending_via_currents(query, count=args.count)
        all_topics.extend(cu)
        print(f"  Currents API: {len(cu)} articles")

    # Deduplicate and take top N
    unique = deduplicate_topics(all_topics)[:args.count]

    if not unique:
        print("[Trend Finder] No topics found. Try --source all or check internet connection.")
        return

    if args.dry_run:
        print(f"\n[DRY RUN] Would add {len(unique)} trending topics:\n")
        for i, t in enumerate(unique, 1):
            ptype = determine_post_type(t["title"])
            tags = generate_hashtags(t["title"])
            print(f"  {i}. [{ptype}] {t['title']}")
            print(f"     Source: {t['source']} | {tags}")
            if t.get("description"):
                print(f"     {t['description'][:120]}")
            print()
        return

    conn = connect()
    added = []
    # Assign to upcoming daily slots
    today = dt.date.today()

    for i, topic in enumerate(unique):
        ptype = determine_post_type(topic["title"])
        tags = generate_hashtags(topic["title"])

        # Schedule for the next available daily slot
        offset = i + 1
        scheduled = today + dt.timedelta(days=offset)
        day_name = scheduled.strftime("%a").lower()

        row_id = add_idea(
            conn,
            title=topic["title"],
            post_type=ptype,
            insight=topic.get("description", ""),
            scheduled_day=day_name,
            scheduled_date=scheduled.isoformat(),
            source=f"trend-finder/{topic['source']}",
            hashtags=tags,
        )
        added.append({"id": row_id, "title": topic["title"], "type": ptype})
        print(f"  Added #{row_id}: {topic['title'][:70]}")

    if args.json:
        print(json.dumps(added, indent=2))
    else:
        s = stats(conn)
        print(f"\nAdded {len(added)} trending topics. Hub now has {s['total']} post(s)")


if __name__ == "__main__":
    main()
