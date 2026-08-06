#!/usr/bin/env python3
"""ats_audit.py — ATS keyword-gap auditor (advanced-ideas 2.2). No external deps.

Parses a CV (HTML / Markdown / text) and reports how well it matches a job's keywords, so you clear the
85%+ ATS bar before applying. Two modes:
  --keywords "kubernetes, ci/cd, terraform, ..."   (curated skill list — most reliable)
  --jd path/to/jd.txt                               (auto-extract candidate keywords from a JD)

Usage:
  py -3 tools/ats_audit.py --cv output/cv/tailored/1-Innova-ESI-DevOps-Engineer.html --keywords "docker,kubernetes,jenkins,ansible,terraform,ci/cd,linux,python,helm,prometheus"
  py -3 tools/ats_audit.py --cv output/cv/azam-shah-devops-cv.md --jd jd.txt
"""
import argparse, os, re, sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

STOPWORDS = set("""a an the and or of to in for with on at by from as is are be we you your our their they it
this that will can role team work working experience years strong good ability skills knowledge etc using use
job about who what which help build built including plus per across into out over more most other via""".split())


def read_text(path):
    raw = open(path, encoding="utf-8", errors="ignore").read()
    if path.lower().endswith((".html", ".htm")):
        raw = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", raw)
        raw = re.sub(r"(?s)<[^>]+>", " ", raw)          # strip tags
        raw = re.sub(r"&[a-z]+;", " ", raw)             # strip entities
    return re.sub(r"\s+", " ", raw).lower()


def norm(term):
    return re.sub(r"\s+", " ", term.strip().lower())


def present(term, cv):
    """Keyword is present if it appears as a token/phrase in the CV text."""
    t = re.escape(norm(term))
    # allow word-ish boundaries; tech terms like c++/ci/cd/node.js handled by escaping
    return re.search(rf"(?<![a-z0-9]){t}(?![a-z0-9])", cv) is not None


def keywords_from_jd(jd_text, top=25):
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9+#./-]{2,}", jd_text.lower())
    freq = {}
    for w in words:
        if w in STOPWORDS or len(w) < 3:
            continue
        freq[w] = freq.get(w, 0) + 1
    return [w for w, _ in sorted(freq.items(), key=lambda x: -x[1])[:top]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cv", required=True, help="CV file (html/md/txt)")
    ap.add_argument("--keywords", help="comma-separated keywords, or a file path")
    ap.add_argument("--jd", help="job-description file to auto-extract keywords from")
    ap.add_argument("--target", type=float, default=85.0, help="target match %% (default 85)")
    args = ap.parse_args()

    if not os.path.exists(args.cv):
        print("ERROR: CV not found:", args.cv); sys.exit(1)
    cv = read_text(args.cv)

    kws = []
    if args.keywords:
        src = open(args.keywords, encoding="utf-8").read() if os.path.exists(args.keywords) else args.keywords
        kws = [norm(k) for k in re.split(r"[,\n]", src) if k.strip()]
    elif args.jd and os.path.exists(args.jd):
        kws = keywords_from_jd(open(args.jd, encoding="utf-8", errors="ignore").read())
    else:
        print("ERROR: provide --keywords or --jd"); sys.exit(1)

    kws = list(dict.fromkeys(kws))  # dedupe, keep order
    hit = [k for k in kws if present(k, cv)]
    miss = [k for k in kws if k not in hit]
    pct = (len(hit) / len(kws) * 100) if kws else 0.0

    print(f"ATS keyword audit — {os.path.basename(args.cv)}")
    print(f"Match: {pct:.0f}%  ({len(hit)}/{len(kws)} keywords)   target {args.target:.0f}%  "
          f"→ {'PASS ✅' if pct >= args.target else 'BELOW TARGET ⚠'}")
    if miss:
        print(f"\nMissing ({len(miss)}): {', '.join(miss)}")
        print("→ Weave the *true* ones into a bullet or the skills line (never fabricate a skill you lack).")
    if hit:
        print(f"\nPresent ({len(hit)}): {', '.join(hit)}")


if __name__ == "__main__":
    main()
