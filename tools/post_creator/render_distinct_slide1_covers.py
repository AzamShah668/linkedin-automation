"""
Distinct Slide 1 Hero Cover Generator
Renders 2 distinct, highly detailed Slide 1 covers with topic-specific HUD overlays, crisp typography, and zero gibberish text:
- Post 1 Slide 1: Autonomous Job Hunt Autopilot (Recruitment Pipeline specs, cyan/amber theme, 62 jobs / 0 bounces stats)
- Post 2 Slide 1: AI Visual Content Studio (8K Image Generator specs, purple/cyan theme, FLUX.1 / MCP stats)
"""

import os
import sys
import subprocess
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
POST_CREATOR_DIR = os.path.join(PROJECT_ROOT, "tools", "post_creator")
IMAGES_DIR = os.path.join(PROJECT_ROOT, "output", "posts", "images")
POST1_CAROUSEL_DIR = os.path.join(PROJECT_ROOT, "output", "posts", "carousel_bundle_post1")
POST2_CAROUSEL_DIR = os.path.join(PROJECT_ROOT, "output", "posts", "carousel_bundle")
EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

# ═══════════════════════════════════════════════════════════════════════
# POST 1 SLIDE 1: Autonomous Job Hunt Autopilot (Cyan & Amber Recruitment Cyberpunk)
# ═══════════════════════════════════════════════════════════════════════
POST1_SLIDE1_HTML = """<!DOCTYPE html>
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
    padding: 16px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .h-left { display: flex; flex-direction: column; }
  .h-sub { font-family: 'Fira Code', monospace; font-size: 13px; font-weight: 800; color: #ff9100; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 2px; }
  .h-title { font-size: 32px; font-weight: 900; color: #fff; letter-spacing: -0.5px; }
  .h-title span { color: #00e5ff; text-shadow: 0 0 16px rgba(0,229,255,0.9); }
  .h-tag { font-family: 'Fira Code', monospace; font-size: 12px; font-weight: 800; background: #00e5ff; color: #040814; padding: 6px 14px; border-radius: 8px; }

  .artwork-box {
    width: 100%;
    height: 520px;
    margin: 12px 0;
    border-radius: 16px;
    overflow: hidden;
    border: 2.5px solid #00e5ff;
    box-shadow: 0 0 30px rgba(0, 229, 255, 0.35);
    position: relative;
  }
  .art-img { width: 100%; height: 100%; object-fit: cover; }

  .spec-overlay {
    position: absolute;
    bottom: 12px;
    left: 12px;
    right: 12px;
    background: rgba(4, 8, 20, 0.92);
    border: 2px solid #ff9100;
    box-shadow: 0 0 20px rgba(255, 145, 0, 0.4);
    border-radius: 12px;
    padding: 12px 18px;
    backdrop-filter: blur(10px);
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .so-head { font-family: 'Fira Code', monospace; font-size: 12px; font-weight: 800; color: #ff9100; text-transform: uppercase; letter-spacing: 1px; }
  .so-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
  .so-pill { font-size: 12px; font-weight: 800; background: #081026; color: #fff; border: 1.5px solid #00e5ff; padding: 6px 10px; border-radius: 6px; text-align: center; }

  .hud-stack {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-bottom: 8px;
  }
  .hud-row {
    background: rgba(15, 23, 42, 0.95);
    border-radius: 10px;
    padding: 12px 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .hr-1 { border: 2px solid #ff9100; box-shadow: 0 0 14px rgba(255, 145, 0, 0.3); }
  .hr-2 { border: 2px solid #00e5ff; box-shadow: 0 0 14px rgba(0, 229, 255, 0.3); }
  .hr-3 { border: 2px solid #00e676; box-shadow: 0 0 14px rgba(0, 230, 118, 0.3); }

  .hr-title { font-size: 17px; font-weight: 900; }
  .hr-1 .hr-title { color: #ff9100; }
  .hr-2 .hr-title { color: #00e5ff; }
  .hr-3 .hr-title { color: #00e676; }

  .hr-desc { font-size: 13.5px; color: #cbd5e1; font-weight: 700; }
  .hr-code { font-family: 'Fira Code', monospace; font-size: 11px; font-weight: 800; background: #040814; color: #facc15; padding: 4px 10px; border-radius: 6px; border: 1px solid rgba(250,204,21,0.4); }

  .stats-banner {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin-bottom: 6px;
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
    padding: 14px;
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
      <div class="h-left">
        <div class="h-sub">⚡ AUTONOMOUS RECRUITMENT ENGINE</div>
        <div class="h-title">JOB HUNT <span>AUTOPILOT</span></div>
      </div>
      <div class="h-tag">10-STAGE PIPELINE</div>
    </div>

    <div class="artwork-box">
      <img src="file:///{ARTWORK_PATH}" class="art-img" alt="3D Job Hunt Command Center">
      <div class="spec-overlay">
        <div class="so-head">🤖 RECRUITMENT PIPELINE ARCHITECTURE (PLAYWRIGHT + LINKEDIN MCP)</div>
        <div class="so-grid">
          <div class="so-pill">🔍 LinkedIn Discovery</div>
          <div class="so-pill">🧠 Notion & SQLite DB</div>
          <div class="so-pill">📝 AI Tailored CV PDF</div>
          <div class="so-pill">📱 1-Tap Slack Mobile</div>
          <div class="so-pill">✉️ 2-Touch Pitching</div>
          <div class="so-pill">🛡️ 100% Ban-Safe</div>
        </div>
      </div>
    </div>

    <div class="hud-stack">
      <div class="hud-row hr-1">
        <div>
          <div class="hr-title">1. Automated Scraper & Scorer</div>
          <div class="hr-desc">LinkedIn MCP daily discovery at 08:00 IST. Dedupes & scores roles (≥80 fit).</div>
        </div>
        <div class="hr-code">daily-discovery.ps1</div>
      </div>
      <div class="hud-row hr-2">
        <div>
          <div class="hr-title">2. Human-in-the-Loop Mobile Gate</div>
          <div class="hr-desc">Slack webhook review card. 1-tap mobile phone confirmation before any outreach.</div>
        </div>
        <div class="hr-code">check_approvals.py</div>
      </div>
      <div class="hud-row hr-3">
        <div>
          <div class="hr-title">3. Stealth Outreach & Pitch Tracker</div>
          <div class="hr-desc">Bare connection request → accept watcher → auto-sends tailored CV + pitch packet.</div>
        </div>
        <div class="hr-code">watch-accepts.ps1</div>
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
# POST 2 SLIDE 1: AI Visual Content Studio (Purple & Neon Cyan Studio Cyberpunk)
# ═══════════════════════════════════════════════════════════════════════
POST2_SLIDE1_HTML = """<!DOCTYPE html>
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
    padding: 24px;
    justify-content: space-between;
    overflow: hidden;
    position: relative;
  }

  .outer-frame {
    border: 3.5px solid #e040fb;
    box-shadow: 0 0 45px rgba(224, 64, 251, 0.5), inset 0 0 20px rgba(224, 64, 251, 0.15);
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
    background: #140826;
    border: 2.5px solid #e040fb;
    box-shadow: 0 0 25px rgba(224, 64, 251, 0.45);
    border-radius: 14px;
    padding: 16px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .h-left { display: flex; flex-direction: column; }
  .h-sub { font-family: 'Fira Code', monospace; font-size: 13px; font-weight: 800; color: #00e5ff; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 2px; }
  .h-title { font-size: 32px; font-weight: 900; color: #fff; letter-spacing: -0.5px; }
  .h-title span { color: #e040fb; text-shadow: 0 0 16px rgba(224,64,251,0.95); }
  .h-tag { font-family: 'Fira Code', monospace; font-size: 12px; font-weight: 800; background: #e040fb; color: #040814; padding: 6px 14px; border-radius: 8px; }

  .artwork-box {
    width: 100%;
    height: 520px;
    margin: 12px 0;
    border-radius: 16px;
    overflow: hidden;
    border: 2.5px solid #e040fb;
    box-shadow: 0 0 30px rgba(224, 64, 251, 0.35);
    position: relative;
  }
  .art-img { width: 100%; height: 100%; object-fit: cover; }

  .spec-overlay {
    position: absolute;
    bottom: 12px;
    left: 12px;
    right: 12px;
    background: rgba(4, 8, 20, 0.92);
    border: 2px solid #00e5ff;
    box-shadow: 0 0 20px rgba(0, 229, 255, 0.4);
    border-radius: 12px;
    padding: 12px 18px;
    backdrop-filter: blur(10px);
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .so-head { font-family: 'Fira Code', monospace; font-size: 12px; font-weight: 800; color: #00e5ff; text-transform: uppercase; letter-spacing: 1px; }
  .so-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
  .so-pill { font-size: 12px; font-weight: 800; background: #081026; color: #fff; border: 1.5px solid #e040fb; padding: 6px 10px; border-radius: 6px; text-align: center; }

  .hud-stack {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-bottom: 8px;
  }
  .hud-row {
    background: rgba(15, 23, 42, 0.95);
    border-radius: 10px;
    padding: 12px 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .hr-1 { border: 2px solid #e040fb; box-shadow: 0 0 14px rgba(224, 64, 251, 0.3); }
  .hr-2 { border: 2px solid #00e5ff; box-shadow: 0 0 14px rgba(0, 229, 255, 0.3); }
  .hr-3 { border: 2px solid #facc15; box-shadow: 0 0 14px rgba(250, 204, 21, 0.3); }

  .hr-title { font-size: 17px; font-weight: 900; }
  .hr-1 .hr-title { color: #e040fb; }
  .hr-2 .hr-title { color: #00e5ff; }
  .hr-3 .hr-title { color: #facc15; }

  .hr-desc { font-size: 13.5px; color: #cbd5e1; font-weight: 700; }
  .hr-code { font-family: 'Fira Code', monospace; font-size: 11px; font-weight: 800; background: #040814; color: #facc15; padding: 4px 10px; border-radius: 6px; border: 1px solid rgba(250,204,21,0.4); }

  .stats-banner {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin-bottom: 6px;
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
    padding: 14px;
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
      <div class="h-left">
        <div class="h-sub">⚡ AI CONTENT CREATION ENGINE</div>
        <div class="h-title">AI VISUAL <span>CONTENT STUDIO</span></div>
      </div>
      <div class="h-tag">8K CAROUSEL PACKAGER</div>
    </div>

    <div class="artwork-box">
      <img src="file:///{ARTWORK_PATH}" class="art-img" alt="3D Content Studio Command Center">
      <div class="spec-overlay">
        <div class="so-head">🎨 VISUAL CONTENT PIPELINE (FLUX.1 + IMAGEN 3 + MCP PROTOCOL)</div>
        <div class="so-grid">
          <div class="so-pill">✍️ LLM Proof Copywriter</div>
          <div class="so-pill">🖼️ FLUX.1 & Imagen 3</div>
          <div class="so-pill">📐 Vector Edge Renderer</div>
          <div class="so-pill">📊 Space Grotesk Cards</div>
          <div class="so-pill">🎭 Dual 3D Avatars</div>
          <div class="so-pill">🔌 Stdio RPC MCP Hub</div>
        </div>
      </div>
    </div>

    <div class="hud-stack">
      <div class="hud-row hr-1">
        <div>
          <div class="hr-title">1. LLM Proof-of-Work Copywriter</div>
          <div class="hr-desc">Generates 5-part LinkedIn post copy grounded in real project code & metrics.</div>
        </div>
        <div class="hr-code">post_generator.py</div>
      </div>
      <div class="hud-row hr-2">
        <div>
          <div class="hr-title">2. Edge Headless Vector Renderer</div>
          <div class="hr-desc">Renders Space Grotesk & Outfit typography HTML cards to crisp PNG vector slides.</div>
        </div>
        <div class="hr-code">generate_4slide_carousel.py</div>
      </div>
      <div class="hud-row hr-3">
        <div>
          <div class="hr-title">3. Stdio RPC Protocol Gateway</div>
          <div class="hr-desc">Dispatches ready JSON packages via mcp-post-studio to mcp-server-linkedin.</div>
        </div>
        <div class="hr-code">mcp_server.py</div>
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

def render_distinct_covers():
    art_path = os.path.join(IMAGES_DIR, "ai_robot_human_command_center_diagram.png")

    print("=================================================================")
    print("[Distinct Slide 1 Cover Generator] Rendering Custom Slide 1 Covers...")
    print("=================================================================")

    # 1. Render Post 1 Slide 1 (Job Hunt Autopilot)
    print("\n[Post 1 Slide 1] Rendering Autonomous Job Hunt Autopilot Hero Cover...")
    p1_s1_html = POST1_SLIDE1_HTML.replace("{ARTWORK_PATH}", art_path.replace("\\", "/"))
    p1_s1_path = os.path.join(POST1_CAROUSEL_DIR, "post1_slide_1_hero.png")
    render_edge_screenshot(p1_s1_html, p1_s1_path)
    print(f"[OK] Post 1 Slide 1 Ready: {p1_s1_path}")

    # 2. Render Post 2 Slide 1 (AI Visual Content Studio)
    print("\n[Post 2 Slide 1] Rendering AI Visual Content Studio Hero Cover...")
    p2_s1_html = POST2_SLIDE1_HTML.replace("{ARTWORK_PATH}", art_path.replace("\\", "/"))
    p2_s1_path = os.path.join(POST2_CAROUSEL_DIR, "slide_1_hero_command_center.png")
    render_edge_screenshot(p2_s1_html, p2_s1_path)
    print(f"[OK] Post 2 Slide 1 Ready: {p2_s1_path}")

    print("\n=================================================================")
    print("[SUCCESS] BOTH SLIDE 1 COVERS RE-RENDERED WITH DISTINCT TOPIC SPECS!")
    print("=================================================================")

if __name__ == "__main__":
    render_distinct_covers()
