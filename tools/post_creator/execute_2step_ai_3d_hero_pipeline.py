"""
2-Step AI 3D Command Center Slide 1 Hero Studio
Step 1: Render clean, readable 5-layer base architecture diagram
Step 2: Execute FLUX.1 AI Image Generation to build the 3D Command Center Visual (3D Human Developer + 3D AI Robot Agent + Glowing Cyan/Orange Control Screen)
"""

import os
import sys
import subprocess
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
POST_CREATOR_DIR = os.path.join(PROJECT_ROOT, "tools", "post_creator")
sys.path.insert(0, POST_CREATOR_DIR)

from image_studio import create_high_res_image

IMAGES_DIR = os.path.join(PROJECT_ROOT, "output", "posts", "images")
CAROUSEL_POST1_DIR = os.path.join(PROJECT_ROOT, "output", "posts", "carousel_bundle_post1")
CAROUSEL_POST2_DIR = os.path.join(PROJECT_ROOT, "output", "posts", "carousel_bundle")
EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

# ═══════════════════════════════════════════════════════════════════════
# STEP 1: Render Base Clean Core Architecture Diagram
# ═══════════════════════════════════════════════════════════════════════
STEP1_BASE_HTML = """<!DOCTYPE html>
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
    background-image: 
      radial-gradient(circle at 50% 0%, rgba(0, 229, 255, 0.2) 0%, transparent 50%),
      radial-gradient(circle at 50% 100%, rgba(255, 145, 0, 0.2) 0%, transparent 50%),
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
  }

  .header {
    background: #0d1733;
    border: 2.5px solid #00e5ff;
    box-shadow: 0 0 25px rgba(0, 229, 255, 0.4);
    border-radius: 14px;
    padding: 18px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .h-title { font-size: 32px; font-weight: 900; color: #fff; }
  .h-title span { color: #00e5ff; text-shadow: 0 0 16px rgba(0,229,255,0.9); }
  .h-badge { font-family: 'Fira Code', monospace; font-size: 13px; font-weight: 800; background: #00e5ff; color: #040814; padding: 6px 14px; border-radius: 8px; }

  .stack-grid { display: flex; flex-direction: column; flex: 1; margin: 12px 0; justify-content: space-between; gap: 10px; }
  .layer-box { background: rgba(15, 23, 42, 0.95); border-radius: 12px; padding: 16px 20px; display: flex; flex-direction: column; justify-content: space-between; flex: 1; }
  .l-amber  { border: 2.5px solid #ff9100; box-shadow: 0 0 18px rgba(255, 145, 0, 0.4); }
  .l-cyan   { border: 2.5px solid #00e5ff; box-shadow: 0 0 18px rgba(0, 229, 255, 0.4); }
  .l-green  { border: 2.5px solid #00e676; box-shadow: 0 0 18px rgba(0, 230, 118, 0.4); }
  .l-purple { border: 2.5px solid #e040fb; box-shadow: 0 0 18px rgba(224, 64, 251, 0.4); }
  .l-red    { border: 2.5px solid #ff1744; box-shadow: 0 0 18px rgba(255, 23, 68, 0.4); }

  .layer-head { display: flex; align-items: center; justify-content: space-between; }
  .l-name { font-size: 22px; font-weight: 900; letter-spacing: 0.5px; }
  .l-amber  .l-name { color: #ff9100; }
  .l-cyan   .l-name { color: #00e5ff; }
  .l-green  .l-name { color: #00e676; }
  .l-purple .l-name { color: #e040fb; }
  .l-red    .l-name { color: #ff5252; }

  .file-code { font-family: 'Fira Code', monospace; font-size: 13px; font-weight: 800; background: #040814; color: #facc15; padding: 5px 12px; border-radius: 6px; border: 1px solid rgba(250,204,21,0.4); }
  .l-body-text { font-size: 16px; color: #e2e8f0; font-weight: 700; line-height: 1.35; margin: 4px 0; }
  .pills-bar { display: flex; gap: 8px; flex-wrap: wrap; }
  .badge-pill { font-size: 12px; font-weight: 800; padding: 5px 12px; border-radius: 6px; background: #040814; color: #fff; border: 1.5px solid rgba(255,255,255,0.3); }

  .footer-bar { background: #0d1733; border: 2px solid #00e5ff; border-radius: 12px; padding: 14px 22px; display: flex; align-items: center; justify-content: space-between; }
  .f-box { display: flex; flex-direction: column; }
  .f-val { font-size: 22px; font-weight: 900; color: #00e5ff; }
  .f-lbl { font-size: 11px; color: #facc15; font-weight: 800; text-transform: uppercase; }
</style>
</head>
<body>
  <div class="outer-frame">
    <div class="header">
      <div class="h-title">CORE SYSTEM ARCHITECTURE • <span>LINKEDIN AUTOMATION</span></div>
      <div class="h-badge">STEP 1 BASE DIAGRAM</div>
    </div>
    <div class="stack-grid">
      <div class="layer-box l-amber">
        <div class="layer-head"><div class="l-name">📱 1. CLIENT & INTERFACE LAYER</div><div class="file-code">web/ + check_approvals.py</div></div>
        <div class="l-body-text">Slack mobile webhooks for 1-tap connection approval + live SQLite Web UI dashboard review queue.</div>
        <div class="pills-bar"><span class="badge-pill">📱 SLACK MOBILE WEBHOOK</span><span class="badge-pill">⚡ 1-TAP PHONE APPROVAL</span><span class="badge-pill">💻 LIVE SQLITE WEB UI</span></div>
      </div>
      <div class="layer-box l-cyan">
        <div class="layer-head"><div class="l-name">🔌 2. PROTOCOL GATEWAY LAYER</div><div class="file-code">.mcp.json + mcp_server.py</div></div>
        <div class="l-body-text">Stdio RPC Gateway orchestrating mcp-server-linkedin (Playwright browser protocol) & mcp-post-studio.</div>
        <div class="pills-bar"><span class="badge-pill">🔌 STDIO JSON-RPC 2.0</span><span class="badge-pill">⚙️ MCP SERVER HUB</span><span class="badge-pill">🎨 POST STUDIO MCP</span></div>
      </div>
      <div class="layer-box l-green">
        <div class="layer-head"><div class="l-name">🔍 3. CORE AUTOMATION SERVICES</div><div class="file-code">daily-discovery.ps1 + watch-accepts.ps1</div></div>
        <div class="l-body-text">Autonomous Playwright scraper ingests target roles daily, filtering duplicates and sending stealth pitches.</div>
        <div class="pills-bar"><span class="badge-pill">🌐 PLAYWRIGHT CHROMIUM</span><span class="badge-pill">🔍 DAILY SCRAPER</span><span class="badge-pill">✉️ STEALTH CV SENDER</span></div>
      </div>
      <div class="layer-box l-purple">
        <div class="layer-head"><div class="l-name">🎨 4. AI & VISUAL CREATOR ENGINE</div><div class="file-code">image_studio.py + post_generator.py</div></div>
        <div class="l-body-text">Renders 8k photorealistic visual content via FLUX.1 & Google Imagen 3 visual studio engines.</div>
        <div class="pills-bar"><span class="badge-pill">🖼️ FLUX.1 ENGINE</span><span class="badge-pill">🧠 GOOGLE IMAGEN 3 API</span><span class="badge-pill">✍️ DYNAMIC COPYWRITER</span></div>
      </div>
      <div class="layer-box l-red">
        <div class="layer-head"><div class="l-name">💾 5. DATA & STORAGE LAYER</div><div class="file-code">board_db.py + notion_push.py</div></div>
        <div class="l-body-text">Persistent Local SQLite3 DB synced bi-directionally with Notion Cloud Board for state tracking.</div>
        <div class="pills-bar"><span class="badge-pill">📊 NOTION REST API</span><span class="badge-pill">💾 SQLITE3 DB</span><span class="badge-pill">🔄 TWO-WAY SYNC</span></div>
      </div>
    </div>
    <div class="footer-bar">
      <div class="f-box"><div class="f-val">100% Ban-Safe</div><div class="f-lbl">Human-in-the-Loop</div></div>
      <div class="f-box"><div class="f-val">&lt; 50ms Latency</div><div class="f-lbl">Stdio RPC Gateway</div></div>
      <div class="f-box"><div class="f-val">62 Jobs</div><div class="f-lbl">Discovered</div></div>
      <div class="f-box"><div class="f-val">10x Output</div><div class="f-lbl">Interview Rate</div></div>
    </div>
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

def execute_2step_pipeline():
    os.makedirs(IMAGES_DIR, exist_ok=True)
    os.makedirs(CAROUSEL_POST1_DIR, exist_ok=True)
    os.makedirs(CAROUSEL_POST2_DIR, exist_ok=True)

    print("=================================================================")
    print("[2-Step AI Pipeline] STEP 1: Rendering Base Clean Architecture Diagram...")
    print("=================================================================")
    step1_path = os.path.join(IMAGES_DIR, "step1_clean_base_architecture.png")
    render_edge_screenshot(STEP1_BASE_HTML, step1_path)
    print(f"[OK] Step 1 Base Architecture Diagram Rendered: {step1_path}")

    print("\n=================================================================")
    print("[2-Step AI Pipeline] STEP 2: Generating 3D Command Center AI Visual via FLUX.1...")
    print("=================================================================")

    # Generate Post 1 3D Command Center Hero Image
    print("\nGenerating 3D AI Command Center Visual for Post 1 (Job Hunt Autopilot)...")
    p1_prompt = (
        'A cinematic 3D Pixar-style sci-fi command center architecture diagram on a dark slate cybernetic background (#030712). '
        'At the top, the title "AUTONOMOUS JOB HUNT AUTOPILOT" glows in bright cyan neon text. '
        'On the left side: A 3D Pixar-style human developer in a hoodie standing looking at the command center with determination. '
        'On the right side: A sleek glowing futuristic AI robot agent standing with a digital HUD tablet operating the recruitment system. '
        'In the center: A giant glowing cyan and orange neon cybernetic control center screen displaying 5 stacked architecture layers with clear labels: '
        '"1. CLIENT & SLACK APPROVAL GATE", "2. AUTOMATED DISCOVERY ENGINE", "3. AI RESEARCH & CV TAILORING", "4. TWO-STAGE OUTREACH DISPATCH", "5. STATE STORE & TRACKING ENGINE". '
        'Background features glowing circuit lines, HUD telemetry widgets with "62 JOBS" and "0 BOUNCES" stats, blue and orange ambient lighting, aspect ratio 4:5, 8k resolution, 3D digital render.'
    )
    p1_meta = create_high_res_image(prompt=p1_prompt, aspect_ratio="4:5", filename="post1_slide_1_hero.png")
    p1_path = os.path.join(CAROUSEL_POST1_DIR, "post1_slide_1_hero.png")
    print(f"[OK] Step 2 Post 1 3D AI Command Center Generated: {p1_meta['file_path']}")

    # Generate Post 2 3D Command Center Hero Image
    print("\nGenerating 3D AI Command Center Visual for Post 2 (AI Content Studio)...")
    p2_prompt = (
        'A cinematic 3D Pixar-style sci-fi command center architecture diagram on a dark slate cybernetic background (#030712). '
        'At the top, the title "AI VISUAL CONTENT STUDIO" glows in bright cyan neon text. '
        'On the left side: A 3D Pixar-style human developer in a hoodie standing looking at the command center with determination. '
        'On the right side: A sleek glowing futuristic AI robot agent standing with a digital HUD tablet operating the content studio engine. '
        'In the center: A giant glowing cyan and purple neon cybernetic control center screen displaying 5 stacked architecture layers with clear labels: '
        '"1. LLM PROOF COPYWRITER", "2. EDGE VECTOR RENDERER", "3. FLUX.1 & IMAGEN 3 ENGINE", "4. 4-SLIDE CAROUSEL PACKAGER", "5. STDIO RPC MCP GATEWAY". '
        'Background features glowing circuit lines, HUD telemetry widgets with "8K HIGH-RES" and "MCP PROTOCOL" stats, blue and purple ambient lighting, aspect ratio 4:5, 8k resolution, 3D digital render.'
    )
    p2_meta = create_high_res_image(prompt=p2_prompt, aspect_ratio="4:5", filename="slide_1_hero_command_center.png")
    p2_path = os.path.join(CAROUSEL_POST2_DIR, "slide_1_hero_command_center.png")
    print(f"[OK] Step 2 Post 2 3D AI Command Center Generated: {p2_meta['file_path']}")

    print("\n=================================================================")
    print("[SUCCESS] 2-STEP AI 3D COMMAND CENTER PIPELINE COMPLETE!")
    print("=================================================================")

if __name__ == "__main__":
    execute_2step_pipeline()
