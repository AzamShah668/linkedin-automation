#!/usr/bin/env bash
# html-to-pdf.sh — convert HTML CV/cover-letter files to print-ready PDF via headless Chrome/Edge.
# Part of the Job Hunt Autopilot content layer (completion plan step 1). No external installs.
#
# Usage:
#   tools/html-to-pdf.sh <file.html> [more.html ...]   # convert specific files
#   tools/html-to-pdf.sh --all                         # convert every HTML in output/cv/ (+ tailored/)
# Output: <name>.pdf written to output/pdf/.
set -euo pipefail

ROOT="d:/linkdin automation"
OUTDIR="$ROOT/output/pdf"
mkdir -p "$OUTDIR"

# Pick an available Chromium engine (Chrome preferred, Edge fallback).
BROWSER=""
for p in \
  "/c/Program Files/Google/Chrome/Application/chrome.exe" \
  "/c/Program Files (x86)/Google/Chrome/Application/chrome.exe" \
  "/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" \
  "/c/Program Files/Microsoft/Edge/Application/msedge.exe" ; do
  [ -f "$p" ] && { BROWSER="$p"; break; }
done
[ -n "$BROWSER" ] || { echo "ERROR: no Chrome/Edge found for PDF export"; exit 1; }

convert() {
  local in="$1"
  [ -f "$in" ] || { echo "SKIP (not found): $in"; return; }
  local base; base="$(basename "$in" .html)"
  local out="$OUTDIR/$base.pdf"
  # ABSOLUTE, forward-slash path (cygpath -m -a) → valid file URL even when given a relative arg.
  # (Relative paths produce file:///output\... which Chrome renders blank.) Percent-encode spaces.
  local abs; abs="$(cygpath -m -a "$in")"
  local url="file:///${abs// /%20}"
  # Isolated temp profile + full-render flags so pages don't print blank on a race.
  local udd; udd="$(mktemp -d)"
  "$BROWSER" --headless=new --disable-gpu --no-pdf-header-footer \
    --user-data-dir="$(cygpath -w "$udd")" --virtual-time-budget=10000 \
    --run-all-compositor-stages-before-draw \
    --print-to-pdf="$(cygpath -w "$out")" "$url" >/dev/null 2>&1 || true
  sleep 1
  rm -rf "$udd" 2>/dev/null || true
  if [ -s "$out" ]; then echo "OK  → output/pdf/$base.pdf ($(wc -c < "$out") bytes)"; else echo "FAIL: $in"; fi
}

if [ "${1:-}" = "--all" ]; then
  shopt -s nullglob
  for f in "$ROOT"/output/cv/*.html "$ROOT"/output/cv/tailored/*.html; do convert "$f"; done
else
  [ "$#" -ge 1 ] || { echo "usage: tools/html-to-pdf.sh <file.html ...> | --all"; exit 1; }
  for f in "$@"; do convert "$f"; done
fi
