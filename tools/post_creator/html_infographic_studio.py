"""
HTML/CSS 3D Isometric Neon Architecture Infographic Generator
"""

import os
import sys
import subprocess
import time

DEFAULT_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "output", "posts", "images")
EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

ISOMETRIC_3D_STACKED_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@700;800;900&family=Fira+Code:wght@700&display=swap');
  
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    width: 1080px;
    height: 1350px;
    background: #090e18;
    font-family: 'Plus Jakarta Sans', sans-serif;
    color: #ffffff;
    display: flex;
    flex-direction: column;
    padding: 32px;
    justify-content: space-between;
    overflow: hidden;
  }

  /* Outer Boundary Frame */
  .frame {
    border: 2px solid rgba(0, 229, 255, 0.4);
    box-shadow: 0 0 30px rgba(0, 229, 255, 0.2);
    border-radius: 24px;
    padding: 24px;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    background: #0d1322;
  }

  /* Header Box */
  .header {
    background: rgba(15, 23, 42, 0.9);
    border: 2px solid #00e5ff;
    box-shadow: 0 0 20px rgba(0, 229, 255, 0.4);
    border-radius: 16px;
    padding: 14px;
    text-align: center;
  }
  .title {
    font-size: 32px;
    font-weight: 900;
    letter-spacing: 1px;
    color: #ffffff;
  }
  .title span {
    color: #00e5ff;
    text-shadow: 0 0 10px rgba(0, 229, 255, 0.8);
  }

  /* Stack */
  .stack {
    display: flex;
    flex-direction: column;
    gap: 8px;
    flex: 1;
    justify-content: space-between;
    margin: 16px 0;
  }

  .layer {
    background: #111a2e;
    border-radius: 18px;
    padding: 16px 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: relative;
  }

  .layer-orange { border: 2px solid #ff9100; box-shadow: 0 0 20px rgba(255, 145, 0, 0.3); }
  .layer-cyan { border: 2px solid #00e5ff; box-shadow: 0 0 20px rgba(0, 229, 255, 0.3); }
  .layer-green { border: 2px solid #00e676; box-shadow: 0 0 20px rgba(0, 230, 118, 0.3); }
  .layer-purple { border: 2px solid #d500f9; box-shadow: 0 0 20px rgba(213, 0, 249, 0.3); }
  .layer-red { border: 2px solid #ff1744; box-shadow: 0 0 20px rgba(255, 23, 68, 0.3); }

  .left-info {
    max-width: 320px;
  }
  .layer-title {
    font-size: 20px;
    font-weight: 900;
    letter-spacing: 0.5px;
  }
  .layer-orange .layer-title { color: #ff9100; }
  .layer-cyan .layer-title { color: #00e5ff; }
  .layer-green .layer-title { color: #00e676; }
  .layer-purple .layer-title { color: #e040fb; }
  .layer-red .layer-title { color: #ff5252; }

  .layer-sub {
    font-size: 13px;
    color: #94a3b8;
    font-weight: 600;
    margin-top: 2px;
  }

  /* Center 3D Icon Badge */
  .center-3d-badge {
    position: absolute;
    top: 50%;
    left: 45%;
    transform: translate(-50%, -50%);
    width: 64px;
    height: 64px;
    border-radius: 16px;
    background: #0f172a;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 32px;
    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.5);
  }
  .layer-orange .center-3d-badge { border: 2px solid #ff9100; }
  .layer-cyan .center-3d-badge { border: 2px solid #00e5ff; }
  .layer-green .center-3d-badge { border: 2px solid #00e676; }
  .layer-purple .center-3d-badge { border: 2px solid #d500f9; }
  .layer-red .center-3d-badge { border: 2px solid #ff1744; }

  /* Right Buttons */
  .right-buttons {
    display: flex;
    gap: 10px;
  }
  .btn {
    background: #090e18;
    padding: 10px 16px;
    border-radius: 10px;
    font-size: 13px;
    font-weight: 800;
    letter-spacing: 0.5px;
  }
  .layer-orange .btn { border: 1.5px solid #ff9100; color: #ffffff; }
  .layer-cyan .btn { border: 1.5px solid #00e5ff; color: #ffffff; }
  .layer-green .btn { border: 1.5px solid #00e676; color: #ffffff; }
  .layer-purple .btn { border: 1.5px solid #d500f9; color: #ffffff; }
  .layer-red .btn { border: 1.5px solid #ff1744; color: #ffffff; }

  /* Connecting Pipeline Flow */
  .flow {
    text-align: center;
    margin: -4px 0;
    z-index: 5;
  }
  .flow-tag {
    font-family: 'Fira Code', monospace;
    font-size: 11px;
    font-weight: 700;
    background: #090e18;
    border: 1px solid rgba(255, 255, 255, 0.25);
    color: #00e5ff;
    padding: 2px 10px;
    border-radius: 10px;
  }
</style>
</head>
<body>

  <div class="frame">
    <div class="header">
      <div class="title">HOW IT WORKS: <span>THE CORE ARCHITECTURE</span></div>
    </div>

    <div class="stack">

      <!-- LAYER 1 -->
      <div class="layer layer-orange">
        <div class="left-info">
          <div class="layer-title">CLIENT & INTERFACE</div>
          <div class="layer-sub">Human-in-the-Loop mobile approval & live dashboard control.</div>
        </div>
        <div class="center-3d-badge">📱</div>
        <div class="right-buttons">
          <div class="btn">MOBILE PHONE APP</div>
          <div class="btn">LIVE DASHBOARD</div>
        </div>
      </div>

      <div class="flow"><span class="flow-tag">REST / SLACK WEBHOOK ↓</span></div>

      <!-- LAYER 2 -->
      <div class="layer layer-cyan">
        <div class="left-info">
          <div class="layer-title">PROTOCOL GATEWAY</div>
          <div class="layer-sub">Centralized MCP Server & Agent Protocol orchestration.</div>
        </div>
        <div class="center-3d-badge">🖥️</div>
        <div class="right-buttons">
          <div class="btn">MCP SERVER HUB</div>
          <div class="btn">POST STUDIO MCP</div>
        </div>
      </div>

      <div class="flow"><span class="flow-tag">STDIO RPC / IPC ↓</span></div>

      <!-- LAYER 3 -->
      <div class="layer layer-green">
        <div class="left-info">
          <div class="layer-title">CORE SERVICES</div>
          <div class="layer-sub">Autonomous background scrapers, Playwright, & pipeline runners.</div>
        </div>
        <div class="center-3d-badge">🔍</div>
        <div class="right-buttons">
          <div class="btn">DAILY DISCOVERY</div>
          <div class="btn">STEALTH SENDER</div>
        </div>
      </div>

      <div class="flow"><span class="flow-tag">PLAYWRIGHT / API ↓</span></div>

      <!-- LAYER 4 -->
      <div class="layer layer-purple">
        <div class="left-info">
          <div class="layer-title">AI & VISUAL CREATOR</div>
          <div class="layer-sub">Deep learning high res image rendering & post copy generation.</div>
        </div>
        <div class="center-3d-badge">🧠</div>
        <div class="right-buttons">
          <div class="btn">FLUX.1 ENGINE</div>
          <div class="btn">IMAGEN 3 API</div>
        </div>
      </div>

      <div class="flow"><span class="flow-tag">SQLITE / REST ↓</span></div>

      <!-- LAYER 5 -->
      <div class="layer layer-red">
        <div class="left-info">
          <div class="layer-title">DATA STORAGE</div>
          <div class="layer-sub">Persistent lead state, SQLite DB, Notion cloud sync, & artifacts.</div>
        </div>
        <div class="center-3d-badge">🛢️</div>
        <div class="right-buttons">
          <div class="btn">NOTION DATABASE</div>
          <div class="btn">SQLITE3 DB</div>
        </div>
      </div>

    </div>
  </div>

</body>
</html>
"""

def render_html_to_png(html_content: str, output_filename: str) -> str:
    """Renders HTML string into high-res PNG image via headless Edge."""
    os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)
    temp_html_path = os.path.join(DEFAULT_OUTPUT_DIR, f"temp_{int(time.time())}.html")
    output_png_path = os.path.join(DEFAULT_OUTPUT_DIR, output_filename)

    with open(temp_html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    cmd = [
        EDGE_PATH,
        "--headless",
        "--disable-gpu",
        "--window-size=1080,1350",
        "--hide-scrollbars",
        f"--screenshot={output_png_path}",
        temp_html_path
    ]

    subprocess.run(cmd, check=True)

    if os.path.exists(temp_html_path):
        os.remove(temp_html_path)

    return output_png_path

if __name__ == "__main__":
    print("[Infographic Studio] Rendering 3D Isometric Stacked Card Architecture...")
    res_path = render_html_to_png(ISOMETRIC_3D_STACKED_HTML, "infographic_3d_stacked_cards.png")
    print(f"[OK] Saved to: {res_path}")
