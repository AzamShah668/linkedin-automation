"""
Unified LinkedIn Post Generator — Full Platform Showcase
Generates a single, complete 4-slide carousel post that covers the ENTIRE
LinkedIn Automation Platform (Job Hunt Autopilot + AI Content Studio).

Outputs:
  output/posts/unified_post/slide_1_hero.png
  output/posts/unified_post/slide_2_architecture.png
  output/posts/unified_post/slide_3_comparison.png
  output/posts/unified_post/slide_4_roadmap.png
  output/posts/unified_post/unified_post_package.json
"""

import os
import sys
import json
import time
import shutil
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
POST_CREATOR_DIR = os.path.join(PROJECT_ROOT, "tools", "post_creator")
sys.path.insert(0, POST_CREATOR_DIR)

from image_studio import create_high_res_image

OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output", "posts", "unified_post")
IMAGES_DIR = os.path.join(PROJECT_ROOT, "output", "posts", "images")
EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

# ─────────────────────────────────────────────────────────
# SLIDE 1: 3D Hero (AI-generated base + vector HTML overlay)
# ─────────────────────────────────────────────────────────

SLIDE1_HERO_PROMPT = """Pixar-style 3D rendered futuristic command center scene, dark navy blue background.
On the LEFT a male software engineer in a sleek futuristic suit standing confidently, arms crossed.
In the CENTER a massive glowing holographic screen displaying a vertical stack of 5 neon-bordered panels: amber, cyan, green, purple, red. Each panel has a small icon and short label.
On the RIGHT a tall sleek humanoid AI robot with glowing cyan eyes holding a transparent tablet, looking at the central screen.
The scene has floating holographic HUD elements, circuit board traces on the floor glowing cyan, dark atmospheric lighting with volumetric light rays. Ultra-detailed Octane render quality. No text anywhere, purely visual scene. The holographic panels should be blank colored rectangles without any text or symbols inside them."""

SLIDE1_OVERLAY_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@700;800;900&family=Fira+Code:wght@700;800&display=swap');
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
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
  }}

  .outer-frame {{
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
  }}

  .header {{
    background: #0d1733;
    border: 2.5px solid #00e5ff;
    box-shadow: 0 0 25px rgba(0, 229, 255, 0.4);
    border-radius: 14px;
    padding: 18px 24px;
    text-align: center;
  }}
  .h-sub {{ font-family: 'Fira Code', monospace; font-size: 14px; font-weight: 800; color: #facc15; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 4px; }}
  .h-title {{ font-size: 34px; font-weight: 900; color: #fff; letter-spacing: -0.5px; }}
  .h-title span {{ color: #00e5ff; text-shadow: 0 0 16px rgba(0,229,255,0.9); }}

  .artwork-container {{
    width: 100%;
    flex: 1;
    margin: 14px 0;
    border-radius: 16px;
    overflow: hidden;
    border: 2.5px solid #00e5ff;
    box-shadow: 0 0 30px rgba(0, 229, 255, 0.35);
    position: relative;
  }}
  .art-img {{ width: 100%; height: 100%; object-fit: cover; }}

  .overlay-badge {{
    position: absolute;
    background: rgba(4, 8, 20, 0.88);
    border-radius: 10px;
    padding: 8px 16px;
    font-family: 'Fira Code', monospace;
    font-size: 13px;
    font-weight: 800;
    backdrop-filter: blur(8px);
  }}
  .badge-tl {{ top: 16px; left: 16px; border: 1.5px solid #00e5ff; color: #00e5ff; }}
  .badge-tr {{ top: 16px; right: 16px; border: 1.5px solid #facc15; color: #facc15; }}
  .badge-bl {{ bottom: 16px; left: 16px; border: 1.5px solid #e040fb; color: #e040fb; }}
  .badge-br {{ bottom: 16px; right: 16px; border: 1.5px solid #00e676; color: #00e676; }}

  .stats-banner {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin-bottom: 4px;
  }}
  .stat-card {{
    background: rgba(15, 23, 42, 0.95);
    border: 2px solid #00e5ff;
    border-radius: 12px;
    padding: 12px;
    text-align: center;
    box-shadow: 0 0 15px rgba(0, 229, 255, 0.25);
  }}
  .sc-val {{ font-size: 22px; font-weight: 900; color: #00e5ff; }}
  .sc-lbl {{ font-size: 11px; font-weight: 800; color: #facc15; text-transform: uppercase; margin-top: 2px; }}

  .footer-cta {{
    background: linear-gradient(90deg, #1e1b4b, #311b92);
    border: 2.5px solid #818cf8;
    border-radius: 14px;
    padding: 14px;
    text-align: center;
    font-size: 18px;
    font-weight: 900;
    color: #c7d2fe;
    letter-spacing: 0.5px;
  }}
</style>
</head>
<body>
  <div class="outer-frame">
    <div class="header">
      <div class="h-sub">⚡ FULL PLATFORM ARCHITECTURE</div>
      <div class="h-title">I AUTOMATED MY <span>ENTIRE LINKEDIN</span></div>
    </div>

    <div class="artwork-container">
      <img src="file:///{art_path}" class="art-img" alt="3D Command Center">
      <div class="overlay-badge badge-tl">🤖 AI AGENT OPERATED</div>
      <div class="overlay-badge badge-tr">🛡️ 100% BAN-SAFE</div>
      <div class="overlay-badge badge-bl">🎨 FLUX.1 VISUAL ENGINE</div>
      <div class="overlay-badge badge-br">⚡ 5 SCHEDULED TASKS</div>
    </div>

    <div class="stats-banner">
      <div class="stat-card"><div class="sc-val">62 Jobs</div><div class="sc-lbl">Discovered</div></div>
      <div class="stat-card"><div class="sc-val">5 Applied</div><div class="sc-lbl">Submitted</div></div>
      <div class="stat-card"><div class="sc-val">0 Bounces</div><div class="sc-lbl">Verified Mail</div></div>
      <div class="stat-card"><div class="sc-val">~2 min</div><div class="sc-lbl">Human Effort</div></div>
    </div>

    <div class="footer-cta">🚀 JOB HUNT AUTOPILOT + AI CONTENT STUDIO • ONE PLATFORM</div>
  </div>
</body>
</html>"""

# ─────────────────────────────────────────────────────────
# SLIDE 2: Unified 5-Layer Architecture Specs Card
# ─────────────────────────────────────────────────────────

SLIDE2_HTML = """<!DOCTYPE html>
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
  .h-title { font-size: 28px; font-weight: 900; color: #fff; letter-spacing: -0.5px; }
  .h-title span { color: #00e5ff; text-shadow: 0 0 12px rgba(0,229,255,0.9); }
  .h-tag { font-family: 'Fira Code', monospace; font-size: 12px; font-weight: 800; background: #00e5ff; color: #040814; padding: 6px 14px; border-radius: 8px; }
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

  .file-code { font-family: 'Fira Code', monospace; font-size: 11px; font-weight: 700; background: #040814; color: #facc15; padding: 4px 10px; border-radius: 6px; border: 1px solid rgba(250,204,21,0.4); }
  .l-body-text { font-size: 14.5px; color: #e2e8f0; font-weight: 600; line-height: 1.35; margin: 4px 0; }
  .pills-bar { display: flex; gap: 8px; flex-wrap: wrap; }
  .badge-pill { font-size: 11px; font-weight: 800; padding: 4px 10px; border-radius: 6px; background: #040814; }
  .l-amber  .badge-pill { border: 1.5px solid #ff9100; color: #fff; }
  .l-cyan   .badge-pill { border: 1.5px solid #00e5ff; color: #fff; }
  .l-green  .badge-pill { border: 1.5px solid #00e676; color: #fff; }
  .l-purple .badge-pill { border: 1.5px solid #e040fb; color: #fff; }
  .l-red    .badge-pill { border: 1.5px solid #ff1744; color: #fff; }

  .footer-bar { background: #0d1733; border: 2px solid #00e5ff; border-radius: 12px; padding: 12px 20px; display: flex; align-items: center; justify-content: space-between; }
  .f-box { display: flex; flex-direction: column; }
  .f-val { font-size: 18px; font-weight: 900; color: #00e5ff; }
  .f-lbl { font-size: 10px; color: #facc15; font-weight: 800; text-transform: uppercase; }
</style>
</head>
<body>
  <div class="bg-sym s-bulb">💡</div>
  <div class="bg-sym s-gear1">⚙️</div>
  <div class="bg-sym s-code">&lt;/&gt;</div>
  <div class="bg-sym s-gear2">⚙️</div>
  <div class="outer-frame">
    <div class="header">
      <div class="h-title">SLIDE 02 • <span>THE FULL STACK</span></div>
      <div class="h-tag">5-LAYER DEEP DIVE</div>
    </div>
    <div class="stack-grid">
      <div class="layer-box l-amber">
        <div class="layer-head"><div class="l-name">📱 1. CLIENT & APPROVAL GATE</div><div class="file-code">web/ + check_approvals.py</div></div>
        <div class="l-body-text"><b>Human-in-the-Loop:</b> Slack mobile webhooks for 1-tap approval + live SQLite web dashboard. Nothing sends without your explicit tap.</div>
        <div class="pills-bar"><span class="badge-pill">📱 SLACK MOBILE WEBHOOK</span><span class="badge-pill">⚡ 1-TAP APPROVAL</span><span class="badge-pill">💻 LIVE SQLITE WEB UI</span></div>
      </div>
      <div class="layer-box l-cyan">
        <div class="layer-head"><div class="l-name">🔌 2. MCP PROTOCOL GATEWAY</div><div class="file-code">.mcp.json + mcp_server.py</div></div>
        <div class="l-body-text"><b>Stdio RPC Hub:</b> Orchestrates mcp-server-linkedin (Playwright browser), mcp-post-studio (FLUX.1 visuals), and all tool dispatch.</div>
        <div class="pills-bar"><span class="badge-pill">🔌 STDIO JSON-RPC 2.0</span><span class="badge-pill">⚙️ MCP SERVER HUB</span><span class="badge-pill">🎨 POST STUDIO MCP</span></div>
      </div>
      <div class="layer-box l-green">
        <div class="layer-head"><div class="l-name">🔍 3. AUTOMATION ENGINES</div><div class="file-code">daily-discovery.ps1 + flush-approved.ps1</div></div>
        <div class="l-body-text"><b>Job Hunt + Content Pipelines:</b> Daily job scraping, CV tailoring, stealth outreach dispatch, AND 4-slide carousel generation — all scheduled.</div>
        <div class="pills-bar"><span class="badge-pill">🌐 PLAYWRIGHT CHROMIUM</span><span class="badge-pill">🔍 DAILY SCRAPER</span><span class="badge-pill">✉️ STEALTH SENDER</span><span class="badge-pill">🖼️ CAROUSEL GEN</span></div>
      </div>
      <div class="layer-box l-purple">
        <div class="layer-head"><div class="l-name">🎨 4. AI VISUAL & COPY ENGINE</div><div class="file-code">image_studio.py + post_generator.py</div></div>
        <div class="l-body-text"><b>Dual AI Render Studio:</b> FLUX.1 (Pollinations) + Google Imagen 3 for 8K visuals. Dynamic copywriter generates post text from real project data.</div>
        <div class="pills-bar"><span class="badge-pill">🖼️ FLUX.1 ENGINE</span><span class="badge-pill">🧠 GOOGLE IMAGEN 3</span><span class="badge-pill">✍️ AI COPYWRITER</span></div>
      </div>
      <div class="layer-box l-red">
        <div class="layer-head"><div class="l-name">💾 5. STATE & TRACKING LAYER</div><div class="file-code">board_db.py + notion_push.py</div></div>
        <div class="l-body-text"><b>Persistent State:</b> SQLite3 DB synced bi-directionally with Notion Cloud Board. Tracks lead stages, follow-ups, post packages, and invite status.</div>
        <div class="pills-bar"><span class="badge-pill">📊 NOTION REST API</span><span class="badge-pill">💾 SQLITE3 DB</span><span class="badge-pill">🔄 TWO-WAY SYNC</span><span class="badge-pill">📈 INVITE TRACKER</span></div>
      </div>
    </div>
    <div class="footer-bar">
      <div class="f-box"><div class="f-val">62 Jobs Found</div><div class="f-lbl">Automated Discovery</div></div>
      <div class="f-box"><div class="f-val">0 Bounces</div><div class="f-lbl">Verified Delivery</div></div>
      <div class="f-box"><div class="f-val">100% Free</div><div class="f-lbl">No Cloud Bills</div></div>
      <div class="f-box"><div class="f-val">Ban-Safe</div><div class="f-lbl">Human-in-the-Loop</div></div>
    </div>
  </div>
</body>
</html>"""

# ─────────────────────────────────────────────────────────
# SLIDE 3: Dual 3D Character Avatars
# ─────────────────────────────────────────────────────────

SLIDE3_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@700;800;900&family=Fira+Code:wght@700&display=swap');
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: 1080px;
    height: 1350px;
    background: #040814;
    font-family: 'Plus Jakarta Sans', sans-serif;
    color: #ffffff;
    display: flex;
    flex-direction: column;
    padding: 24px;
    justify-content: space-between;
    overflow: hidden;
    position: relative;
  }}
  .bg-sym {{ position: absolute; opacity: 0.35; z-index: 1; }}
  .s-bulb {{ top: 30px; right: 30px; font-size: 56px; opacity: 0.9; filter: drop-shadow(0 0 20px #facc15); }}
  .s-gear {{ bottom: 40px; left: 30px; font-size: 48px; }}
  .outer-frame {{ border: 3px solid #facc15; box-shadow: 0 0 40px rgba(250, 204, 21, 0.4); border-radius: 20px; padding: 20px; height: 100%; display: flex; flex-direction: column; justify-content: space-between; background: rgba(6, 12, 28, 0.95); position: relative; z-index: 2; }}
  .header {{ text-align: center; margin-bottom: 10px; }}
  .tag {{ display: inline-block; background: rgba(250, 204, 21, 0.2); border: 2px solid #facc15; color: #facc15; font-size: 13px; font-weight: 900; padding: 5px 16px; border-radius: 14px; letter-spacing: 1px; }}
  .title {{ font-size: 34px; font-weight: 900; color: #fff; margin-top: 4px; }}
  .title span {{ color: #facc15; text-shadow: 0 0 12px rgba(250,204,21,0.8); }}
  .grid-cols {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; flex: 1; margin: 8px 0; }}
  .col-card {{ border-radius: 16px; padding: 18px; display: flex; flex-direction: column; justify-content: space-between; height: 100%; }}
  .col-old {{ background: #0d1527; border: 2.5px solid #ff1744; box-shadow: 0 0 20px rgba(255, 23, 68, 0.3); }}
  .col-new {{ background: #091a30; border: 2.5px solid #00e5ff; box-shadow: 0 0 25px rgba(0, 229, 255, 0.4); }}
  .c-header {{ font-size: 18px; font-weight: 900; padding: 10px; border-radius: 10px; text-align: center; margin-bottom: 12px; text-transform: uppercase; }}
  .col-old .c-header {{ background: rgba(255, 23, 68, 0.25); color: #ff5252; border: 1.5px solid #ff1744; }}
  .col-new .c-header {{ background: #00e5ff; color: #040814; text-shadow: none; }}
  .avatar-container {{ width: 100%; height: 200px; border-radius: 12px; overflow: hidden; margin-bottom: 14px; border: 2px solid rgba(255,255,255,0.2); display: flex; align-items: center; justify-content: center; }}
  .avatar-img {{ width: 100%; height: 100%; object-fit: cover; }}
  .c-list {{ list-style: none; display: flex; flex-direction: column; gap: 10px; }}
  .c-item {{ display: flex; align-items: center; gap: 10px; font-size: 15px; font-weight: 700; line-height: 1.25; }}
  .ibox {{ width: 34px; height: 34px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 16px; flex-shrink: 0; }}
  .col-old .ibox {{ background: rgba(255, 23, 68, 0.2); color: #ff5252; }}
  .col-new .ibox {{ background: rgba(0, 229, 255, 0.2); color: #00e5ff; }}
  .status-box {{ border-radius: 10px; padding: 12px; text-align: center; margin-top: 10px; }}
  .col-old .status-box {{ background: #1e293b; color: #ff5252; border: 1.5px solid #ff1744; }}
  .col-new .status-box {{ background: #00e5ff; color: #040814; font-weight: 900; }}
  .status-box h5 {{ font-size: 11px; text-transform: uppercase; letter-spacing: 1px; }}
  .status-box p {{ font-size: 16px; font-weight: 900; margin-top: 2px; }}
  .banner {{ background: linear-gradient(90deg, #1e1b4b, #311b92); border: 2px solid #818cf8; border-radius: 14px; padding: 14px; text-align: center; font-size: 17px; font-weight: 900; color: #fff; }}
</style>
</head>
<body>
  <div class="bg-sym s-bulb">💡</div>
  <div class="bg-sym s-gear">⚙️</div>
  <div class="outer-frame">
    <div class="header">
      <div class="tag">SLIDE 03 • THE PARADIGM SHIFT</div>
      <div class="title">DOING IT MANUALLY VS <span>FULL AUTOPILOT</span></div>
    </div>
    <div class="grid-cols">
      <div class="col-card col-old">
        <div>
          <div class="c-header">The Old Way</div>
          <div class="avatar-container"><img src="file:///{stressed_path}" class="avatar-img" alt="Stressed Developer"></div>
          <div class="c-list">
            <div class="c-item"><div class="ibox">❌</div> 3-5 Hours Daily Manual Grind</div>
            <div class="c-item"><div class="ibox">❌</div> Copy-Paste Generic Outreach</div>
            <div class="c-item"><div class="ibox">❌</div> Messy Spreadsheet Tracking</div>
            <div class="c-item"><div class="ibox">❌</div> Generic Stock Image Posts</div>
            <div class="c-item"><div class="ibox">❌</div> Abysmal Reply Rates (< 2%)</div>
            <div class="c-item"><div class="ibox">❌</div> Zero Content Consistency</div>
          </div>
        </div>
        <div class="status-box"><h5>STATUS</h5><p>EXHAUSTING & UNPREDICTABLE</p></div>
      </div>
      <div class="col-card col-new">
        <div>
          <div class="c-header">Full Autopilot Platform</div>
          <div class="avatar-container"><img src="file:///{happy_path}" class="avatar-img" alt="Happy Automated Developer"></div>
          <div class="c-list">
            <div class="c-item"><div class="ibox">⚡</div> Autonomous Daily Job Scraping</div>
            <div class="c-item"><div class="ibox">🧠</div> AI-Tailored CV + Pitch Packets</div>
            <div class="c-item"><div class="ibox">📱</div> 1-Tap Phone Approval Gate</div>
            <div class="c-item"><div class="ibox">🎨</div> 8K AI Carousel Generator</div>
            <div class="c-item"><div class="ibox">✉️</div> Stealth Recruiter Outreach</div>
            <div class="c-item"><div class="ibox">🛡️</div> 100% Ban-Safe Architecture</div>
          </div>
        </div>
        <div class="status-box"><h5>STATUS</h5><p>10X OUTPUT & INTERVIEWS</p></div>
      </div>
    </div>
    <div class="banner">🚀 STOP GRINDING. BUILD SYSTEMS THAT COMPOUND YOUR CAREER.</div>
  </div>
</body>
</html>"""

# ─────────────────────────────────────────────────────────
# SLIDE 4: Operational Roadmap (5 Scheduled Tasks)
# ─────────────────────────────────────────────────────────

SLIDE4_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@700;800;900&family=Fira+Code:wght@700&display=swap');
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: 1080px;
    height: 1350px;
    background: #030712;
    background-image:
      radial-gradient(circle at 50% 0%, rgba(224, 64, 251, 0.35) 0%, transparent 60%),
      radial-gradient(circle at 50% 100%, rgba(0, 229, 255, 0.3) 0%, transparent 60%),
      linear-gradient(rgba(224, 64, 251, 0.06) 1.5px, transparent 1.5px),
      linear-gradient(90deg, rgba(224, 64, 251, 0.06) 1.5px, transparent 1.5px);
    background-size: 100% 100%, 100% 100%, 28px 28px, 28px 28px;
    font-family: 'Outfit', -apple-system, sans-serif;
    color: #ffffff;
    display: flex;
    flex-direction: column;
    padding: 24px;
    justify-content: space-between;
    overflow: hidden;
    position: relative;
  }}
  .bg-sym {{ position: absolute; opacity: 0.4; z-index: 1; pointer-events: none; font-weight: 900; }}
  .s-q1 {{ top: 30px; right: 35px; font-size: 64px; opacity: 0.9; filter: drop-shadow(0 0 20px #e040fb); color: #e040fb; }}
  .s-bulb {{ bottom: 40px; right: 40px; font-size: 58px; opacity: 0.85; filter: drop-shadow(0 0 20px #facc15); }}
  .s-q2 {{ bottom: 180px; left: 25px; font-size: 54px; color: #00e5ff; opacity: 0.85; filter: drop-shadow(0 0 15px #00e5ff); }}

  .outer-frame {{
    border: 3.5px solid #e040fb;
    box-shadow: 0 0 45px rgba(224, 64, 251, 0.5);
    border-radius: 20px;
    padding: 20px;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    background: rgba(6, 12, 28, 0.95);
    position: relative;
    z-index: 2;
  }}
  .header {{
    background: #140826;
    border: 2.5px solid #e040fb;
    box-shadow: 0 0 25px rgba(224, 64, 251, 0.45);
    border-radius: 14px;
    padding: 16px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }}
  .h-title {{ font-size: 32px; font-weight: 900; color: #fff; letter-spacing: -0.5px; }}
  .h-title span {{ color: #e040fb; text-shadow: 0 0 14px rgba(224,64,251,0.95); }}
  .h-badge {{ font-family: 'Fira Code', monospace; font-size: 13px; font-weight: 800; background: #e040fb; color: #040814; padding: 6px 14px; border-radius: 8px; }}

  .robot-flow-banner {{
    width: 100%;
    height: 210px;
    border-radius: 14px;
    overflow: hidden;
    margin: 8px 0;
    border: 2.5px solid #00e5ff;
    box-shadow: 0 0 25px rgba(0, 229, 255, 0.4);
    display: flex;
    align-items: center;
    justify-content: center;
    background: #000;
  }}
  .robot-img {{ width: 100%; height: 100%; object-fit: cover; }}

  .roadmap-stack {{
    display: flex;
    flex-direction: column;
    gap: 7px;
    flex: 1;
    justify-content: space-between;
  }}

  .step-card {{
    background: rgba(15, 23, 42, 0.95);
    border-radius: 14px;
    padding: 14px 20px;
    display: flex;
    align-items: center;
    gap: 18px;
    flex: 1;
  }}
  .sc-1 {{ border: 2.5px solid #00e5ff; box-shadow: 0 0 14px rgba(0, 229, 255, 0.35); }}
  .sc-2 {{ border: 2.5px solid #e040fb; box-shadow: 0 0 14px rgba(224, 64, 251, 0.35); }}
  .sc-3 {{ border: 2.5px solid #00e676; box-shadow: 0 0 14px rgba(0, 230, 118, 0.35); }}
  .sc-4 {{ border: 2.5px solid #facc15; box-shadow: 0 0 14px rgba(250, 204, 21, 0.35); }}
  .sc-5 {{ border: 2.5px solid #ff9100; box-shadow: 0 0 14px rgba(255, 145, 0, 0.35); }}

  .s-num {{
    font-family: 'Fira Code', monospace;
    font-size: 24px;
    font-weight: 900;
    width: 52px;
    height: 52px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }}
  .n1 {{ background: #00e5ff; color: #040814; }}
  .n2 {{ background: #e040fb; color: #040814; }}
  .n3 {{ background: #00e676; color: #040814; }}
  .n4 {{ background: #facc15; color: #040814; }}
  .n5 {{ background: #ff9100; color: #040814; }}

  .s-details {{ display: flex; flex-direction: column; gap: 2px; flex: 1; }}
  .s-head-row {{ display: flex; align-items: center; justify-content: space-between; }}
  .s-title {{ font-size: 20px; font-weight: 900; color: #fff; }}
  .sc-1 .s-title {{ color: #00e5ff; }}
  .sc-2 .s-title {{ color: #e040fb; }}
  .sc-3 .s-title {{ color: #00e676; }}
  .sc-4 .s-title {{ color: #facc15; }}
  .sc-5 .s-title {{ color: #ff9100; }}

  .s-tag {{ font-family: 'Fira Code', monospace; font-size: 11px; font-weight: 800; background: #040814; padding: 3px 8px; border-radius: 6px; border: 1.5px solid rgba(255,255,255,0.25); color: #fff; }}
  .s-desc {{ font-size: 14px; color: #e2e8f0; font-weight: 700; line-height: 1.3; }}
  .s-result {{ font-size: 13px; color: #00e676; font-weight: 800; }}

  .cta-banner {{
    background: #0d1733;
    border: 2.5px solid #00e5ff;
    box-shadow: 0 0 25px rgba(0, 229, 255, 0.45);
    border-radius: 14px;
    padding: 14px;
    text-align: center;
    font-size: 18px;
    font-weight: 900;
    color: #00e5ff;
    letter-spacing: 0.5px;
  }}
</style>
</head>
<body>
  <div class="bg-sym s-q1">❓</div>
  <div class="bg-sym s-bulb">💡</div>
  <div class="bg-sym s-q2">❓</div>

  <div class="outer-frame">
    <div class="header">
      <div class="h-title">SLIDE 04 • <span>5 SCHEDULED TASKS</span></div>
      <div class="h-badge">RUNS WHILE YOU SLEEP</div>
    </div>

    <div class="robot-flow-banner">
      <img src="file:///{robot_path}" class="robot-img" alt="Robot Flowchart">
    </div>

    <div class="roadmap-stack">
      <div class="step-card sc-1">
        <div class="s-num n1">01</div>
        <div class="s-details">
          <div class="s-head-row">
            <div class="s-title">🔍 Daily Job Discovery</div>
            <div class="s-tag">DAILY 08:00</div>
          </div>
          <div class="s-desc">Scrapes DevOps + AI roles, dedupes, scores, pushes to Notion + Slack digest.</div>
          <div class="s-result">RESULT: Board grew 24 → 62 jobs in one run</div>
        </div>
      </div>
      <div class="step-card sc-2">
        <div class="s-num n2">02</div>
        <div class="s-details">
          <div class="s-head-row">
            <div class="s-title">📤 Flush Approved Queue</div>
            <div class="s-tag">EVERY 30 MIN</div>
          </div>
          <div class="s-desc">Drains Slack ✅ queue. Sends bare connection requests (throttled, jittered, capped).</div>
          <div class="s-result">RESULT: 3 outreach dispatched, 0 bans</div>
        </div>
      </div>
      <div class="step-card sc-3">
        <div class="s-num n3">03</div>
        <div class="s-details">
          <div class="s-head-row">
            <div class="s-title">👁️ Watch Accepts</div>
            <div class="s-tag">EVERY 4 HOURS</div>
          </div>
          <div class="s-desc">Detects connection accept → waits 3-20h → auto-sends tailored CV + pitch.</div>
          <div class="s-result">RESULT: Swaleha Pathan (Innova ESI) accepted</div>
        </div>
      </div>
      <div class="step-card sc-4">
        <div class="s-num n4">04</div>
        <div class="s-details">
          <div class="s-head-row">
            <div class="s-title">📧 Reply & Bounce Check</div>
            <div class="s-tag">4X / DAY</div>
          </div>
          <div class="s-desc">Gmail read-only scan for recruiter replies and bounces across all domains.</div>
          <div class="s-result">RESULT: 0 bounces — all 3 emails delivered</div>
        </div>
      </div>
      <div class="step-card sc-5">
        <div class="s-num n5">05</div>
        <div class="s-details">
          <div class="s-head-row">
            <div class="s-title">📦 Sweep & Build Packets</div>
            <div class="s-tag">EVERY 6 HOURS</div>
          </div>
          <div class="s-desc">Drains unprocessed board rows. Builds tailored CV + outreach packet, max 2/cycle.</div>
          <div class="s-result">RESULT: 4 packets built, 56 in queue</div>
        </div>
      </div>
    </div>

    <div class="cta-banner">⚡ 5 TASKS • 0 CLOUD BILLS • RUNS ON YOUR LAPTOP WHILE YOU SLEEP</div>
  </div>
</body>
</html>"""


# ═════════════════════════════════════════════════════════
# POST COPY
# ═════════════════════════════════════════════════════════

POST_BODY = """I automated my entire LinkedIn — job hunting, recruiter outreach, content creation, and posting — with one platform that runs while I sleep.

Here is the full architecture:

THE PROBLEM:
I was spending 3+ hours a day on LinkedIn manually — scrolling job boards, copy-pasting the same CV everywhere, writing generic outreach messages, and posting content with stock images. The reply rate was below 2%. The burnout was real.

So I stopped doing it manually and engineered a system instead.

WHAT IT DOES:

🔍 ENGINE 1: JOB HUNT AUTOPILOT
→ Scheduled task fires at 08:00 every morning
→ Scrapes target DevOps + AI/MLOps roles via Playwright
→ Deduplicates against 62 board rows, scores each role 0-100
→ AI reads the JD, researches the company, generates a tailored CV
→ Drafts personalized recruiter pitch (email + LinkedIn message)
→ Everything hits my Slack queue — I tap ✅ on my phone to approve
→ Nothing sends without that tap. Ever.
→ Connection accepted? → Waits 3-20 hours → sends full CV + pitch automatically

🎨 ENGINE 2: AI CONTENT STUDIO
→ Takes any engineering topic as input
→ Generates LinkedIn post copy in a proven 5-part framework
→ Renders 4-slide visual carousel with FLUX.1 + Imagen 3 (8K resolution)
→ Packages everything into a ready-to-publish bundle via MCP protocol
→ This very post and its carousel were generated by this system

THE HARD ENGINEERING PROBLEMS:
• Browser profile lock: 3 Chromium instances fighting for one LinkedIn session. Cost me an hour debugging fake "session expired" errors.
• Headless permission cliff: Claude running unattended silently refuses any tool not in the allowlist. 58 entries now.
• AI text rendering: AI image generators produce gibberish text. Solved with hybrid HTML vector overlays on 3D backgrounds.
• Ban safety: Randomized jitter on every action, daily caps, no headless scraping. Zero bans in 30+ days.

THE STACK:
5 Windows Scheduled Tasks • 2 MCP Protocol Servers • Playwright Chromium • SQLite3 + Notion DB • Slack Webhooks • FLUX.1 + Imagen 3 • Python + PowerShell

RESULTS:
→ 62 jobs discovered automatically
→ 5 applications submitted
→ 3 tailored CVs delivered to real recruiters (0 bounces)
→ 4-slide carousels generated in under 60 seconds
→ Total human effort per application: ~2 minutes of phone review
→ Total cloud bill: $0. Runs entirely on my laptop.

The whole thing is 39 scripts, 5 scheduled tasks, and zero excuses.

What repetitive workflow are you still doing manually? Drop it in the comments — I'll tell you how I'd automate it.

#SoftwareEngineering #Automation #AI #Python #LinkedIn #JobSearch #MCP #SystemDesign #DevOps #CareerGrowth"""


# ═════════════════════════════════════════════════════════
# RENDERING PIPELINE
# ═════════════════════════════════════════════════════════

def render_edge_screenshot(html_string: str, output_png_path: str):
    """Render HTML to PNG via Edge headless."""
    temp_html = os.path.join(OUTPUT_DIR, f"temp_{int(time.time())}.html")
    with open(temp_html, "w", encoding="utf-8") as f:
        f.write(html_string)
    cmd = [EDGE_PATH, "--headless", "--disable-gpu", "--window-size=1080,1350",
           "--hide-scrollbars", f"--screenshot={output_png_path}", temp_html]
    subprocess.run(cmd, check=True, capture_output=True)
    if os.path.exists(temp_html):
        os.remove(temp_html)


def generate_slide1_hero():
    """Generate 3D artwork via FLUX.1, then overlay vector text."""
    print("\n[Slide 1/4] Generating 3D base artwork via FLUX.1...")

    # Check if existing art is usable
    existing_art = os.path.join(IMAGES_DIR, "ai_robot_human_command_center_diagram.png")
    if os.path.exists(existing_art) and os.path.getsize(existing_art) > 500000:
        print(f"  → Reusing existing high-quality 3D artwork: {existing_art}")
        art_path = existing_art
    else:
        result = create_high_res_image(
            prompt=SLIDE1_HERO_PROMPT,
            aspect_ratio="4:5",
            engine="auto",
            output_dir=IMAGES_DIR,
            filename="unified_command_center_3d.png",
            style_preset="3d-render"
        )
        art_path = result["file_path"]
        print(f"  → 3D artwork generated: {art_path}")

    print("  → Overlaying vector text badges via Edge HTML...")
    art_path_fwd = art_path.replace("\\", "/")
    s1_html = SLIDE1_OVERLAY_HTML.format(art_path=art_path_fwd)
    s1_path = os.path.join(OUTPUT_DIR, "slide_1_hero.png")
    render_edge_screenshot(s1_html, s1_path)
    print(f"  ✓ Slide 1 complete: {s1_path}")
    return s1_path


def generate_slide2_architecture():
    """Render the unified 5-layer architecture specs card."""
    print("\n[Slide 2/4] Rendering 5-Layer Architecture Specs Card (Space Grotesk)...")
    s2_path = os.path.join(OUTPUT_DIR, "slide_2_architecture.png")
    render_edge_screenshot(SLIDE2_HTML, s2_path)
    print(f"  ✓ Slide 2 complete: {s2_path}")
    return s2_path


def generate_slide3_comparison():
    """Render before vs after comparison with 3D avatars."""
    print("\n[Slide 3/4] Rendering Before vs After Comparison (Dual 3D Avatars)...")
    stressed_img = os.path.join(IMAGES_DIR, "stressed_manual_job_hunter.png")
    happy_img = os.path.join(IMAGES_DIR, "happy_automated_job_hunter.png")

    # Generate avatars if missing
    if not os.path.exists(stressed_img) or os.path.getsize(stressed_img) < 100000:
        print("  → Generating 'Stressed Developer' avatar...")
        create_high_res_image(
            prompt="3D Pixar-style frustrated male software developer sitting at desk surrounded by 40 open browser tabs, empty coffee cups, papers scattered everywhere, blue screen errors on monitors, stressed exhausted facial expression, cluttered messy dark office, dramatic moody lighting, highly detailed Octane render",
            aspect_ratio="1:1", output_dir=IMAGES_DIR, filename="stressed_manual_job_hunter.png", style_preset="3d-render"
        )

    if not os.path.exists(happy_img) or os.path.getsize(happy_img) < 100000:
        print("  → Generating 'Happy Developer' avatar...")
        create_high_res_image(
            prompt="3D Pixar-style confident happy male software developer relaxing in modern bright office, holding glowing tablet showing green checkmarks and interview success stats, clean organized desk, warm natural lighting, smiling expression, robot assistant in background, highly detailed Octane render",
            aspect_ratio="1:1", output_dir=IMAGES_DIR, filename="happy_automated_job_hunter.png", style_preset="3d-render"
        )

    stressed_path = stressed_img.replace("\\", "/")
    happy_path = happy_img.replace("\\", "/")
    s3_html = SLIDE3_HTML.format(stressed_path=stressed_path, happy_path=happy_path)
    s3_path = os.path.join(OUTPUT_DIR, "slide_3_comparison.png")
    render_edge_screenshot(s3_html, s3_path)
    print(f"  ✓ Slide 3 complete: {s3_path}")
    return s3_path


def generate_slide4_roadmap():
    """Render operational roadmap with 3D robot flowchart banner."""
    print("\n[Slide 4/4] Rendering 5-Task Operational Roadmap (Outfit + 3D Robot)...")
    robot_img = os.path.join(IMAGES_DIR, "roadmap_execution_robot_flow.png")

    if not os.path.exists(robot_img) or os.path.getsize(robot_img) < 100000:
        print("  → Generating 3D Robot Flowchart visual...")
        create_high_res_image(
            prompt="3D Pixar-style futuristic AI robot engineer standing in front of glowing neon holographic 4-step execution flowchart, data ingest to analysis to execution to result checkmark, dark command center background, cyan and purple neon lighting, highly detailed Octane render, no text",
            aspect_ratio="16:9", output_dir=IMAGES_DIR, filename="roadmap_execution_robot_flow.png", style_preset="3d-render"
        )

    robot_path = robot_img.replace("\\", "/")
    s4_html = SLIDE4_HTML.format(robot_path=robot_path)
    s4_path = os.path.join(OUTPUT_DIR, "slide_4_roadmap.png")
    render_edge_screenshot(s4_html, s4_path)
    print(f"  ✓ Slide 4 complete: {s4_path}")
    return s4_path


def package_post(slide_paths: dict):
    """Bundle everything into a ready-to-post JSON package."""
    timestamp = int(time.time())
    package = {
        "post_id": f"unified_full_platform_{timestamp}",
        "post_title": "I Automated My Entire LinkedIn",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "post_body": POST_BODY,
        "carousel_slides": [
            {"slide": 1, "file": slide_paths["slide_1"], "desc": "3D Command Center Hero — Full Platform Overview"},
            {"slide": 2, "file": slide_paths["slide_2"], "desc": "Space Grotesk 5-Layer Architecture Deep Dive"},
            {"slide": 3, "file": slide_paths["slide_3"], "desc": "Before vs After — Manual Grind vs Full Autopilot"},
            {"slide": 4, "file": slide_paths["slide_4"], "desc": "5 Scheduled Tasks — Runs While You Sleep"},
        ],
        "status": "ready_to_post",
        "hashtags": "#SoftwareEngineering #Automation #AI #Python #LinkedIn #JobSearch #MCP #SystemDesign #DevOps #CareerGrowth"
    }
    pkg_path = os.path.join(OUTPUT_DIR, "unified_post_package.json")
    with open(pkg_path, "w", encoding="utf-8") as f:
        json.dump(package, f, indent=2, ensure_ascii=False)
    print(f"\n  ✓ Package saved: {pkg_path}")
    return pkg_path


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("=" * 70)
    print(" UNIFIED LINKEDIN POST GENERATOR — FULL PLATFORM SHOWCASE")
    print("=" * 70)

    s1 = generate_slide1_hero()
    s2 = generate_slide2_architecture()
    s3 = generate_slide3_comparison()
    s4 = generate_slide4_roadmap()

    slides = {"slide_1": s1, "slide_2": s2, "slide_3": s3, "slide_4": s4}
    pkg = package_post(slides)

    print("\n" + "=" * 70)
    print(" ✅ ALL 4 SLIDES + PACKAGE GENERATED SUCCESSFULLY")
    print(f" Output Directory: {OUTPUT_DIR}")
    print("=" * 70)

    return slides


if __name__ == "__main__":
    main()
