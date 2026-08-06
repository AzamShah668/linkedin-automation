"""
Render High-Density, Ultra-Detailed Technical Architecture Visual (Slide 2 Upgrade).
Fills the 1080x1350 canvas with deep technical specifications, component files, protocol details, and zero dead space.
"""

import os
import sys
import subprocess
import time

DEFAULT_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "output", "posts", "images")
EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

SLIDE2_ULTRA_TECHNICAL_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@700;800;900&family=Fira+Code:wght@600;700&display=swap');
  
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    width: 1080px;
    height: 1350px;
    background: #030712;
    background-image: 
      radial-gradient(circle at 50% 0%, rgba(0, 229, 255, 0.18) 0%, transparent 65%),
      radial-gradient(circle at 50% 100%, rgba(255, 145, 0, 0.15) 0%, transparent 65%),
      linear-gradient(rgba(0, 229, 255, 0.04) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0, 229, 255, 0.04) 1px, transparent 1px);
    background-size: 100% 100%, 100% 100%, 32px 32px, 32px 32px;
    font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
    color: #ffffff;
    display: flex;
    flex-direction: column;
    padding: 32px;
    justify-content: space-between;
    overflow: hidden;
  }

  /* Outer Cyber Container */
  .outer-frame {
    border: 3px solid #00e5ff;
    box-shadow: 0 0 35px rgba(0, 229, 255, 0.3), inset 0 0 20px rgba(0, 229, 255, 0.1);
    border-radius: 20px;
    padding: 24px;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    background: rgba(6, 11, 24, 0.95);
  }

  /* Header Box */
  .header-banner {
    background: rgba(15, 23, 42, 0.95);
    border: 2px solid #00e5ff;
    box-shadow: 0 0 20px rgba(0, 229, 255, 0.35);
    border-radius: 14px;
    padding: 14px 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .header-title-group {
    display: flex;
    flex-direction: column;
  }
  .h-badge {
    font-family: 'Fira Code', monospace;
    font-size: 12px;
    font-weight: 800;
    color: #ff9100;
    letter-spacing: 1.5px;
    text-transform: uppercase;
  }
  .h-title {
    font-size: 30px;
    font-weight: 900;
    letter-spacing: 0.5px;
    color: #ffffff;
  }
  .h-title span {
    color: #00e5ff;
    text-shadow: 0 0 10px rgba(0, 229, 255, 0.8);
  }
  .h-right-tag {
    background: rgba(0, 229, 255, 0.15);
    border: 1px solid #00e5ff;
    color: #00e5ff;
    font-family: 'Fira Code', monospace;
    font-size: 12px;
    font-weight: 700;
    padding: 6px 14px;
    border-radius: 8px;
  }

  /* 5 Full-Width Stack Containers */
  .stack-container {
    display: flex;
    flex-direction: column;
    gap: 10px;
    flex: 1;
    margin: 14px 0;
    justify-content: space-between;
  }

  .layer-block {
    background: rgba(15, 23, 42, 0.95);
    border-radius: 14px;
    padding: 14px 18px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .l-orange { border: 2px solid #ff9100; box-shadow: 0 0 14px rgba(255, 145, 0, 0.3); }
  .l-cyan   { border: 2px solid #00e5ff; box-shadow: 0 0 14px rgba(0, 229, 255, 0.3); }
  .l-green  { border: 2px solid #00e676; box-shadow: 0 0 14px rgba(0, 230, 118, 0.3); }
  .l-purple { border: 2px solid #d500f9; box-shadow: 0 0 14px rgba(213, 0, 249, 0.3); }
  .l-red    { border: 2px solid #ff1744; box-shadow: 0 0 14px rgba(255, 23, 68, 0.3); }

  .layer-row-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .layer-title-text {
    font-size: 17px;
    font-weight: 900;
    letter-spacing: 0.5px;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .l-orange .layer-title-text { color: #ff9100; }
  .l-cyan   .layer-title-text { color: #00e5ff; }
  .l-green  .layer-title-text { color: #00e676; }
  .l-purple .layer-title-text { color: #e040fb; }
  .l-red    .layer-title-text { color: #ff5252; }

  .layer-file-pill {
    font-family: 'Fira Code', monospace;
    font-size: 11px;
    font-weight: 700;
    background: #030712;
    padding: 3px 10px;
    border-radius: 6px;
    color: #cbd5e1;
    border: 1px solid rgba(255, 255, 255, 0.15);
  }

  .layer-desc-text {
    font-size: 13px;
    color: #cbd5e1;
    font-weight: 600;
    line-height: 1.35;
  }

  .tech-pills-row {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }
  .tpill {
    font-size: 11px;
    font-weight: 800;
    padding: 4px 10px;
    border-radius: 6px;
    background: #090e18;
  }
  .l-orange .tpill { border: 1px solid #ff9100; color: #ffffff; }
  .l-cyan   .tpill { border: 1px solid #00e5ff; color: #ffffff; }
  .l-green  .tpill { border: 1px solid #00e676; color: #ffffff; }
  .l-purple .tpill { border: 1px solid #d500f9; color: #ffffff; }
  .l-red    .tpill { border: 1px solid #ff1744; color: #ffffff; }

  .flow-divider {
    text-align: center;
    margin: -5px 0;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .flow-badge {
    font-family: 'Fira Code', monospace;
    font-size: 10px;
    font-weight: 700;
    background: #030712;
    border: 1px solid rgba(0, 229, 255, 0.4);
    color: #00e5ff;
    padding: 2px 10px;
    border-radius: 8px;
  }

  /* Bottom Specs Footer */
  .footer-specs {
    background: rgba(15, 23, 42, 0.95);
    border: 1px solid rgba(0, 229, 255, 0.3);
    border-radius: 12px;
    padding: 12px 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .spec-box { display: flex; flex-direction: column; }
  .spec-val { font-size: 17px; font-weight: 900; color: #00e5ff; }
  .spec-lbl { font-size: 10px; color: #94a3b8; font-weight: 700; text-transform: uppercase; }
</style>
</head>
<body>

  <div class="outer-frame">
    <!-- Header -->
    <div class="header-banner">
      <div class="header-title-group">
        <div class="h-badge">SLIDE 02 • SYSTEM SPECIFICATIONS</div>
        <div class="h-title">5-LAYER <span>CORE ARCHITECTURE</span></div>
      </div>
      <div class="h-right-tag">STDIO RPC PROTOCOL</div>
    </div>

    <!-- 5 Full-Width Layers Stack -->
    <div class="stack-container">

      <!-- LAYER 1 -->
      <div class="layer-block l-orange">
        <div class="layer-row-top">
          <div class="layer-title-text">📱 1. CLIENT & INTERFACE LAYER</div>
          <div class="layer-file-pill">web/ + check_approvals.py</div>
        </div>
        <div class="layer-desc-text">
          <b>Human-in-the-Loop Safeguard:</b> Mobile phone Slack webhooks for 1-tap connection approval + SQLite web UI dashboard for pitch review.
        </div>
        <div class="tech-pills-row">
          <span class="tpill">SLACK WEBHOOK API</span>
          <span class="tpill">MOBILE 1-TAP APPROVAL</span>
          <span class="tpill">SQLITE WEB UI</span>
        </div>
      </div>

      <div class="flow-divider"><span class="flow-badge">REST API / SLACK WEBHOOK ↓</span></div>

      <!-- LAYER 2 -->
      <div class="layer-block l-cyan">
        <div class="layer-row-top">
          <div class="layer-title-text">🔌 2. PROTOCOL GATEWAY LAYER</div>
          <div class="layer-file-pill">.mcp.json + mcp_server.py</div>
        </div>
        <div class="layer-desc-text">
          <b>Stdio RPC Protocol Gateway:</b> Orchestrates `mcp-server-linkedin` (Playwright automation) & `mcp-post-studio` (FLUX.1 content creation).
        </div>
        <div class="tech-pills-row">
          <span class="tpill">STDIO JSON-RPC 2.0</span>
          <span class="tpill">MCP SERVER HUB</span>
          <span class="tpill">POST STUDIO MCP</span>
        </div>
      </div>

      <div class="flow-divider"><span class="flow-badge">STDIO RPC PROTOCOL ↓</span></div>

      <!-- LAYER 3 -->
      <div class="layer-block l-green">
        <div class="layer-row-top">
          <div class="layer-title-text">🔍 3. CORE AUTOMATION SERVICES</div>
          <div class="layer-file-pill">daily-discovery.ps1 + watch-accepts.ps1</div>
        </div>
        <div class="layer-desc-text">
          <b>Autonomous Playwright Services:</b> Ingests target LinkedIn job listings & recruiter contacts daily, filtering duplicates and sending stealth pitches.
        </div>
        <div class="tech-pills-row">
          <span class="tpill">PLAYWRIGHT CHROMIUM</span>
          <span class="tpill">DAILY SCRAPER</span>
          <span class="tpill">STEALTH CV SENDER</span>
        </div>
      </div>

      <div class="flow-divider"><span class="flow-badge">PLAYWRIGHT BROWSER ENGINE ↓</span></div>

      <!-- LAYER 4 -->
      <div class="layer-block l-purple">
        <div class="layer-row-top">
          <div class="layer-title-text">🎨 4. AI & VISUAL CREATOR ENGINE</div>
          <div class="layer-file-pill">image_studio.py + post_generator.py</div>
        </div>
        <div class="layer-desc-text">
          <b>Deep Learning Visual Studio:</b> Renders 8k photorealistic content visuals via FLUX.1 (Pollinations REST API) & Google Imagen 3 for daily LinkedIn posts.
        </div>
        <div class="tech-pills-row">
          <span class="tpill">FLUX.1 ENGINE</span>
          <span class="tpill">GOOGLE IMAGEN 3 API</span>
          <span class="tpill">DYNAMIC COPYWRITER</span>
        </div>
      </div>

      <div class="flow-divider"><span class="flow-badge">SQLITE3 & NOTION SYNC ↓</span></div>

      <!-- LAYER 5 -->
      <div class="layer-block l-red">
        <div class="layer-row-top">
          <div class="layer-title-text">💾 5. DATA & STORAGE LAYER</div>
          <div class="layer-file-pill">board_db.py + notion_push.py</div>
        </div>
        <div class="layer-desc-text">
          <b>Persistent State Management:</b> Local SQLite3 DB synced bi-directionally with Notion Cloud Board, storing lead stages, timestamps & post packages.
        </div>
        <div class="tech-pills-row">
          <span class="tpill">NOTION REST API</span>
          <span class="tpill">SQLITE3 DB</span>
          <span class="tpill">TWO-WAY SYNC</span>
          <span class="tpill">JSON ARTIFACTS</span>
        </div>
      </div>

    </div>

    <!-- Specs Footer -->
    <div class="footer-specs">
      <div class="spec-box">
        <div class="spec-val">100% Ban-Safe</div>
        <div class="spec-lbl">Human-in-the-Loop</div>
      </div>
      <div class="spec-box">
        <div class="spec-val">&lt; 50ms Latency</div>
        <div class="spec-lbl">Stdio RPC Gateway</div>
      </div>
      <div class="spec-box">
        <div class="spec-val">100% Free</div>
        <div class="spec-lbl">FLUX.1 Visual Studio</div>
      </div>
      <div class="spec-box">
        <div class="spec-val">10x Output</div>
        <div class="spec-lbl">Interview Rate</div>
      </div>
    </div>
  </div>

</body>
</html>
"""

def render_image():
    os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)
    temp_html = os.path.join(DEFAULT_OUTPUT_DIR, "temp_slide2.html")
    output_png = os.path.join(DEFAULT_OUTPUT_DIR, "masterpiece_command_center_architecture.png")

    with open(temp_html, "w", encoding="utf-8") as f:
        f.write(SLIDE2_ULTRA_TECHNICAL_HTML)

    cmd = [
        EDGE_PATH,
        "--headless",
        "--disable-gpu",
        "--window-size=1080,1350",
        "--hide-scrollbars",
        f"--screenshot={output_png}",
        temp_html
    ]

    subprocess.run(cmd, check=True)
    if os.path.exists(temp_html):
        os.remove(temp_html)
    print(f"[OK] Upgraded Slide 2 rendered to: {output_png}")

if __name__ == "__main__":
    render_image()
