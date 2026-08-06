"""
Hybrid Vector Composite Slide 1 Cover Studio
Combines pristine 3D Command Center artwork background with 100% crisp glassmorphic vector text overlays.
Eliminates ALL AI gibberish text while providing complete technical context & project proof!
"""

import os
import sys
import subprocess
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
IMAGES_DIR = os.path.join(PROJECT_ROOT, "output", "posts", "images")
POST1_CAROUSEL_DIR = os.path.join(PROJECT_ROOT, "output", "posts", "carousel_bundle_post1")
POST2_CAROUSEL_DIR = os.path.join(PROJECT_ROOT, "output", "posts", "carousel_bundle")
EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

# ═══════════════════════════════════════════════════════════════════════
# POST 1 SLIDE 1: Autonomous Job Hunt Autopilot (Pristine 3D + 100% Crisp English Text)
# ═══════════════════════════════════════════════════════════════════════
POST1_SLIDE1_HYBRID_HTML = """<!DOCTYPE html>
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
    padding: 22px;
    justify-content: space-between;
    overflow: hidden;
    position: relative;
  }

  .outer-frame {
    border: 3.5px solid #00e5ff;
    box-shadow: 0 0 45px rgba(0, 229, 255, 0.4), inset 0 0 20px rgba(0, 229, 255, 0.15);
    border-radius: 20px;
    padding: 18px;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    background: rgba(6, 12, 28, 0.95);
    position: relative;
    z-index: 2;
  }

  .header {
    background: rgba(13, 23, 51, 0.95);
    border: 2.5px solid #00e5ff;
    box-shadow: 0 0 25px rgba(0, 229, 255, 0.4);
    border-radius: 14px;
    padding: 14px 22px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .h-sub { font-family: 'Fira Code', monospace; font-size: 13px; font-weight: 800; color: #ff9100; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 2px; }
  .h-title { font-size: 32px; font-weight: 900; color: #fff; letter-spacing: -0.5px; }
  .h-title span { color: #00e5ff; text-shadow: 0 0 16px rgba(0,229,255,0.9); }
  .h-badge { font-family: 'Fira Code', monospace; font-size: 12px; font-weight: 800; background: #00e5ff; color: #040814; padding: 6px 14px; border-radius: 8px; }

  .hero-viewport {
    width: 100%;
    height: 480px;
    margin: 10px 0;
    border-radius: 16px;
    overflow: hidden;
    border: 2.5px solid #00e5ff;
    box-shadow: 0 0 30px rgba(0, 229, 255, 0.35);
    position: relative;
  }
  .bg-art { width: 100%; height: 100%; object-fit: cover; }

  .badge-top-left {
    position: absolute;
    top: 14px;
    left: 14px;
    background: rgba(4, 8, 20, 0.9);
    border: 1.5px solid #00e5ff;
    border-radius: 8px;
    padding: 6px 14px;
    font-family: 'Fira Code', monospace;
    font-size: 12px;
    font-weight: 800;
    color: #00e5ff;
    backdrop-filter: blur(8px);
  }
  .badge-top-right {
    position: absolute;
    top: 14px;
    right: 14px;
    background: rgba(4, 8, 20, 0.9);
    border: 1.5px solid #ff9100;
    border-radius: 8px;
    padding: 6px 14px;
    font-family: 'Fira Code', monospace;
    font-size: 12px;
    font-weight: 800;
    color: #ff9100;
    backdrop-filter: blur(8px);
  }

  .stack-grid {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-bottom: 8px;
  }
  .layer-card {
    background: rgba(15, 23, 42, 0.96);
    border-radius: 12px;
    padding: 12px 18px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    backdrop-filter: blur(10px);
  }
  .lc-amber  { border: 2px solid #ff9100; box-shadow: 0 0 14px rgba(255, 145, 0, 0.35); }
  .lc-cyan   { border: 2px solid #00e5ff; box-shadow: 0 0 14px rgba(0, 229, 255, 0.35); }
  .lc-green  { border: 2px solid #00e676; box-shadow: 0 0 14px rgba(0, 230, 118, 0.35); }
  .lc-purple { border: 2px solid #e040fb; box-shadow: 0 0 14px rgba(224, 64, 251, 0.35); }
  .lc-red    { border: 2px solid #ff1744; box-shadow: 0 0 14px rgba(255, 23, 68, 0.35); }

  .lc-left { display: flex; flex-direction: column; gap: 2px; }
  .lc-title { font-size: 17px; font-weight: 900; }
  .lc-amber  .lc-title { color: #ff9100; }
  .lc-cyan   .lc-title { color: #00e5ff; }
  .lc-green  .lc-title { color: #00e676; }
  .lc-purple .lc-title { color: #e040fb; }
  .lc-red    .lc-title { color: #ff5252; }

  .lc-desc { font-size: 13px; color: #e2e8f0; font-weight: 700; }
  .lc-code { font-family: 'Fira Code', monospace; font-size: 11px; font-weight: 800; background: #040814; color: #facc15; padding: 4px 10px; border-radius: 6px; border: 1px solid rgba(250,204,21,0.4); }

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
    padding: 10px;
    text-align: center;
    box-shadow: 0 0 15px rgba(0, 229, 255, 0.25);
  }
  .sc-val { font-size: 20px; font-weight: 900; color: #00e5ff; }
  .sc-lbl { font-size: 10.5px; font-weight: 800; color: #facc15; text-transform: uppercase; margin-top: 2px; }

  .footer-cta {
    background: linear-gradient(90deg, #1e1b4b, #311b92);
    border: 2.5px solid #818cf8;
    border-radius: 14px;
    padding: 13px;
    text-align: center;
    font-size: 19px;
    font-weight: 900;
    color: #c7d2fe;
    letter-spacing: 0.5px;
  }
</style>
</head>
<body>
  <div class="outer-frame">
    <div class="header">
      <div>
        <div class="h-sub">⚡ AUTONOMOUS RECRUITMENT ENGINE</div>
        <div class="h-title">AUTONOMOUS <span>JOB HUNT AUTOPILOT</span></div>
      </div>
      <div class="h-badge">10-STAGE PIPELINE</div>
    </div>

    <div class="hero-viewport">
      <img src="file:///{ARTWORK_PATH}" class="bg-art" alt="3D Command Center Artwork">
      <div class="badge-top-left">🤖 AI AGENT OPERATED</div>
      <div class="badge-top-right">🛡️ 100% BAN-SAFE</div>
    </div>

    <div class="stack-grid">
      <div class="layer-card lc-amber">
        <div class="lc-left">
          <div class="lc-title">📱 1. CLIENT & SLACK APPROVAL GATE</div>
          <div class="lc-desc">Slack mobile webhooks for 1-tap connection approval + SQLite web UI.</div>
        </div>
        <div class="lc-code">web/ + check_approvals.py</div>
      </div>
      <div class="layer-card lc-cyan">
        <div class="lc-left">
          <div class="lc-title">🔍 2. AUTOMATED DISCOVERY ENGINE</div>
          <div class="lc-desc">LinkedIn MCP daily discovery at 08:00 IST. Dedupes & scores roles (≥80 fit).</div>
        </div>
        <div class="lc-code">daily-discovery.ps1</div>
      </div>
      <div class="layer-card lc-green">
        <div class="lc-left">
          <div class="lc-title">🧠 3. AI RESEARCH & CV TAILORING</div>
          <div class="lc-desc">Analyzes JDs, researches company stack, generates tailored CV PDFs & pitches.</div>
        </div>
        <div class="lc-code">cv-architect + outreach</div>
      </div>
      <div class="layer-card lc-purple">
        <div class="lc-left">
          <div class="lc-title">✉️ 4. TWO-STAGE OUTREACH DISPATCH</div>
          <div class="lc-desc">Bare connection request → accept watcher → auto-sends CV + pitch packet.</div>
        </div>
        <div class="lc-code">flush-approved.ps1</div>
      </div>
      <div class="layer-card lc-red">
        <div class="lc-left">
          <div class="lc-title">💾 5. STATE STORE & TRACKING ENGINE</div>
          <div class="lc-desc">Local SQLite3 DB synced bi-directionally with Notion Cloud Board (Day 3/7 follow-ups).</div>
        </div>
        <div class="lc-code">board_db.py + notion_push.py</div>
      </div>
    </div>

    <div class="stats-banner">
      <div class="stat-card"><div class="sc-val">62 Jobs</div><div class="sc-lbl">Discovered</div></div>
      <div class="stat-card"><div class="sc-val">5 Applied</div><div class="sc-lbl">Submitted</div></div>
      <div class="stat-card"><div class="sc-val">0 Bounces</div><div class="sc-lbl">Verified Mail</div></div>
      <div class="stat-card"><div class="sc-val">~2 min</div><div class="sc-lbl">Human Effort</div></div>
    </div>

    <div class="footer-cta">🚀 5 WINDOWS SCHEDULED TASKS • RUNS WHILE YOU SLEEP</div>
  </div>
</body>
</html>"""

# ═══════════════════════════════════════════════════════════════════════
# POST 2 SLIDE 1: AI Visual Content Studio (Pristine 3D + 100% Crisp English Text)
# ═══════════════════════════════════════════════════════════════════════
POST2_SLIDE1_HYBRID_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@700;800;900&family=Fira+Code:wght@700;800&display=swap');
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    width: 1080px;
    height: 1350px;
    background: #030712;
    font-family: 'Outfit', -apple-system, sans-serif;
    color: #ffffff;
    display: flex;
    flex-direction: column;
    padding: 22px;
    justify-content: space-between;
    overflow: hidden;
    position: relative;
  }

  .outer-frame {
    border: 3.5px solid #e040fb;
    box-shadow: 0 0 45px rgba(224, 64, 251, 0.5), inset 0 0 20px rgba(224, 64, 251, 0.15);
    border-radius: 20px;
    padding: 18px;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    background: rgba(6, 12, 28, 0.95);
    position: relative;
    z-index: 2;
  }

  .header {
    background: rgba(20, 8, 38, 0.95);
    border: 2.5px solid #e040fb;
    box-shadow: 0 0 25px rgba(224, 64, 251, 0.45);
    border-radius: 14px;
    padding: 14px 22px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .h-sub { font-family: 'Fira Code', monospace; font-size: 13px; font-weight: 800; color: #00e5ff; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 2px; }
  .h-title { font-size: 32px; font-weight: 900; color: #fff; letter-spacing: -0.5px; }
  .h-title span { color: #e040fb; text-shadow: 0 0 16px rgba(224,64,251,0.95); }
  .h-badge { font-family: 'Fira Code', monospace; font-size: 12px; font-weight: 800; background: #e040fb; color: #040814; padding: 6px 14px; border-radius: 8px; }

  .hero-viewport {
    width: 100%;
    height: 480px;
    margin: 10px 0;
    border-radius: 16px;
    overflow: hidden;
    border: 2.5px solid #e040fb;
    box-shadow: 0 0 30px rgba(224, 64, 251, 0.35);
    position: relative;
  }
  .bg-art { width: 100%; height: 100%; object-fit: cover; }

  .badge-top-left {
    position: absolute;
    top: 14px;
    left: 14px;
    background: rgba(4, 8, 20, 0.9);
    border: 1.5px solid #e040fb;
    border-radius: 8px;
    padding: 6px 14px;
    font-family: 'Fira Code', monospace;
    font-size: 12px;
    font-weight: 800;
    color: #e040fb;
    backdrop-filter: blur(8px);
  }
  .badge-top-right {
    position: absolute;
    top: 14px;
    right: 14px;
    background: rgba(4, 8, 20, 0.9);
    border: 1.5px solid #00e5ff;
    border-radius: 8px;
    padding: 6px 14px;
    font-family: 'Fira Code', monospace;
    font-size: 12px;
    font-weight: 800;
    color: #00e5ff;
    backdrop-filter: blur(8px);
  }

  .stack-grid {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-bottom: 8px;
  }
  .layer-card {
    background: rgba(15, 23, 42, 0.96);
    border-radius: 12px;
    padding: 12px 18px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    backdrop-filter: blur(10px);
  }
  .lc-amber  { border: 2px solid #ff9100; box-shadow: 0 0 14px rgba(255, 145, 0, 0.35); }
  .lc-cyan   { border: 2px solid #00e5ff; box-shadow: 0 0 14px rgba(0, 229, 255, 0.35); }
  .lc-purple { border: 2px solid #e040fb; box-shadow: 0 0 14px rgba(224, 64, 251, 0.35); }
  .lc-green  { border: 2px solid #00e676; box-shadow: 0 0 14px rgba(0, 230, 118, 0.35); }
  .lc-red    { border: 2px solid #ff1744; box-shadow: 0 0 14px rgba(255, 23, 68, 0.35); }

  .lc-left { display: flex; flex-direction: column; gap: 2px; }
  .lc-title { font-size: 17px; font-weight: 900; }
  .lc-amber  .lc-title { color: #ff9100; }
  .lc-cyan   .lc-title { color: #00e5ff; }
  .lc-purple .lc-title { color: #e040fb; }
  .lc-green  .lc-title { color: #00e676; }
  .lc-red    .lc-title { color: #ff5252; }

  .lc-desc { font-size: 13px; color: #e2e8f0; font-weight: 700; }
  .lc-code { font-family: 'Fira Code', monospace; font-size: 11px; font-weight: 800; background: #040814; color: #facc15; padding: 4px 10px; border-radius: 6px; border: 1px solid rgba(250,204,21,0.4); }

  .stats-banner {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin-bottom: 4px;
  }
  .stat-card {
    background: rgba(15, 23, 42, 0.95);
    border: 2px solid #e040fb;
    border-radius: 12px;
    padding: 10px;
    text-align: center;
    box-shadow: 0 0 15px rgba(224, 64, 251, 0.25);
  }
  .sc-val { font-size: 20px; font-weight: 900; color: #e040fb; }
  .sc-lbl { font-size: 10.5px; font-weight: 800; color: #00e5ff; text-transform: uppercase; margin-top: 2px; }

  .footer-cta {
    background: linear-gradient(90deg, #1e1b4b, #311b92);
    border: 2.5px solid #818cf8;
    border-radius: 14px;
    padding: 13px;
    text-align: center;
    font-size: 19px;
    font-weight: 900;
    color: #c7d2fe;
    letter-spacing: 0.5px;
  }
</style>
</head>
<body>
  <div class="outer-frame">
    <div class="header">
      <div>
        <div class="h-sub">⚡ AI CONTENT CREATION ENGINE</div>
        <div class="h-title">AI VISUAL <span>CONTENT STUDIO</span></div>
      </div>
      <div class="h-badge">8K CAROUSEL PACKAGER</div>
    </div>

    <div class="hero-viewport">
      <img src="file:///{ARTWORK_PATH}" class="bg-art" alt="3D Command Center Artwork">
      <div class="badge-top-left">🤖 AI VISUAL ENGINE</div>
      <div class="badge-top-right">🔌 STDIO RPC MCP</div>
    </div>

    <div class="stack-grid">
      <div class="layer-card lc-amber">
        <div class="lc-left">
          <div class="lc-title">✍️ 1. LLM PROOF-OF-WORK COPYWRITER</div>
          <div class="lc-desc">5-part LinkedIn post copy grounded in real project architecture & metrics.</div>
        </div>
        <div class="lc-code">post_generator.py</div>
      </div>
      <div class="layer-card lc-cyan">
        <div class="lc-left">
          <div class="lc-title">📐 2. EDGE HEADLESS VECTOR RENDERER</div>
          <div class="lc-desc">Space Grotesk & Outfit typography HTML cards converted to crisp vector PNGs.</div>
        </div>
        <div class="lc-code">generate_4slide_carousel.py</div>
      </div>
      <div class="layer-card lc-purple">
        <div class="lc-left">
          <div class="lc-title">🖼️ 3. FLUX.1 & IMAGEN 3 VISUAL ENGINE</div>
          <div class="lc-desc">Renders 8K photorealistic 3D command centers & character avatars via REST API.</div>
        </div>
        <div class="lc-code">image_studio.py</div>
      </div>
      <div class="layer-card lc-green">
        <div class="lc-left">
          <div class="lc-title">📊 4. 4-SLIDE CAROUSEL PACKAGER</div>
          <div class="lc-desc">Bundles LinkedIn post copy + 4 carousel slides into ready JSON publishing packages.</div>
        </div>
        <div class="lc-code">package_post2_content_studio.py</div>
      </div>
      <div class="layer-card lc-red">
        <div class="lc-left">
          <div class="lc-title">🔌 5. STDIO RPC PROTOCOL GATEWAY</div>
          <div class="lc-desc">Orchestrates mcp-post-studio tools with mcp-server-linkedin for 1-click dispatch.</div>
        </div>
        <div class="lc-code">mcp_server.py</div>
      </div>
    </div>

    <div class="stats-banner">
      <div class="stat-card"><div class="sc-val">FLUX.1</div><div class="sc-lbl">Visual Engine</div></div>
      <div class="stat-card"><div class="sc-val">8K High-Res</div><div class="sc-lbl">Rendering</div></div>
      <div class="stat-card"><div class="sc-val">Stdio RPC</div><div class="sc-lbl">MCP Protocol</div></div>
      <div class="stat-card"><div class="sc-val">4-Slide</div><div class="sc-lbl">Carousel Pack</div></div>
    </div>

    <div class="footer-cta">🚀 AUTOMATED 8K CAROUSEL ENGINE • POWERED BY MCP</div>
  </div>
</body>
</html>"""

def render_edge_screenshot(html_string, output_png_path):
    temp_html = os.path.join(PROJECT_ROOT, f"temp_{int(time.time())}.html")
    with open(temp_html, "w", encoding="utf-8") as f:
        f.write(html_string)
    cmd = [EDGE_PATH, "--headless", "--disable-gpu", "--window-size=1080,1350", "--hide-scrollbars", f"--screenshot={output_png_path}", temp_html]
    subprocess.run(cmd, check=True)
    if os.path.exists(temp_html):
        os.remove(temp_html)

def render_hybrid_slide1_covers():
    art_path = os.path.join(IMAGES_DIR, "ai_robot_human_command_center_diagram.png")

    print("=================================================================")
    print("[Hybrid Vector Studio] Rendering Pristine 3D + 100% Crisp English Covers...")
    print("=================================================================")

    # 1. Render Post 1 Slide 1 (Job Hunt Autopilot)
    print("\n[Post 1 Slide 1] Rendering Pristine 3D + Crisp English Hybrid Cover for Job Hunt Autopilot...")
    p1_html = POST1_SLIDE1_HYBRID_HTML.replace("{ARTWORK_PATH}", art_path.replace("\\", "/"))
    p1_path = os.path.join(POST1_CAROUSEL_DIR, "post1_slide_1_hero.png")
    render_edge_screenshot(p1_html, p1_path)
    print(f"[OK] Post 1 Slide 1 Hybrid Cover Ready: {p1_path}")

    # 2. Render Post 2 Slide 1 (AI Visual Content Studio)
    print("\n[Post 2 Slide 1] Rendering Pristine 3D + Crisp English Hybrid Cover for Content Studio...")
    p2_html = POST2_SLIDE1_HYBRID_HTML.replace("{ARTWORK_PATH}", art_path.replace("\\", "/"))
    p2_path = os.path.join(POST2_CAROUSEL_DIR, "slide_1_hero_command_center.png")
    render_edge_screenshot(p2_html, p2_path)
    print(f"[OK] Post 2 Slide 1 Hybrid Cover Ready: {p2_path}")

    print("\n=================================================================")
    print("[SUCCESS] BOTH SLIDE 1 COVERS RE-RENDERED WITH ZERO GIBBERISH TEXT!")
    print("=================================================================")

if __name__ == "__main__":
    render_hybrid_slide1_covers()
