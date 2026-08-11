#!/usr/bin/env python3
"""Local web server for the Job Hunt dashboard.

    py -3 tools/serve_dashboard.py            # http://127.0.0.1:8765
    py -3 tools/serve_dashboard.py --port 9000 --no-browser

Why a local server rather than a published page: an Artifact cannot hand you a
PDF (no `pdf` in its download allowlist, and frame code cannot download
directly). A server can — so this is what makes "press it and get the CV"
actually work, including zipped bundles.

Serves:
  /                        the front-end (web/)
  /api/bootstrap           board + stats + packets + slack + invites + research
  /download/cv/<stem>.pdf  the real tailored CV, as an attachment
  /download/cv/<stem>.html the CV as HTML
  /download/packet/<slug>.zip   one company: CV pdf + all messages + research
  /download/all.zip        every CV and every draft

Binds to 127.0.0.1 only — it reads local files and must never be reachable off
the machine. Stdlib only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import mimetypes
import re
import subprocess
import sys
import threading
import webbrowser
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

# backend/ owns the server and the runner; database/ owns the store. Both are added explicitly
# rather than relying on the process CWD, because this is launched from Task Scheduler and from
# dashboard.cmd, which do not agree on where they start.
_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
for _p in (_HERE, _ROOT / "database"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import pipeline_runner as runner  # noqa: E402
from board_db import (  # noqa: E402
    DB_PATH,
    ALLOWED_STATUS,
    all_rows,
    connect,
    pending_notion,
    set_status,
    stats,
    warm_hinted,
)

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "frontend"
OUT = ROOT / "output"
DASH = OUT / "dashboard"

SLACK_FROM = dt.datetime(2026, 7, 25)  # channel is shared with the YouTube project
PUBLIC_CV = "https://github.com/AzamShah668/AzamShah668/blob/main/Azam-Shah-CV.pdf"

GENERAL_CV_STEM = "azam-shah-devops-cv"


def discover_packets() -> list[dict]:
    """Find packets by scanning disk, so one built five minutes ago shows up.

    Each `output/outreach/<slug>/packet.json` describes its own packet
    (company, role, cv_stem, ats, job_id). This used to be a hardcoded list in this
    file, which meant a newly built packet was invisible until someone edited the
    server — exactly the wrong place for that knowledge to live.
    """
    found = []
    for meta_path in sorted((OUT / "outreach").glob("*/packet.json")):
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        meta.setdefault("slug", meta_path.parent.name)
        if not meta.get("company"):
            continue                       # unusable without a company to match on
        found.append(meta)
    return found

DOC_FILES = {
    "contact": "contact.md",
    "touch1": "touch-1-email.md",
    "touch2": "touch-2-linkedin.md",
    "cover": "cover-letter.md",
}

EMOJI = {
    "dart": "🎯", "bust_in_silhouette": "👤", "memo": "📝", "outbox_tray": "📤",
    "information_source": "ℹ️", "white_check_mark": "✅", "clipboard": "📋",
    "postbox": "📮", "warning": "⚠️", "x": "❌", "star": "⭐", "pushpin": "📌",
    "email": "✉️", "handshake": "🤝", "mag": "🔍", "rocket": "🚀",
}

SAFE_STEM = re.compile(r"^[A-Za-z0-9._-]+$")


def read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def cv_paths(stem: str) -> dict[str, Path]:
    """Tailored CVs live under cv/tailored; the general one sits in cv/."""
    tailored = OUT / "cv" / "tailored"
    base = tailored if (tailored / f"{stem}.html").exists() else OUT / "cv"
    return {
        "html": base / f"{stem}.html",
        "md": base / f"{stem}.md",
        "pdf": OUT / "pdf" / f"{stem}.pdf",
    }


CONTACT_FIELDS = ("name", "title", "linkedin_url", "email", "email_verify", "degree", "confidence")


def parse_contact(text: str | None) -> dict:
    """Pull the headline contact facts out of contact.md.

    contact.md is written for a human and holds several people (primary, backup, warm
    referral). The dashboard only needs the first block's essentials, so this reads
    until the second heading and stops — the full document is still shown on /research.
    """
    if not text:
        return {}
    out: dict[str, str] = {}
    seen_first_person = False
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("## "):
            if seen_first_person:
                break            # into the backup/warm sections; stop
            continue
        m = re.match(r"^-\s*([a-z_]+):\s*(.+)$", line)
        if not m:
            continue
        key, value = m.group(1), m.group(2).strip()
        if key in CONTACT_FIELDS and key not in out:
            out[key] = value
            if key == "name":
                seen_first_person = True
    return out


def build_packets() -> list[dict]:
    out = []
    for p in discover_packets():
        d = OUT / "outreach" / p["slug"]
        stem = p.get("cv_stem") or ""
        paths = cv_paths(stem)
        pdf = paths["pdf"] if stem else Path("nonexistent")
        entry = dict(p)
        entry["docs"] = {k: read(d / f) for k, f in DOC_FILES.items()}
        entry["contact"] = parse_contact(entry["docs"].get("contact"))
        entry["cv"] = {
            "stem": stem,
            "html": read(paths["html"]),
            "has_pdf": pdf.exists(),
            "pdf_kb": round(pdf.stat().st_size / 1024) if pdf.exists() else None,
            # Absolute, OS-native: this gets pasted straight into a file-upload
            # dialog, where a repo-relative path is useless.
            "pdf_path": str(pdf.resolve()) if pdf.exists() else None,
            "pdf_dir": str(pdf.parent.resolve()) if stem else None,
        }
        out.append(entry)
    return out


def slack_feed() -> list[dict]:
    raw = read(DASH / "slack-export.json")
    if not raw:
        return []
    msgs = []
    for m in json.loads(raw).get("messages", []):
        try:
            when = dt.datetime.fromtimestamp(float(m["ts"]))
        except (KeyError, TypeError, ValueError):
            continue
        if when < SLACK_FROM:
            continue
        msgs.append({
            "iso": when.isoformat(),
            "text": m.get("text") or "\n".join(m.get("blocks_text") or []),
            "reactions": m.get("reactions") or [],
            "files": m.get("files") or [],
        })
    msgs.sort(key=lambda x: x["iso"], reverse=True)
    return msgs


def _age(path: Path, label: str, stale_after_h: float) -> dict:
    """When a source was last written, and whether that is too long ago.

    Freshness is reported per source rather than for the page as a whole, because these four
    update on completely different clocks: the board changes when discovery runs, the ledger only
    when something is actually sent, and the triage cache only when someone re-probes LinkedIn.
    A single page-level "updated 3s ago" would be true about the FETCH and a lie about the DATA —
    which is the failure this project keeps rediscovering under different names (D23, D29, D35).
    """
    if not path.exists():
        return {"label": label, "updated": None, "ageH": None, "stale": True,
                "why": "never written"}
    ts = dt.datetime.fromtimestamp(path.stat().st_mtime)
    age_h = (dt.datetime.now() - ts).total_seconds() / 3600
    return {"label": label, "updated": ts.isoformat(timespec="seconds"),
            "ageH": round(age_h, 2), "stale": age_h > stale_after_h,
            "why": f"older than {stale_after_h:g}h" if age_h > stale_after_h else ""}


def console() -> dict:
    """Everything the /console page shows, assembled from the pipeline's own records.

    Reads four independent sources on purpose:
      * the board mirror        — what jobs exist
      * the triage cache        — which of them can actually be one-click applied to
      * the apply ledger        — what was genuinely sent (never a board status: D23/D29)
      * the coverage report     — which of those reached a named human (D32/D41)

    Anything missing degrades to an empty list rather than a crash, and says so in `warnings`,
    because a page that renders zeros looks identical to a page whose data source vanished.
    """
    warnings: list[str] = []

    def _load(label, fn, default):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - a broken source must not blank the whole page
            warnings.append(f"{label}: {type(exc).__name__}: {exc}")
            return default

    conn = connect()
    rows = _load("board", lambda: all_rows(conn), [])
    conn.close()

    triage = _load("triage", lambda: json.loads(
        (ROOT / "output" / "apply-log" / "triage.json").read_text(encoding="utf-8"))["rows"], {})
    applied = _load("ledger", lambda: _ledger_rows(), [])
    gaps = _load("coverage", lambda: _coverage_gaps(), [])
    invites = _load("invites", lambda: json.loads(
        (OUT / "outreach" / "pending-invites.json").read_text(encoding="utf-8"))["invites"], [])

    def of_kind(kind):
        out = [v for v in triage.values() if v.get("kind") == kind]
        return sorted(out, key=lambda r: -(r.get("fit") or 0))

    by_day: dict[str, int] = {}
    for r in applied:
        d = r.get("submitted_at")
        if d:
            by_day[d] = by_day.get(d, 0) + 1
    today = dt.date.today()
    series = [{"d": (today - dt.timedelta(days=i)).isoformat()} for i in range(29, -1, -1)]
    for pt in series:
        pt["n"] = by_day.get(pt["d"], 0)

    companies = {r.get("company", "").lower() for r in applied if r.get("company")}
    easy, ext, dead = of_kind("easy-apply"), of_kind("external"), of_kind("dead")

    return {
        "generated": today.isoformat(),
        "fetched": dt.datetime.now().isoformat(timespec="seconds"),
        "warnings": warnings,
        # Each source carries its own age. The refresh action that fixes a stale one is named
        # here so the page can offer the button instead of just complaining.
        "sources": [
            dict(_age(DB_PATH, "Job board", 48), action="sync-board"),
            dict(_age(ROOT / "output" / "apply-log" / "triage.json",
                      "Easy Apply / external split", 24), action="triage"),
            dict(_age(ROOT / "output" / "apply-log" / "submitted.jsonl",
                      "Applications sent", 24 * 30), action=None),
            dict(_age(OUT / "outreach" / "pending-invites.json",
                      "Connection invites", 24 * 7), action="watch-accepts"),
        ],
        "headline": {
            "board": len(rows), "applications": len(applied), "companies": len(companies),
            "replies": sum(1 for r in rows if r.get("reply")),
            "reachedHuman": max(0, len(companies) - len(gaps)), "noHuman": len(gaps),
            "easyApply": len(easy), "external": len(ext), "dead": len(dead),
            "invitesPending": sum(1 for i in invites if i.get("status") == "pending"),
            "invitesAccepted": sum(1 for i in invites if i.get("status") == "followed_up"),
        },
        "series30": series,
        # The whole board, so the console can host the filterable table the old index page had.
        "board": rows,
        "statuses": sorted({(r.get("status") or "?") for r in rows}),
        "channels": _tally(applied, "channel"),
        "easyApplyJobs": easy, "externalJobs": ext, "deadJobs": dead,
        "applied": sorted(applied, key=lambda r: r.get("submitted_at", ""), reverse=True),
        "gaps": gaps, "invites": invites,
    }


def _tally(rows: list[dict], key: str) -> list[dict]:
    counts: dict[str, int] = {}
    for r in rows:
        counts[r.get(key) or "?"] = counts.get(r.get(key) or "?", 0) + 1
    return [{"k": k, "n": n} for k, n in sorted(counts.items(), key=lambda kv: -kv[1])]


def _ledger_rows() -> list[dict]:
    sys.path.insert(0, str(ROOT))
    from apps.autopilot import ledger
    return ledger.load()


def _coverage_gaps() -> list[str]:
    sys.path.insert(0, str(ROOT))
    from apps.autopilot import coverage
    return [g.company for g in coverage.gaps()]


def bootstrap() -> dict:
    conn = connect()
    rows = all_rows(conn)
    for r in rows:
        r["warm_hinted"] = warm_hinted(r)
    st = stats(conn)
    conn.close()

    invites = read(OUT / "outreach" / "pending-invites.json")
    general = cv_paths(GENERAL_CV_STEM)
    return {
        "served": dt.datetime.now().isoformat(timespec="seconds"),
        "board": rows,
        "stats": st,
        "statuses": list(ALLOWED_STATUS),
        "packets": build_packets(),
        # "slack" and "research" removed with their pages (2026-08-11) — they were computed on
        # every bootstrap and nothing reads them now.

        "invites": json.loads(invites).get("invites", []) if invites else [],
        "generalCv": {
            "stem": GENERAL_CV_STEM,
            "has_pdf": general["pdf"].exists(),
            "url": PUBLIC_CV,
        },
        "emoji": EMOJI,
    }


def zip_bytes(entries: list[tuple[str, bytes]]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in entries:
            z.writestr(name, data)
    return buf.getvalue()


def packet_zip(slug: str) -> bytes | None:
    p = next((x for x in discover_packets() if x["slug"] == slug), None)
    if not p:
        return None
    entries: list[tuple[str, bytes]] = []
    stem = p.get("cv_stem") or ""          # a packet can exist before its CV does
    if stem:
        pdf = cv_paths(stem)["pdf"]
        if pdf.exists():
            entries.append((f"CV/{pdf.name}", pdf.read_bytes()))
        html = cv_paths(stem)["html"]
        if html.exists():
            entries.append((f"CV/{html.name}", html.read_bytes()))
    for key, fname in DOC_FILES.items():
        f = OUT / "outreach" / slug / fname
        if f.exists():
            entries.append((f"messages/{fname}", f.read_bytes()))
    reel = OUT / "outreach" / "highlight-reel.md"
    if reel.exists():
        entries.append(("highlight-reel.md", reel.read_bytes()))
    return zip_bytes(entries) if entries else None


def all_zip() -> bytes:
    entries: list[tuple[str, bytes]] = []
    for pdf in sorted((OUT / "pdf").glob("*.pdf")):
        entries.append((f"CVs-pdf/{pdf.name}", pdf.read_bytes()))
    for html in sorted((OUT / "cv" / "tailored").glob("*.html")):
        entries.append((f"CVs-tailored-html/{html.name}", html.read_bytes()))
    for md in sorted((OUT / "outreach").rglob("*.md")):
        entries.append((f"outreach/{md.relative_to(OUT / 'outreach')}".replace("\\", "/"), md.read_bytes()))
    lp = OUT / "linkedin" / "profile-optimization.md"
    if lp.exists():
        entries.append(("linkedin-profile-optimization.md", lp.read_bytes()))
    return zip_bytes(entries)


class Handler(BaseHTTPRequestHandler):
    server_version = "JobHuntDashboard/1.0"

    def log_message(self, fmt, *args):  # quieter, one line per request
        sys.stderr.write("  %s\n" % (fmt % args))

    # ---------- helpers ----------
    def _send(self, code: int, body: bytes, ctype: str, extra: dict | None = None) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, obj, code: int = 200) -> None:
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"),
                   "application/json; charset=utf-8")

    def _fail(self, code: int, msg: str) -> None:
        self._json({"error": msg}, code)

    def _attachment(self, path: Path, download_name: str | None = None) -> None:
        if not path.exists() or not path.is_file():
            return self._fail(404, f"missing file: {path.name}")
        ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        name = download_name or path.name
        self._send(200, path.read_bytes(), ctype,
                   {"Content-Disposition": f'attachment; filename="{name}"'})

    # ---------- routing ----------
    # Each subject is a real page with its own URL, not a tab.
    PAGES = {
        # Console IS the home page (2026-08-11). The old index/board, research and slack pages
        # were removed: research and slack were reading files 5-17 days stale, and the board's
        # useful half (the live table) moved onto the console.
        "/": "console.html", "/console": "console.html", "/index.html": "console.html",
        "/jobs": "jobs.html",
        "/downloads": "downloads.html",
        "/controls": "controls.html",
    }

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        route = unquote(urlparse(self.path).path).rstrip("/") or "/"

        if route in self.PAGES:
            return self._static(WEB / self.PAGES[route])
        if route.startswith("/static/"):
            return self._static(WEB / "static" / route[len("/static/"):])
        if route == "/api/bootstrap":
            return self._json(bootstrap())
        if route == "/api/console":
            return self._json(console())
        if route == "/api/actions":
            return self._json(runner.catalogue())
        if route == "/api/preflight":
            return self._json(runner.preflight())
        if route == "/api/runs":
            return self._json(runner.recent())
        if route.startswith("/api/run/"):
            rid = route[len("/api/run/"):]
            run = runner.get(rid)
            return self._json(run) if run else self._fail(404, "no such run")
        if route.startswith("/download/"):
            return self._download(route[len("/download/"):])
        return self._fail(404, "no such route")

    def do_POST(self):
        route = unquote(urlparse(self.path).path).rstrip("/") or "/"
        try:
            length = int(self.headers.get("Content-Length") or 0)
            payload = json.loads(self.rfile.read(length) or b"{}") if length else {}
        except (ValueError, json.JSONDecodeError):
            return self._fail(400, "body must be JSON")

        if route == "/api/run":
            key = payload.get("action")
            param = payload.get("param")
            run, err = runner.start(key, confirm=bool(payload.get("confirm")),
                                    param=str(param) if param else None)
            if err:
                return self._fail(409, err)
            return self._json(run)

        # Mark a role as applied / delivered / rejected from the dashboard. This is
        # the path for "I applied by hand and the board still says packet ready".
        if route.startswith("/api/job/") and route.endswith("/status"):
            job_id = route[len("/api/job/"):-len("/status")]
            status = payload.get("status")
            conn = connect()
            try:
                row = set_status(conn, job_id, status, payload.get("note"))
            except ValueError as exc:
                conn.close()
                return self._fail(400, str(exc))
            if row is None:
                conn.close()
                return self._fail(404, "no such role on the board")
            pending = len(pending_notion(conn))
            conn.close()
            return self._json({"job": row, "pending_notion": pending})

        # One-click reconciliation: local mirror -> Notion -> local capture.
        if route == "/api/notion/push":
            proc = subprocess.run(
                [sys.executable or "py", "tools/notion_push.py", "--json"],
                cwd=str(ROOT), capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=120,
            )
            try:
                return self._json(json.loads(proc.stdout or "{}"))
            except json.JSONDecodeError:
                return self._fail(500, (proc.stderr or proc.stdout or "push failed").strip()[:400])

        if route.startswith("/api/run/") and route.endswith("/stop"):
            rid = route[len("/api/run/"):-len("/stop")]
            return self._json({"stopped": runner.stop(rid)})

        return self._fail(404, "no such route")

    def _static(self, path: Path) -> None:
        try:
            path = path.resolve()
            path.relative_to(WEB.resolve())          # containment check
        except (ValueError, OSError):
            return self._fail(403, "outside web root")
        if not path.exists() or not path.is_file():
            return self._fail(404, "not found")
        ctype = mimetypes.guess_type(path.name)[0] or "text/plain"
        if ctype.startswith("text/") or ctype == "application/javascript":
            ctype += "; charset=utf-8"
        self._send(200, path.read_bytes(), ctype)

    def _download(self, rest: str) -> None:
        if rest == "all.zip":
            return self._send(200, all_zip(), "application/zip",
                              {"Content-Disposition": 'attachment; filename="job-hunt-everything.zip"'})

        if rest.startswith("packet/") and rest.endswith(".zip"):
            slug = rest[len("packet/"):-len(".zip")]
            if not SAFE_STEM.match(slug):
                return self._fail(400, "bad slug")
            data = packet_zip(slug)
            if data is None:
                return self._fail(404, "no packet for that company")
            return self._send(200, data, "application/zip",
                              {"Content-Disposition": f'attachment; filename="{slug}-packet.zip"'})

        if rest.startswith("cv/"):
            name = rest[len("cv/"):]
            stem, _, ext = name.rpartition(".")
            if not SAFE_STEM.match(stem) or ext not in ("pdf", "html", "md"):
                return self._fail(400, "bad cv request")
            known = {p.get("cv_stem") for p in discover_packets()} | {GENERAL_CV_STEM}
            if stem not in known:
                return self._fail(404, "unknown cv")
            path = cv_paths(stem)[ext]
            pretty = f"Azam-Shah-CV-{stem}.{ext}" if ext != "pdf" else f"Azam-Shah-CV-{stem}.pdf"
            return self._attachment(path, pretty)

        return self._fail(404, "no such download")


def main() -> None:
    ap = argparse.ArgumentParser(description="Local Job Hunt dashboard server")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args()

    # Guard on the actual home page. This checked index.html, which was deleted when the console
    # became home — a startup abort with a message naming a file nobody had touched.
    if not (WEB / "console.html").exists():
        sys.exit(f"front-end missing: {WEB / 'console.html'}")

    url = f"http://127.0.0.1:{args.port}/"
    srv = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    conn = connect()
    s = stats(conn)
    conn.close()

    print(f"Job Hunt dashboard -> {url}")
    print(f"  board: {s['total']} roles · {s['companies']} companies · {s['warm']} warm")
    print(f"  packets: {len(discover_packets())} · downloads: /download/all.zip")
    print("  local only (127.0.0.1). Ctrl+C to stop.\n")

    if not args.no_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
        srv.server_close()


if __name__ == "__main__":
    main()
