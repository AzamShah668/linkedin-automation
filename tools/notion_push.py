#!/usr/bin/env python3
"""Push dashboard status changes into Notion, then clear the queue.

    py -3 tools/notion_push.py            # push everything waiting
    py -3 tools/notion_push.py --json     # machine-readable result
    py -3 tools/notion_push.py --dry-run  # show what would be sent

This is what the "Push to Notion" button on the dashboard calls, so marking a role
applied becomes one click end to end.

**Needs `NOTION_TOKEN` in .env.** Notion is otherwise only reachable through the MCP
connector, which belongs to a Claude session, not to this server. Create an internal
integration at notion.so/my-integrations, share the "Job Hunt — Autopilot" database
with it, and put the secret in .env as NOTION_TOKEN.

Without the token this still does the useful half: it keeps the local seed in step so
nothing can revert, and reports exactly what a Claude session needs to push. Stdlib
only.
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from board_db import connect, mark_pushed, pending_notion  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "output" / "dashboard" / "board-seed.json"
API = "https://api.notion.com/v1/pages/"
NOTION_VERSION = "2022-06-28"


def load_token() -> str | None:
    env = ROOT / ".env"
    if not env.exists():
        return None
    for raw in env.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("NOTION_TOKEN") and "=" in line:
            return line.partition("=")[2].strip().strip('"').strip("'") or None
    return None


def patch_page(token: str, page_id: str, status: str, applied: str | None) -> tuple[bool, str]:
    """PATCH one page. Status may be a `status` or a `select` property, so try both."""
    for kind in ("status", "select"):
        props: dict = {"Status": {kind: {"name": status}}}
        if applied:
            props["Applied Date"] = {"date": {"start": applied}}
        body = json.dumps({"properties": props}).encode("utf-8")
        req = urllib.request.Request(
            API + page_id, data=body, method="PATCH",
            headers={
                "Authorization": f"Bearer {token}",
                "Notion-Version": NOTION_VERSION,
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30):
                return True, f"updated ({kind})"
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:300]
            if exc.code == 400 and kind == "status":
                continue          # wrong property type, try select
            return False, f"HTTP {exc.code}: {detail}"
        except urllib.error.URLError as exc:
            return False, f"network: {exc.reason}"
    return False, "Status is neither a status nor a select property"


def refresh_seed(changes: list[dict], applied_by_job: dict[str, str | None]) -> int:
    """Keep the local Notion capture in step so a later sync cannot revert a change."""
    if not SEED.exists():
        return 0
    data = json.loads(SEED.read_text(encoding="utf-8"))
    by_id = {c["job_id"]: c for c in changes}
    touched = 0
    for row in data.get("rows", []):
        change = by_id.get(row.get("id"))
        if not change:
            continue
        row["status"] = change["to_status"]
        if applied_by_job.get(row["id"]):
            row["applied"] = applied_by_job[row["id"]]
        touched += 1
    if touched:
        import datetime as dt
        data["captured"] = dt.datetime.now().astimezone().isoformat(timespec="seconds")
        SEED.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    return touched


def main() -> None:
    dry = "--dry-run" in sys.argv
    as_json = "--json" in sys.argv

    conn = connect()
    changes = pending_notion(conn)
    if not changes:
        out = {"pushed": 0, "pending": 0, "notion": "nothing waiting",
               "message": "Notion is already up to date."}
        print(json.dumps(out) if as_json else out["message"])
        return

    applied_by_job = {
        r["id"]: r["applied"]
        for r in conn.execute("SELECT id, applied FROM jobs")
    }
    token = load_token()
    results = []

    if dry:
        for c in changes:
            results.append({"job": c["job"], "company": c["company"],
                            "to": c["to_status"], "page": c["job_id"], "result": "dry-run"})
        out = {"pushed": 0, "pending": len(changes), "notion": "dry-run", "results": results}
        print(json.dumps(out, indent=1) if as_json else
              "\n".join(f'  would set {r["company"]} · {r["job"]} -> {r["to"]}' for r in results))
        return

    pushed_ids: list[int] = []
    if token:
        for c in changes:
            ok, detail = patch_page(token, c["job_id"], c["to_status"],
                                    applied_by_job.get(c["job_id"]))
            results.append({"job": c["job"], "company": c["company"],
                            "to": c["to_status"], "ok": ok, "detail": detail})
            if ok:
                pushed_ids.append(c["id"])

    seeded = refresh_seed([c for c in changes if not token or c["id"] in pushed_ids],
                          applied_by_job)

    if token and pushed_ids:
        mark_pushed(conn, pushed_ids)

    remaining = len(pending_notion(conn))
    if token:
        summary = (f"pushed {len(pushed_ids)} of {len(changes)} change(s) to Notion; "
                   f"{remaining} still waiting")
        notion_state = "pushed" if not remaining else "partial"
    else:
        summary = (f"no NOTION_TOKEN in .env, so Notion was not touched. Kept the local capture in "
                   f"step for {seeded} row(s) — nothing can revert. Ask Claude to push "
                   f"{len(changes)} change(s), or add a token to make this button end to end.")
        notion_state = "needs_token"

    out = {"pushed": len(pushed_ids), "pending": remaining, "seed_rows": seeded,
           "notion": notion_state, "results": results, "message": summary}
    if as_json:
        print(json.dumps(out, indent=1))
    else:
        for r in results:
            flag = "ok " if r.get("ok") else "FAIL"
            print(f'  [{flag}] {r["company"]} · {r["job"]} -> {r["to"]}  {r.get("detail","")}')
        print(summary)


if __name__ == "__main__":
    main()
