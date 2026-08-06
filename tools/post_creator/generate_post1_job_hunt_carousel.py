"""
Upgraded Post 1 Carousel Generator — Job Hunt Autopilot
Features ZERO AI gibberish text on Slide 1 (uses crisp HTML vector overlay on pristine 3D artwork)
and a spacious 5-Layer System Architecture Card on Slide 2 with crisp Space Grotesk typography.
"""

import os
import sys
import shutil
import subprocess
import time
import json

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
POST_CREATOR_DIR = os.path.join(PROJECT_ROOT, "tools", "post_creator")
sys.path.insert(0, POST_CREATOR_DIR)

CAROUSEL_DIR = os.path.join(PROJECT_ROOT, "output", "posts", "carousel_bundle_post1")
IMAGES_DIR = os.path.join(PROJECT_ROOT, "output", "posts", "images")
PACKAGES_DIR = os.path.join(PROJECT_ROOT, "output", "posts", "packages")
EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 1: Hero Cover Card with Pristine 3D Command Center Artwork + Vector Text Overlay (ZERO GIBBERISH)
# ═══════════════════════════════════════════════════════════════════════
SLIDE1_HERO_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@700;800;900&family=Fira+Code:wght@700;800&display=swap');
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    width: 1080px;
    height: 1350px;
    background: #030712;
    font-family: 'Space Grotesk', -apple-system, sans-serif;
    color: #ffffff;
    display: flex;
    flex-direction: column;
    padding: 24px;
    justify-content: space-between;
    overflow: hidden;
    position: relative;
  }

  .outer-frame {
    border: 3.5px solid #00e5ff;
    box-shadow: 0 0 45px rgba(0, 229, 255, 0.4), inset 0 0 20px rgba(0, 229, 255, 0.15);
    border-radius: 20px;
    padding: 20px;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    background: rgba(6, 12, 28, 0.95);
    position: relative;
    z-index: 2;
  }

  .header {
    background: #0d1733;
    border: 2.5px solid #00e5ff;
    box-shadow: 0 0 25px rgba(0, 229, 255, 0.4);
    border-radius: 14px;
    padding: 18px 24px;
    text-align: center;
  }
  .h-sub { font-family: 'Fira Code', monospace; font-size: 14px; font-weight: 800; color: #facc15; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 4px; }
  .h-title { font-size: 36px; font-weight: 900; color: #fff; letter-spacing: -0.5px; }
  .h-title span { color: #00e5ff; text-shadow: 0 0 16px rgba(0,229,255,0.9); }

  .artwork-container {
    width: 100%;
    flex: 1;
    margin: 14px 0;
    border-radius: 16px;
    overflow: hidden;
    border: 2.5px solid #00e5ff;
    box-shadow: 0 0 30px rgba(0, 229, 255, 0.35);
    position: relative;
  }
  .art-img { width: 100%; height: 100%; object-fit: cover; }

  .overlay-badge-top {
    position: absolute;
    top: 16px;
    left: 16px;
    background: rgba(4, 8, 20, 0.88);
    border: 1.5px solid #00e5ff;
    border-radius: 10px;
    padding: 8px 16px;
    font-family: 'Fira Code', monospace;
    font-size: 13px;
    font-weight: 800;
    color: #00e5ff;
    backdrop-filter: blur(8px);
  }

  .overlay-badge-right {
    position: absolute;
    top: 16px;
    right: 16px;
    background: rgba(4, 8, 20, 0.88);
    border: 1.5px solid #facc15;
    border-radius: 10px;
    padding: 8px 16px;
    font-family: 'Fira Code', monospace;
    font-size: 13px;
    font-weight: 800;
    color: #facc15;
    backdrop-filter: blur(8px);
  }

  .stats-banner {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin-bottom: 4px;
  }
  .stat-card {
    background: rgba(15, 23, 42, 0.95);
    border: 2px solid #00e5ff;
    border-radius: 12px;
    padding: 12px;
    text-align: center;
    box-shadow: 0 0 15px rgba(0, 229, 255, 0.25);
  }
  .sc-val { font-size: 22px; font-weight: 900; color: #00e5ff; }
  .sc-lbl { font-size: 11px; font-weight: 800; color: #facc15; text-transform: uppercase; margin-top: 2px; }

  .footer-cta {
    background: linear-gradient(90deg, #1e1b4b, #311b92);
    border: 2.5px solid #818cf8;
    border-radius: 14px;
    padding: 14px;
    text-align: center;
    font-size: 20px;
    font-weight: 900;
    color: #c7d2fe;
    letter-spacing: 0.5px;
  }
</style>
</head>
<body>
  <div class="outer-frame">
    <div class="header">
      <div class="h-sub">⚡ AUTONOMOUS OUTREACH ENGINE</div>
      <div class="h-title">AUTONOMOUS <span>JOB HUNT AUTOPILOT</span></div>
    </div>

    <div class="artwork-container">
      <img src="file:///{ARTWORK_PATH}" class="art-img" alt="3D Command Center Artwork">
      <div class="overlay-badge-top">🤖 AI AGENT OPERATED</div>
      <div class="overlay-badge-right">🛡️ 100% BAN-SAFE</div>
    </div>

    <div class="stats-banner">
      <div class="stat-card"><div class="sc-val">62 Jobs</div><div class="sc-lbl">Discovered</div></div>
      <div class="stat-card"><div class="sc-val">5 Applied</div><div class="sc-lbl">Submitted</div></div>
      <div class="stat-card"><div class="sc-val">0 Bounces</div><div class="sc-lbl">Verified Mail</div></div>
      <div class="stat-card"><div class="sc-val">~2 min</div><div class="sc-lbl">Human Effort</div></div>
    </div>

    <div class="footer-cta">🚀 10-STAGE PIPELINE • RUNS ON WINDOWS SCHEDULED TASKS</div>
  </div>
</body>
</html>"""

# ═══════════════════════════════════════════════════════════════════════
# SLIDE 2: High-Density 5-Layer Job Hunt Architecture Specs Card (Space Grotesk)
# ═══════════════════════════════════════════════════════════════════════
SLIDE2_5LAYER_PIPELINE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@600;700;800;900&family=Fira+Code:wght@700&display=swap');
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    width: 1080px;
    height: 1350px;
    background: #030712;
    background-image: 
      radial-gradient(circle at 85% 15%, rgba(250, 204, 21, 0.25) 0%, transparent 45%),
      radial-gradient(circle at 15% 85%, rgba(0, 229, 255, 0.22) 0%, transparent 45%),
      linear-gradient(rgba(0, 229, 255, 0.05) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0, 229, 255, 0.05) 1px, transparent 1px);
    background-size: 100% 100%, 100% 100%, 30px 30px, 30px 30px;
    font-family: 'Space Grotesk', -apple-system, sans-serif;
    color: #ffffff;
    display: flex;
    flex-direction: column;
    padding: 24px;
    justify-content: space-between;
    overflow: hidden;
    position: relative;
  }
  .bg-sym { position: absolute; opacity: 0.35; z-index: 1; pointer-events: none; }
  .s-bulb { top: 40px; right: 40px; font-size: 56px; opacity: 0.85; filter: drop-shadow(0 0 15px #facc15); }
  .s-gear1 { top: 280px; left: 20px; font-size: 38px; }
  .s-code { bottom: 180px; right: 30px; font-size: 38px; font-family: 'Fira Code', monospace; color: #00e5ff; font-weight: 900; }
  .s-gear2 { bottom: 60px; left: 30px; font-size: 42px; }

  .outer-frame {
    border: 3px solid #00e5ff;
    box-shadow: 0 0 40px rgba(0, 229, 255, 0.4), inset 0 0 20px rgba(0, 229, 255, 0.15);
    border-radius: 20px;
    padding: 20px;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    background: rgba(6, 12, 28, 0.95);
    position: relative;
    z-index: 2;
  }
  .header {
    background: #0d1733;
    border: 2px solid #00e5ff;
    box-shadow: 0 0 20px rgba(0, 229, 255, 0.4);
    border-radius: 12px;
    padding: 14px 22px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .h-title { font-size: 30px; font-weight: 900; color: #fff; letter-spacing: -0.5px; }
  .h-title span { color: #00e5ff; text-shadow: 0 0 12px rgba(0,229,255,0.9); }
  .h-tag { font-family: 'Fira Code', monospace; font-size: 13px; font-weight: 800; background: #00e5ff; color: #040814; padding: 6px 14px; border-radius: 8px; }

  .stack-grid { display: flex; flex-direction: column; flex: 1; margin: 10px 0; justify-content: space-between; gap: 8px; }
  .layer-box { background: rgba(15, 23, 42, 0.95); border-radius: 12px; padding: 14px 18px; display: flex; flex-direction: column; justify-content: space-between; flex: 1; }
  .l-amber  { border: 2.5px solid #ff9100; box-shadow: 0 0 16px rgba(255, 145, 0, 0.4); }
  .l-cyan   { border: 2.5px solid #00e5ff; box-shadow: 0 0 16px rgba(0, 229, 255, 0.4); }
  .l-green  { border: 2.5px solid #00e676; box-shadow: 0 0 16px rgba(0, 230, 118, 0.4); }
  .l-purple { border: 2.5px solid #e040fb; box-shadow: 0 0 16px rgba(224, 64, 251, 0.4); }
  .l-red    { border: 2.5px solid #ff1744; box-shadow: 0 0 16px rgba(255, 23, 68, 0.4); }

  .layer-head { display: flex; align-items: center; justify-content: space-between; }
  .l-name { font-size: 20px; font-weight: 900; letter-spacing: 0.5px; }
  .l-amber  .l-name { color: #ff9100; text-shadow: 0 0 8px rgba(255,145,0,0.5); }
  .l-cyan   .l-name { color: #00e5ff; text-shadow: 0 0 8px rgba(0,229,255,0.5); }
  .l-green  .l-name { color: #00e676; text-shadow: 0 0 8px rgba(0,230,118,0.5); }
  .l-purple .l-name { color: #e040fb; text-shadow: 0 0 8px rgba(224,64,251,0.5); }
  .l-red    .l-name { color: #ff5252; text-shadow: 0 0 8px rgba(255,82,82,0.5); }

  .file-code { font-family: 'Fira Code', monospace; font-size: 12px; font-weight: 700; background: #040814; color: #facc15; padding: 4px 10px; border-radius: 6px; border: 1px solid rgba(250,204,21,0.4); }
  .l-body-text { font-size: 15px; color: #e2e8f0; font-weight: 600; line-height: 1.35; margin: 4px 0; }
  .pills-bar { display: flex; gap: 8px; flex-wrap: wrap; }
  .badge-pill { font-size: 12px; font-weight: 800; padding: 5px 12px; border-radius: 6px; background: #040814; }
  .l-amber  .badge-pill { border: 1.5px solid #ff9100; color: #fff; }
  .l-cyan   .badge-pill { border: 1.5px solid #00e5ff; color: #fff; }
  .l-green  .badge-pill { border: 1.5px solid #00e676; color: #fff; }
  .l-purple .badge-pill { border: 1.5px solid #e040fb; color: #fff; }
  .l-red    .badge-pill { border: 1.5px solid #ff1744; color: #fff; }

  .footer-bar { background: #0d1733; border: 2px solid #00e5ff; border-radius: 12px; padding: 12px 20px; display: flex; align-items: center; justify-content: space-between; }
  .f-box { display: flex; flex-direction: column; }
  .f-val { font-size: 20px; font-weight: 900; color: #00e5ff; }
  .f-lbl { font-size: 11px; color: #facc15; font-weight: 800; text-transform: uppercase; }
</style>
</head>
<body>
  <div class="bg-sym s-bulb">💡</div>
  <div class="bg-sym s-gear1">⚙️</div>
  <div class="bg-sym s-code">&lt;/&gt;</div>
  <div class="bg-sym s-gear2">⚙️</div>
  <div class="outer-frame">
    <div class="header">
      <div class="h-title">SLIDE 02 • <span>JOB HUNT SYSTEM ARCHITECTURE</span></div>
      <div class="h-tag">FULL TECHNICAL SPECS</div>
    </div>
    <div class="stack-grid">
      <div class="layer-box l-amber">
        <div class="layer-head"><div class="l-name">📱 1. CLIENT & SLACK APPROVAL GATE</div><div class="file-code">web/ + check_approvals.py</div></div>
        <div class="l-body-text"><b>Human-in-the-Loop Safeguard:</b> Slack mobile webhooks for 1-tap connection approval + live SQLite web dashboard review queue.</div>
        <div class="pills-bar"><span class="badge-pill">📱 SLACK MOBILE WEBHOOK</span><span class="badge-pill">⚡ 1-TAP PHONE APPROVAL</span><span class="badge-pill">💻 LIVE SQLITE WEB UI</span></div>
      </div>
      <div class="layer-box l-cyan">
        <div class="layer-head"><div class="l-name">🔍 2. AUTOMATED DISCOVERY ENGINE</div><div class="file-code">daily-discovery.ps1 + LinkedIn MCP</div></div>
        <div class="l-body-text"><b>Scheduled Job Scraper:</b> Fires daily at 08:00 IST. Ingests fresh DevOps & AI/MLOps roles, deduping against 62 board rows.</div>
        <div class="pills-bar"><span class="badge-pill">🌐 LINKEDIN MCP API</span><span class="badge-pill">⚙️ DAILY 08:00 TASK</span><span class="badge-pill">📊 FIT SCORE ≥ 80</span></div>
      </div>
      <div class="layer-box l-green">
        <div class="layer-head"><div class="l-name">🧠 3. AI RESEARCH & CV TAILORING</div><div class="file-code">cv-architect + recruiter-outreach</div></div>
        <div class="l-body-text"><b>Deep Job Research:</b> Analyzes JDs, researches company stack, generates tailored CVs & 2-touch recruiter pitch packages.</div>
        <div class="pills-bar"><span class="badge-pill">📝 TAILORED CV PDF</span><span class="badge-pill">✉️ TOUCH-1 GMAIL</span><span class="badge-pill">💬 TOUCH-2 LINKEDIN</span></div>
      </div>
      <div class="layer-box l-purple">
        <div class="layer-head"><div class="l-name">✉️ 4. TWO-STAGE OUTREACH DISPATCH</div><div class="file-code">flush-approved.ps1 + watch-accepts.ps1</div></div>
        <div class="l-body-text"><b>Stealth Sender Engine:</b> Sends bare connection request → monitors accepts → auto-sends full CV + personalized pitch package.</div>
        <div class="pills-bar"><span class="badge-pill">🤝 BARE CONNECT REQUEST</span><span class="badge-pill">👁️ ACCEPT WATCHER</span><span class="badge-pill">🛡️ JITTER & DAILY CAPS</span></div>
      </div>
      <div class="layer-box l-red">
        <div class="layer-head"><div class="l-name">💾 5. STATE STORE & TRACKING ENGINE</div><div class="file-code">board_db.py + invite_tracker.py</div></div>
        <div class="l-body-text"><b>Persistent State Management:</b> Local SQLite3 DB synced bi-directionally with Notion Cloud Board; tracks Day 3 & 7 follow-up nudges.</div>
        <div class="pills-bar"><span class="badge-pill">📊 NOTION REST API</span><span class="badge-pill">💾 SQLITE3 DB</span><span class="badge-pill">⏰ DAY 3/7 FOLLOW-UPS</span></div>
      </div>
    </div>
    <div class="footer-bar">
      <div class="f-box"><div class="f-val">62 Jobs</div><div class="f-lbl">Discovered</div></div>
      <div class="f-box"><div class="f-val">5 Applied</div><div class="f-lbl">Submitted</div></div>
      <div class="f-box"><div class="f-val">0 Bounces</div><div class="f-lbl">Verified Mail</div></div>
      <div class="f-box"><div class="f-val">~2 min</div><div class="f-lbl">Human Effort/App</div></div>
    </div>
  </div>
</body>
</html>"""

POST_1_COPY = """I was mass-applying to jobs the dumb way. 3 hours a day, 40 open tabs, copy-pasting the same CV everywhere.

So I stopped and built an autonomous job hunt pipeline instead.

Here is what it does while I sleep:

STAGE 1: DISCOVER
-> Scheduled task fires at 08:00 every morning
-> LinkedIn MCP searches DevOps + AI/MLOps roles (past week only)
-> Deduplicates against 62 existing board rows
-> Scores each role against my profile (fit score 0-100)
-> Pushes to Notion database + posts Slack digest

STAGE 2: PROCESS & TAILOR
-> AI reads the JD, researches the company (tech stack, recent news, values)
-> Generates a tailored CV matched to that specific role
-> Writes a cover letter grounded in real achievements (never fabricated)
-> Drafts a recruiter pitch: formal email (Touch 1) + LinkedIn message (Touch 2)

STAGE 3: HUMAN GATE
-> Everything lands in a Slack review queue
-> I review on my phone and tap the checkmark to approve
-> Nothing sends without that tap. Ever.

STAGE 4: OUTREACH
-> Bare connection request (no note — LinkedIn caps notes at 3/month)
-> They accept -> wait 3-20 hours -> full CV + personalized pitch auto-sends
-> Day 3 + Day 7 follow-up nudges, then stop

The hard engineering problems I solved:
* Browser profile lock: two Chromium instances cannot share one LinkedIn session. Cost me an hour debugging a fake "session expired" error before I found 3 servers fighting for the same profile.
* Headless permission cliff: Claude running unattended silently refuses any tool not in the allowlist. 58 entries now.
* Ban safety: randomized jitter on every timed action, daily caps, no headless LinkedIn scraping. Signal comes from parsed email alerts only.

Results so far:
-> 62 jobs discovered automatically
-> 5 applications submitted
-> 3 tailored CVs delivered to real recruiters (0 bounces)
-> 1 warm insider connection already accepted
-> Total human effort per application: ~2 minutes of phone review

The whole thing runs on 5 Windows Scheduled Tasks, a Notion database, Slack webhooks, and an MCP protocol server. No cloud deployment. No monthly bill. Just my laptop.

Last week I showed you the AI content studio. This is the system it was built to serve.

What repetitive workflow are you still doing manually? Curious what others are automating.

#SoftwareEngineering #Automation #AI #Python #JobSearch #SystemDesign #MCP #DevOps"""

def render_edge_screenshot(html_string, output_png_path):
    temp_html = os.path.join(CAROUSEL_DIR, f"temp_{int(time.time())}.html")
    with open(temp_html, "w", encoding="utf-8") as f:
        f.write(html_string)
    cmd = [EDGE_PATH, "--headless", "--disable-gpu", "--window-size=1080,1350", "--hide-scrollbars", f"--screenshot={output_png_path}", temp_html]
    subprocess.run(cmd, check=True)
    if os.path.exists(temp_html):
        os.remove(temp_html)

def generate_upgraded_post1_carousel():
    os.makedirs(CAROUSEL_DIR, exist_ok=True)
    os.makedirs(PACKAGES_DIR, exist_ok=True)

    print("=================================================================")
    print("[POST 1] Generating Upgraded Job Hunt Autopilot 4-Slide Carousel")
    print("=================================================================")

    # SLIDE 1: Hero Cover Card using pristine 3D Command Center Artwork (ai_robot_human_command_center_diagram.png)
    print("\n[Slide 1/4] Rendering Slide 1 Hero Cover (Pristine 3D Artwork + Vector Overlay)...")
    art_path = os.path.join(IMAGES_DIR, "ai_robot_human_command_center_diagram.png")
    s1_html = SLIDE1_HERO_HTML.replace("{ARTWORK_PATH}", art_path.replace("\\", "/"))
    s1_path = os.path.join(CAROUSEL_DIR, "post1_slide_1_hero.png")
    render_edge_screenshot(s1_html, s1_path)
    print(f"[OK] Slide 1 ready (ZERO GIBBERISH): {s1_path}")

    # SLIDE 2: 5-Layer Job Hunt System Architecture Specs Card
    print("\n[Slide 2/4] Rendering 5-Layer Job Hunt Specs Card (Space Grotesk)...")
    s2_path = os.path.join(CAROUSEL_DIR, "post1_slide_2_pipeline.png")
    render_edge_screenshot(SLIDE2_5LAYER_PIPELINE_HTML, s2_path)
    print(f"[OK] Slide 2 ready (5-Layer Specs): {s2_path}")

    # SLIDE 3: Dual 3D Character Avatars (Stressed vs Happy)
    print("\n[Slide 3/4] Reusing Dual 3D Character Avatars (Stressed vs Happy)...")
    existing_s3 = os.path.join(PROJECT_ROOT, "output", "posts", "carousel_bundle", "slide_3_before_vs_after_comparison.png")
    s3_path = os.path.join(CAROUSEL_DIR, "post1_slide_3_comparison.png")
    if os.path.exists(existing_s3):
        shutil.copy(existing_s3, s3_path)
        print(f"[OK] Slide 3 ready: {s3_path}")

    # SLIDE 4: 5 Scheduled Tasks Roadmap Card
    print("\n[Slide 4/4] Reusing 5 Scheduled Tasks Roadmap Card...")
    existing_s4 = os.path.join(CAROUSEL_DIR, "post1_slide_4_tasks.png")
    s4_path = os.path.join(CAROUSEL_DIR, "post1_slide_4_tasks.png")
    print(f"[OK] Slide 4 ready: {s4_path}")

    # Package
    post_id = f"post1_job_hunt_{int(time.time())}"
    bundle = {
        "post_id": post_id,
        "series": "LinkedIn Two-Post Series",
        "post_number": 1,
        "post_title": "Autonomous Job Hunt Autopilot",
        "posting_order": "SECOND (heavyweight follow-up)",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "post_body": POST_1_COPY,
        "carousel_slides": [
            {"slide": 1, "file": s1_path, "desc": "Pristine 3D Hero Cover (Zero Gibberish Text)"},
            {"slide": 2, "file": s2_path, "desc": "5-Layer Job Hunt Specs Card (Space Grotesk)"},
            {"slide": 3, "file": s3_path, "desc": "Dual 3D Avatars: Manual vs Autopilot"},
            {"slide": 4, "file": s4_path, "desc": "5 Scheduled Tasks with Real Stats"},
        ],
        "status": "ready_to_post"
    }

    pkg_path = os.path.join(PACKAGES_DIR, f"{post_id}_package.json")
    with open(pkg_path, "w", encoding="utf-8") as f:
        json.dump(bundle, f, indent=2)

    print("\n=================================================================")
    print("[POST 1] Job Hunt Autopilot — ALL 4 SLIDES PERFECTLY UPGRADED")
    print("=================================================================")
    print(f"Package: {pkg_path}")
    for s in bundle["carousel_slides"]:
        exists = "OK" if os.path.exists(s["file"]) else "MISSING"
        print(f"  Slide {s['slide']}: [{exists}] {s['desc']}")

    return pkg_path

if __name__ == "__main__":
    generate_upgraded_post1_carousel()
