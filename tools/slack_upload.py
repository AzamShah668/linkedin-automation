#!/usr/bin/env python3
"""slack_upload.py — upload a file (tailored CV PDF) into the Slack channel. No external deps.

Puts the actual tailored CV in Slack so it is reachable from the phone, without publishing it anywhere
public (Slack files stay inside the workspace — see decision D12: never publish tailored variants).

Uses Slack's current 3-step external upload flow:
  files.getUploadURLExternal -> POST bytes -> files.completeUploadExternal

Usage:
  py -3 tools/slack_upload.py --file output/pdf/2-Infosys-AI-Application-Engineer.pdf --title "Infosys CV"
  py -3 tools/slack_upload.py --file <pdf> --title "..." --comment "Tailored CV for the Infosys role"
"""
import argparse, json, mimetypes, os, sys, urllib.parse, urllib.request, urllib.error

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_env(path):
    env = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def api(method, token, params=None, data=None, form=True):
    url = f"https://slack.com/api/{method}"
    headers = {"Authorization": f"Bearer {token}"}
    if form:
        body = urllib.parse.urlencode(params or {}).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    else:
        body = json.dumps(data or {}).encode()
        headers["Content-Type"] = "application/json; charset=utf-8"
    req = urllib.request.Request(url, data=body, headers=headers)
    return json.load(urllib.request.urlopen(req, timeout=30))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--title", default="")
    ap.add_argument("--comment", default="")
    args = ap.parse_args()

    path = args.file if os.path.isabs(args.file) else os.path.join(ROOT, args.file)
    if not os.path.exists(path):
        print("ERROR: file not found:", path); sys.exit(1)

    env = load_env(os.path.join(ROOT, ".env"))
    token, channel = env.get("SLACK_BOT_TOKEN"), env.get("SLACK_CHANNEL_ID")
    if not token or not channel:
        print("ERROR: SLACK_BOT_TOKEN / SLACK_CHANNEL_ID missing in .env"); sys.exit(1)

    name = os.path.basename(path)
    size = os.path.getsize(path)
    title = args.title or name

    # 1. reserve an upload URL
    r = api("files.getUploadURLExternal", token, {"filename": name, "length": size})
    if not r.get("ok"):
        print("ERROR getUploadURLExternal:", r.get("error"))
        if r.get("error") == "missing_scope":
            print("  -> the bot token needs the 'files:write' scope; add it in the Slack app config and reinstall.")
        sys.exit(1)
    upload_url, file_id = r["upload_url"], r["file_id"]

    # 2. PUT/POST the bytes to the reserved URL
    ctype = mimetypes.guess_type(name)[0] or "application/octet-stream"
    with open(path, "rb") as fh:
        blob = fh.read()
    req = urllib.request.Request(upload_url, data=blob, headers={"Content-Type": ctype})
    try:
        urllib.request.urlopen(req, timeout=60).read()
    except urllib.error.URLError as e:
        print("ERROR uploading bytes:", e); sys.exit(1)

    # 3. complete + share into the channel
    payload = {"files": [{"id": file_id, "title": title}], "channel_id": channel}
    if args.comment:
        payload["initial_comment"] = args.comment
    r2 = api("files.completeUploadExternal", token, data=payload, form=False)
    if r2.get("ok"):
        print(f"OK: uploaded {name} ({size:,} bytes) to Slack")
    else:
        print("ERROR completeUploadExternal:", r2.get("error")); sys.exit(1)


if __name__ == "__main__":
    main()
