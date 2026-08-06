#!/usr/bin/env python3
"""slack_action_card.py — push a SHORT decision card to Slack per job. No external deps.

Reads a target's packet in output/outreach/<slug>/ and posts: the role + fit score, who gets contacted, and
the exact message the robot will send, in a code block. Nothing else.

Deliberately minimal (owner's call, 2026-07-26: "it should be short and small, you are just sending too much
detail, it is making me confused" — then, same day: "I just need to know what the robot sends, only that part
should be there inside a box"). So the message block stays; it is the whole point of the card, the thing being
approved. Everything around it goes. Dropped: the email draft summary, the backup recruiter, the standalone CV
link (it is inside the message already), the do-it-yourself checklist, the daily-cap note, and the explanation
of what a ✅ does. If tempted to add a field, ask: does it change the ✅/❌ call? If not, leave it out.

**The box shows the 2b message, not 2a.** Stage 1 sends a BARE connection request with nothing attached
(05-decisions D12); 2a is never delivered. Previewing 2a would tell the owner he approved something the robot
will not send. Slots ({A / B} and alternative [To <Name>:] paragraphs) are resolved to this one recipient.

Usage:
  py -3 tools/slack_action_card.py --company infosys
  py -3 tools/slack_action_card.py --all
  py -3 tools/slack_action_card.py --company goodspace --dry-run
"""
import argparse, glob, json, os, re, sys, urllib.request, urllib.error

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTREACH = os.path.join(ROOT, "output", "outreach")
# Single general CV linked in every outreach email (decision D12). Tailored variants stay private.
CV_LINK = "https://github.com/AzamShah668/AzamShah668/blob/main/Azam-Shah-CV.pdf"


def load_env(path):
    env = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def read(path):
    return open(path, encoding="utf-8").read() if os.path.exists(path) else ""


def first(pattern, text, default=""):
    m = re.search(pattern, text, re.MULTILINE)
    return m.group(1).strip() if m else default


def all_of(pattern, text):
    return [m.strip() for m in re.findall(pattern, text, re.MULTILINE)]


def first_blockquote(text):
    """Return the first contiguous block of '> ' lines, cleaned, as one string."""
    block, capturing = [], False
    for line in text.splitlines():
        if line.lstrip().startswith(">"):
            block.append(re.sub(r"^\s*>\s?", "", line))
            capturing = True
        elif capturing:
            if line.strip() == "":
                block.append("")           # allow a blank line inside the quote
                if block[-2:] == ["", ""]:
                    break
            else:
                break
    return "\n".join(block).strip()


def section_quote(text, heading_re):
    """The blockquote directly under the first heading matching heading_re."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if re.match(heading_re, line):
            return first_blockquote("\n".join(lines[i + 1:]))
    return ""


def resolve_slots(msg, first_name):
    """Fill the drafting slots so the preview reads exactly as the recipient will see it.

    Templates carry '{Recruiter-A / Pawan}' and alternative '[To <Name>:] ...' paragraphs. Keep only this
    recipient's variant — a preview showing both branches is worse than no preview.
    """
    msg = re.sub(r"\{[^}]*\}", first_name, msg)
    kept, skipping = [], False
    for line in msg.splitlines():
        marker = re.match(r"\s*\[To\s+([A-Za-z]+)[^\]]*\]\s*(.*)", line)
        if marker:
            skipping = marker.group(1).lower() != first_name.lower()
            if skipping:
                continue
            line = marker.group(2)
        elif skipping:
            if line.strip() == "":       # blank line ends the other person's paragraph
                skipping = False
            continue
        kept.append(line)
    return "\n".join(kept).strip()


def build_card(slug):
    """Role, score, recipient, the exact message the robot will send, marker. Nothing else."""
    d = os.path.join(OUTREACH, slug)
    contact = read(os.path.join(d, "contact.md"))
    t2 = read(os.path.join(d, "touch-2-linkedin.md"))
    if not contact:
        return None

    header = first(r"^#\s*Contact\s*[—-]\s*(.+)$", contact, slug)   # "Infosys · AI Application Engineer"
    score = first(r"\bfit\s+(\d{1,3})\b", contact)
    names = all_of(r"^- name:\s*(.+)$", contact)
    urls = all_of(r"^- linkedin_url:\s*(\S+)", contact)

    # Lead with whoever the drafted note addresses ("Hi <Name>"), so the card never names one person while
    # the robot contacts another (warm insider vs cold recruiter).
    recipient = first(r"\bHi\s+([A-Z][a-z]+)", first_blockquote(t2))
    pairs = [(names[i], urls[i] if i < len(urls) else "") for i in range(len(names))]
    lead = [p for p in pairs if p[0].split() and p[0].split()[0].lower() == recipient.lower()]
    ordered = lead + [p for p in pairs if p not in lead]
    warm = "⭐" in contact and bool(lead)

    # Show the 2b message — the one actually delivered. The 2a note is NEVER sent: stage 1 is a bare
    # connection request with nothing attached (05-decisions D12). Previewing 2a would be a lie.
    msg = resolve_slots(section_quote(t2, r"^##\s*2b\b"), recipient or "there")

    title = f"*🎯 {header}*" + (f"  ·  fit {score}" if score else "")
    lines = [title]
    if ordered:
        name, link = ordered[0]
        lines.append(f"👤 *{name}*" + (" ⭐ warm" if warm else "") + (f" — {link}" if link else ""))
    apply_url = first(r"^- apply_url:\s*(\S+)", contact)
    if apply_url:
        lines.append(f"📮 apply: {apply_url}")
    lines.append("_connect request now (no note) · this sends once they accept:_")
    lines.append("```" + (msg or "(2b message missing — check touch-2-linkedin.md)") + "```")
    lines.append("✅ send   ❌ skip")
    lines.append(f"`ref:{slug}`")   # machine-readable marker mapping a reaction back to the job
    return "\n".join(lines)


def post(text, dry):
    env = load_env(os.path.join(ROOT, ".env"))
    token, channel = env.get("SLACK_BOT_TOKEN"), env.get("SLACK_CHANNEL_ID")
    if dry or not token or not channel:
        print(("DRY-RUN / no creds — card preview:\n" if dry else "ERROR: Slack creds missing; preview:\n") + text)
        return dry
    req = urllib.request.Request(
        "https://slack.com/api/chat.postMessage",
        data=json.dumps({"channel": channel, "text": text, "mrkdwn": True, "unfurl_links": False}).encode("utf-8"),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"})
    try:
        resp = json.load(urllib.request.urlopen(req, timeout=15))
    except urllib.error.URLError as e:
        print("ERROR posting:", e); return False
    if resp.get("ok"):
        print(f"OK: posted card (ts={resp.get('ts')})"); return True
    print("Slack API error:", resp.get("error")); return False


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--company", help="folder slug under output/outreach/")
    g.add_argument("--all", action="store_true", help="post a card for every packet")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    slugs = ([os.path.basename(os.path.dirname(p)) for p in glob.glob(os.path.join(OUTREACH, "*", "contact.md"))]
             if args.all else [args.company])
    for slug in slugs:
        card = build_card(slug)
        if not card:
            print(f"skip {slug}: no contact.md"); continue
        post(card, args.dry_run)


if __name__ == "__main__":
    main()
