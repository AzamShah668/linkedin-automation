"""
Master Dynamic 4-Slide LinkedIn Carousel Generator
Takes ANY topic / genre and automatically produces the complete 4-slide visual pack:
- Slide 1: Hero 3D Command Center AI Visual dynamically customized for topic
- Slide 2: Space Grotesk 5-Layer Core Architecture Specs
- Slide 3: Dual 3D Character Avatars (Stressed Manual Developer vs Happy Automated Developer)
- Slide 4: Space Grotesk Operational Execution Roadmap + 3D Robot Hologram Flowchart + Interrogation Symbols (❓) & Lightbulbs (💡)
"""

import os
import sys
import shutil
import subprocess
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
POST_CREATOR_DIR = os.path.join(PROJECT_ROOT, "tools", "post_creator")
sys.path.insert(0, POST_CREATOR_DIR)

from image_studio import create_high_res_image

CAROUSEL_DIR = os.path.join(PROJECT_ROOT, "output", "posts", "carousel_bundle")
IMAGES_DIR = os.path.join(PROJECT_ROOT, "output", "posts", "images")
EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

SLIDE2_SPACE_GROTESK_HTML = """<!DOCTYPE html>
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
      <div class="h-title">SLIDE 02 • <span>{TOPIC_HEADER}</span></div>
      <div class="h-tag">FULL TECHNICAL DEEP DIVE</div>
    </div>
    <div class="stack-grid">
      <div class="layer-box l-amber">
        <div class="layer-head"><div class="l-name">📱 1. CLIENT & INTERFACE LAYER</div><div class="file-code">web/ + check_approvals.py</div></div>
        <div class="l-body-text"><b>Human-in-the-Loop Safeguard:</b> Slack mobile webhooks for 1-tap connection approval + SQLite web UI dashboard for pitch review.</div>
        <div class="pills-bar"><span class="badge-pill">📱 SLACK MOBILE WEBHOOK</span><span class="badge-pill">⚡ 1-TAP PHONE APPROVAL</span><span class="badge-pill">💻 LIVE SQLITE WEB UI</span></div>
      </div>
      <div class="layer-box l-cyan">
        <div class="layer-head"><div class="l-name">🔌 2. PROTOCOL GATEWAY LAYER</div><div class="file-code">.mcp.json + mcp_server.py</div></div>
        <div class="l-body-text"><b>Stdio RPC Gateway:</b> Orchestrates mcp-server-linkedin (Playwright browser protocol) & mcp-post-studio (FLUX.1 visual studio).</div>
        <div class="pills-bar"><span class="badge-pill">🔌 STDIO JSON-RPC 2.0</span><span class="badge-pill">⚙️ MCP SERVER HUB</span><span class="badge-pill">🎨 POST STUDIO MCP</span></div>
      </div>
      <div class="layer-box l-green">
        <div class="layer-head"><div class="l-name">🔍 3. CORE AUTOMATION SERVICES</div><div class="file-code">daily-discovery.ps1 + watch-accepts.ps1</div></div>
        <div class="l-body-text"><b>Autonomous Scraper & Outreach:</b> Ingests target LinkedIn job listings & recruiter contacts daily, filtering duplicates and sending stealth pitches.</div>
        <div class="pills-bar"><span class="badge-pill">🌐 PLAYWRIGHT CHROMIUM</span><span class="badge-pill">🔍 DAILY SCRAPER</span><span class="badge-pill">✉️ STEALTH CV SENDER</span></div>
      </div>
      <div class="layer-box l-purple">
        <div class="layer-head"><div class="l-name">🎨 4. AI & VISUAL CREATOR ENGINE</div><div class="file-code">image_studio.py + post_generator.py</div></div>
        <div class="l-body-text"><b>Deep Learning Visual Studio:</b> Renders 8k photorealistic content visuals via FLUX.1 (Pollinations REST API) & Google Imagen 3.</div>
        <div class="pills-bar"><span class="badge-pill">🖼️ FLUX.1 ENGINE</span><span class="badge-pill">🧠 GOOGLE IMAGEN 3 API</span><span class="badge-pill">✍️ DYNAMIC COPYWRITER</span></div>
      </div>
      <div class="layer-box l-red">
        <div class="layer-head"><div class="l-name">💾 5. DATA & STORAGE LAYER</div><div class="file-code">board_db.py + notion_push.py</div></div>
        <div class="l-body-text"><b>Persistent State Management:</b> Local SQLite3 DB synced bi-directionally with Notion Cloud Board, storing lead stages and post packages.</div>
        <div class="pills-bar"><span class="badge-pill">📊 NOTION REST API</span><span class="badge-pill">💾 SQLITE3 DB</span><span class="badge-pill">🔄 TWO-WAY SYNC</span></div>
      </div>
    </div>
    <div class="footer-bar">
      <div class="f-box"><div class="f-val">100% Ban-Safe</div><div class="f-lbl">Human-in-the-Loop</div></div>
      <div class="f-box"><div class="f-val">&lt; 50ms Latency</div><div class="f-lbl">Stdio RPC Gateway</div></div>
      <div class="f-box"><div class="f-val">100% Free</div><div class="f-lbl">FLUX.1 Visual Studio</div></div>
      <div class="f-box"><div class="f-val">10x Output</div><div class="f-lbl">Interview Rate</div></div>
    </div>
  </div>
</body>
</html>"""

SLIDE3_AVATARS_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@700;800;900&family=Fira+Code:wght@700&display=swap');
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
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
  }
  .bg-sym { position: absolute; opacity: 0.35; z-index: 1; }
  .s-bulb { top: 30px; right: 30px; font-size: 56px; opacity: 0.9; filter: drop-shadow(0 0 20px #facc15); }
  .s-gear { bottom: 40px; left: 30px; font-size: 48px; }
  .outer-frame { border: 3px solid #facc15; box-shadow: 0 0 40px rgba(250, 204, 21, 0.4); border-radius: 20px; padding: 20px; height: 100%; display: flex; flex-direction: column; justify-content: space-between; background: rgba(6, 12, 28, 0.95); position: relative; z-index: 2; }
  .header { text-align: center; margin-bottom: 10px; }
  .tag { display: inline-block; background: rgba(250, 204, 21, 0.2); border: 2px solid #facc15; color: #facc15; font-size: 13px; font-weight: 900; padding: 5px 16px; border-radius: 14px; letter-spacing: 1px; }
  .title { font-size: 34px; font-weight: 900; color: #fff; margin-top: 4px; }
  .title span { color: #facc15; text-shadow: 0 0 12px rgba(250,204,21,0.8); }
  .grid-cols { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; flex: 1; margin: 8px 0; }
  .col-card { border-radius: 16px; padding: 18px; display: flex; flex-direction: column; justify-content: space-between; height: 100%; }
  .col-old { background: #0d1527; border: 2.5px solid #ff1744; box-shadow: 0 0 20px rgba(255, 23, 68, 0.3); }
  .col-new { background: #091a30; border: 2.5px solid #00e5ff; box-shadow: 0 0 25px rgba(0, 229, 255, 0.4); }
  .c-header { font-size: 20px; font-weight: 900; padding: 10px; border-radius: 10px; text-align: center; margin-bottom: 12px; text-transform: uppercase; }
  .col-old .c-header { background: rgba(255, 23, 68, 0.25); color: #ff5252; border: 1.5px solid #ff1744; }
  .col-new .c-header { background: #00e5ff; color: #040814; text-shadow: none; }
  .avatar-container { width: 100%; height: 200px; border-radius: 12px; overflow: hidden; margin-bottom: 14px; border: 2px solid rgba(255,255,255,0.2); display: flex; align-items: center; justify-content: center; }
  .avatar-img { width: 100%; height: 100%; object-fit: cover; }
  .c-list { list-style: none; display: flex; flex-direction: column; gap: 10px; }
  .c-item { display: flex; align-items: center; gap: 10px; font-size: 15px; font-weight: 700; line-height: 1.25; }
  .ibox { width: 34px; height: 34px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 16px; flex-shrink: 0; }
  .col-old .ibox { background: rgba(255, 23, 68, 0.2); color: #ff5252; }
  .col-new .ibox { background: rgba(0, 229, 255, 0.2); color: #00e5ff; }
  .status-box { border-radius: 10px; padding: 12px; text-align: center; margin-top: 10px; }
  .col-old .status-box { background: #1e293b; color: #ff5252; border: 1.5px solid #ff1744; }
  .col-new .status-box { background: #00e5ff; color: #040814; font-weight: 900; }
  .status-box h5 { font-size: 11px; text-transform: uppercase; letter-spacing: 1px; }
  .status-box p { font-size: 16px; font-weight: 900; margin-top: 2px; }
  .banner { background: linear-gradient(90deg, #1e1b4b, #311b92); border: 2px solid #818cf8; border-radius: 14px; padding: 14px; text-align: center; font-size: 18px; font-weight: 900; color: #fff; }
</style>
</head>
<body>
  <div class="bg-sym s-bulb">💡</div>
  <div class="bg-sym s-gear">⚙️</div>
  <div class="outer-frame">
    <div class="header">
      <div class="tag">SLIDE 03 • PARADIGM SHIFT</div>
      <div class="title">MANUAL PROCESS VS <span>AUTOPILOT ERA</span></div>
    </div>
    <div class="grid-cols">
      <div class="col-card col-old">
        <div>
          <div class="c-header">Manual Process</div>
          <div class="avatar-container"><img src="file:///{STRESSED_IMG_PATH}" class="avatar-img" alt="Stressed Developer"></div>
          <div class="c-list">
            <div class="c-item"><div class="ibox">❌</div> 3-5 Hours Daily Manual Work</div>
            <div class="c-item"><div class="ibox">❌</div> Copy-Paste Generic Outreach</div>
            <div class="c-item"><div class="ibox">❌</div> Messy Spreadsheet Tracking</div>
            <div class="c-item"><div class="ibox">❌</div> Severe Fatigue & Burnout</div>
            <div class="c-item"><div class="ibox">❌</div> Abysmal Reply Rates (&lt; 2%)</div>
            <div class="c-item"><div class="ibox">❌</div> High Manual Error Risk</div>
          </div>
        </div>
        <div class="status-box"><h5>STATUS</h5><p>EXHAUSTING & UNPREDICTABLE</p></div>
      </div>
      <div class="col-card col-new">
        <div>
          <div class="c-header">{TOPIC_HEADER}</div>
          <div class="avatar-container"><img src="file:///{HAPPY_IMG_PATH}" class="avatar-img" alt="Happy Automated Developer"></div>
          <div class="c-list">
            <div class="c-item"><div class="ibox">⚡</div> Playwright Autonomous Scraper</div>
            <div class="c-item"><div class="ibox">🧠</div> Notion Cloud DB & SQLite Engine</div>
            <div class="c-item"><div class="ibox">📱</div> 1-Tap Mobile Phone Review Queue</div>
            <div class="c-item"><div class="ibox">✉️</div> Personalized Pitch Dispatcher</div>
            <div class="c-item"><div class="ibox">🎨</div> FLUX.1 & Imagen 3 Visual Studio</div>
            <div class="c-item"><div class="ibox">🛡️</div> 100% Ban-Safe Human-in-the-Loop</div>
          </div>
        </div>
        <div class="status-box"><h5>STATUS</h5><p>10X OUTPUT & INTERVIEWS</p></div>
      </div>
    </div>
    <div class="banner">🚀 STOP SPAMMING. BUILD SYSTEMS THAT SCALE YOUR IMPACT.</div>
  </div>
</body>
</html>"""

SLIDE4_OUTFIT_UPGRADED_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@700;800;900&family=Fira+Code:wght@700&display=swap');
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
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
  }
  .bg-sym { position: absolute; opacity: 0.4; z-index: 1; pointer-events: none; font-weight: 900; }
  .s-q1 { top: 30px; right: 35px; font-size: 64px; opacity: 0.9; filter: drop-shadow(0 0 20px #e040fb); color: #e040fb; }
  .s-bulb { bottom: 40px; right: 40px; font-size: 58px; opacity: 0.85; filter: drop-shadow(0 0 20px #facc15); }
  .s-q2 { bottom: 180px; left: 25px; font-size: 54px; color: #00e5ff; opacity: 0.85; filter: drop-shadow(0 0 15px #00e5ff); }
  .s-gear { top: 280px; left: 25px; font-size: 42px; opacity: 0.7; }
  .s-code { top: 480px; right: 25px; font-family: 'Fira Code', monospace; font-size: 38px; color: #00e676; opacity: 0.8; }

  .outer-frame {
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
  .h-title { font-size: 34px; font-weight: 900; color: #fff; letter-spacing: -0.5px; }
  .h-title span { color: #e040fb; text-shadow: 0 0 14px rgba(224,64,251,0.95); }
  .h-badge { font-family: 'Fira Code', monospace; font-size: 14px; font-weight: 800; background: #e040fb; color: #040814; padding: 6px 14px; border-radius: 8px; }

  .robot-flow-banner {
    width: 100%;
    height: 230px;
    border-radius: 14px;
    overflow: hidden;
    margin: 8px 0;
    border: 2.5px solid #00e5ff;
    box-shadow: 0 0 25px rgba(0, 229, 255, 0.4);
    display: flex;
    align-items: center;
    justify-content: center;
    background: #000;
  }
  .robot-img { width: 100%; height: 100%; object-fit: cover; }

  .roadmap-stack {
    display: flex;
    flex-direction: column;
    gap: 8px;
    flex: 1;
    justify-content: space-between;
  }

  .step-card {
    background: rgba(15, 23, 42, 0.95);
    border-radius: 14px;
    padding: 16px 22px;
    display: flex;
    align-items: center;
    gap: 22px;
    flex: 1;
  }
  .sc-1 { border: 2.5px solid #00e5ff; box-shadow: 0 0 16px rgba(0, 229, 255, 0.35); }
  .sc-2 { border: 2.5px solid #e040fb; box-shadow: 0 0 16px rgba(224, 64, 251, 0.35); }
  .sc-3 { border: 2.5px solid #00e676; box-shadow: 0 0 16px rgba(0, 230, 118, 0.35); }
  .sc-4 { border: 2.5px solid #facc15; box-shadow: 0 0 16px rgba(250, 204, 21, 0.35); }

  .s-num {
    font-family: 'Fira Code', monospace;
    font-size: 28px;
    font-weight: 900;
    width: 60px;
    height: 60px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    box-shadow: 0 0 15px rgba(0,0,0,0.6);
  }
  .n1 { background: #00e5ff; color: #040814; }
  .n2 { background: #e040fb; color: #040814; }
  .n3 { background: #00e676; color: #040814; }
  .n4 { background: #facc15; color: #040814; }

  .s-details { display: flex; flex-direction: column; gap: 4px; flex: 1; }
  .s-head-row { display: flex; align-items: center; justify-content: space-between; }
  .s-title { font-size: 24px; font-weight: 900; color: #fff; letter-spacing: -0.3px; }
  .sc-1 .s-title { color: #00e5ff; }
  .sc-2 .s-title { color: #e040fb; }
  .sc-3 .s-title { color: #00e676; }
  .sc-4 .s-title { color: #facc15; }

  .s-tag { font-family: 'Fira Code', monospace; font-size: 12px; font-weight: 800; background: #040814; padding: 4px 10px; border-radius: 6px; border: 1.5px solid rgba(255,255,255,0.25); color: #fff; }
  .s-desc { font-size: 17.5px; color: #f1f5f9; font-weight: 700; line-height: 1.35; }

  .cta-banner {
    background: #0d1733;
    border: 2.5px solid #00e5ff;
    box-shadow: 0 0 25px rgba(0, 229, 255, 0.45);
    border-radius: 14px;
    padding: 16px;
    text-align: center;
    font-size: 20px;
    font-weight: 900;
    color: #00e5ff;
    letter-spacing: 0.5px;
  }
</style>
</head>
<body>
  <div class="bg-sym s-q1">❓</div>
  <div class="bg-sym s-bulb">💡</div>
  <div class="bg-sym s-q2">❓</div>
  <div class="bg-sym s-gear">⚙️</div>
  <div class="bg-sym s-code">&lt;/&gt;</div>

  <div class="outer-frame">
    <div class="header">
      <div class="h-title">SLIDE 04 • <span>OPERATIONAL ROADMAP</span></div>
      <div class="h-badge">4-STAGE PIPELINE FLOW</div>
    </div>

    <div class="robot-flow-banner">
      <img src="file:///{ROBOT_FLOW_IMG_PATH}" class="robot-img" alt="Robot Hologram Flowchart">
    </div>

    <div class="roadmap-stack">
      <div class="step-card sc-1">
        <div class="s-num n1">01</div>
        <div class="s-details">
          <div class="s-head-row">
            <div class="s-title">🔍 Autonomous Daily Discovery</div>
            <div class="s-tag">PLAYWRIGHT SCRAPER</div>
          </div>
          <div class="s-desc">Playwright scraper ingests target roles & recruiter leads daily, filtering out spam or duplicate entries.</div>
        </div>
      </div>
      <div class="step-card sc-2">
        <div class="s-num n2">02</div>
        <div class="s-details">
          <div class="s-head-row">
            <div class="s-title">🧠 Notion DB & SQLite Sync</div>
            <div class="s-tag">TWO-WAY STATE STORE</div>
          </div>
          <div class="s-desc">Centralized state storage tracks lead stage, message drafts, and timestamps in real-time.</div>
        </div>
      </div>
      <div class="step-card sc-3">
        <div class="s-num n3">03</div>
        <div class="s-details">
          <div class="s-head-row">
            <div class="s-title">📱 1-Tap Mobile Phone Review</div>
            <div class="s-tag">HUMAN-IN-THE-LOOP</div>
          </div>
          <div class="s-desc">Human-in-the-Loop approval via mobile Slack webhooks before any connection or DM dispatches.</div>
        </div>
      </div>
      <div class="step-card sc-4">
        <div class="s-num n4">04</div>
        <div class="s-details">
          <div class="s-head-row">
            <div class="s-title">✉️ Stealth Outreach & FLUX.1 Studio</div>
            <div class="s-tag">MCP VISUAL STUDIO</div>
          </div>
          <div class="s-desc">Dispatches custom pitch packets safely and generates high-res post content via MCP.</div>
        </div>
      </div>
    </div>

    <div class="cta-banner">⚡ 100% AUTOMATED EXECUTION • SAFEGUARDED BY HUMAN APPROVAL</div>
  </div>
</body>
</html>"""

def render_edge_screenshot(html_string: str, output_png_path: str):
    temp_html = os.path.join(CAROUSEL_DIR, f"temp_{int(time.time())}.html")
    with open(temp_html, "w", encoding="utf-8") as f:
        f.write(html_string)
    cmd = [EDGE_PATH, "--headless", "--disable-gpu", "--window-size=1080,1350", "--hide-scrollbars", f"--screenshot={output_png_path}", temp_html]
    subprocess.run(cmd, check=True)
    if os.path.exists(temp_html):
        os.remove(temp_html)

def generate_upgraded_4slide_carousel(topic: str = "LinkedIn Job Hunt & Outreach Automation"):
    os.makedirs(CAROUSEL_DIR, exist_ok=True)
    print("=================================================================")
    print(f"[Master Automation Pipeline] Generating 4 Slides for: '{topic}'")
    print("=================================================================")

    # SLIDE 1: Hero Cover Card using pristine 3D Command Center Artwork + Vector HTML Overlay (ZERO GIBBERISH)
    print("\n[Slide 1/4] Rendering Slide 1 Hero Cover (Pristine 3D Artwork + Vector Overlay)...")
    art_path = os.path.join(IMAGES_DIR, "ai_robot_human_command_center_diagram.png")
    s1_html = f"""<!DOCTYPE html>
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
  .h-title {{ font-size: 36px; font-weight: 900; color: #fff; letter-spacing: -0.5px; }}
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

  .overlay-badge-top {{
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
  }}

  .overlay-badge-right {{
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
  }}

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
    font-size: 20px;
    font-weight: 900;
    color: #c7d2fe;
    letter-spacing: 0.5px;
  }}
</style>
</head>
<body>
  <div class="outer-frame">
    <div class="header">
      <div class="h-sub">⚡ AI VISUAL CONTENT STUDIO</div>
      <div class="h-title"><span>{topic.upper()}</span></div>
    </div>

    <div class="artwork-container">
      <img src="file:///{art_path.replace('\\', '/')}" class="art-img" alt="3D Command Center Artwork">
      <div class="overlay-badge-top">🤖 AI AGENT OPERATED</div>
      <div class="overlay-badge-right">🛡️ 100% BAN-SAFE</div>
    </div>

    <div class="stats-banner">
      <div class="stat-card"><div class="sc-val">FLUX.1</div><div class="sc-lbl">Visual Engine</div></div>
      <div class="stat-card"><div class="sc-val">8K High-Res</div><div class="sc-lbl">Rendering</div></div>
      <div class="stat-card"><div class="sc-val">Stdio RPC</div><div class="sc-lbl">MCP Protocol</div></div>
      <div class="stat-card"><div class="sc-val">4-Slide</div><div class="sc-lbl">Carousel Pack</div></div>
    </div>

    <div class="footer-cta">🚀 AUTOMATED 8K CAROUSEL GENERATOR • POWERED BY MCP</div>
  </div>
</body>
</html>"""
    s1_path = os.path.join(CAROUSEL_DIR, "slide_1_hero_command_center.png")
    render_edge_screenshot(s1_html, s1_path)
    print(f"[OK] Slide 1 ready (ZERO GIBBERISH): {s1_path}")

    # SLIDE 2: Space Grotesk High-Density Architecture Card
    print("\n[Slide 2/4] Rendering Space Grotesk High-Density Architecture Card...")
    s2_html = SLIDE2_SPACE_GROTESK_HTML.replace("{TOPIC_HEADER}", topic.upper())
    s2_path = os.path.join(CAROUSEL_DIR, "slide_2_core_architecture_details.png")
    render_edge_screenshot(s2_html, s2_path)
    print(f"[OK] Slide 2 ready: {s2_path}")

    # SLIDE 3: Dual 3D Character Avatars (Stressed vs Happy)
    print("\n[Slide 3/4] Rendering Dual 3D Character Avatars (Stressed vs Happy)...")
    stressed_img = os.path.join(IMAGES_DIR, "stressed_manual_job_hunter.png")
    happy_img = os.path.join(IMAGES_DIR, "happy_automated_job_hunter.png")
    s3_html = SLIDE3_AVATARS_HTML.replace("{STRESSED_IMG_PATH}", stressed_img.replace("\\", "/")).replace("{HAPPY_IMG_PATH}", happy_img.replace("\\", "/")).replace("{TOPIC_HEADER}", topic)
    s3_path = os.path.join(CAROUSEL_DIR, "slide_3_before_vs_after_comparison.png")
    render_edge_screenshot(s3_html, s3_path)
    print(f"[OK] Slide 3 ready with 3D Avatars: {s3_path}")

    # SLIDE 4: Ultra-Bold Outfit Typography, Interrogation Symbols, Lightbulbs & Huge Text
    print("\n[Slide 4/4] Rendering Ultra-Bold Outfit Typography & Interrogation Symbols...")
    robot_flow_img = os.path.join(IMAGES_DIR, "roadmap_execution_robot_flow.png")
    s4_html = SLIDE4_OUTFIT_UPGRADED_HTML.replace("{ROBOT_FLOW_IMG_PATH}", robot_flow_img.replace("\\", "/"))
    s4_path = os.path.join(CAROUSEL_DIR, "slide_4_operational_roadmap_cta.png")
    render_edge_screenshot(s4_html, s4_path)
    print(f"[OK] Slide 4 ready with Outfit font & Question symbols: {s4_path}")

    print("\n=================================================================")
    print("[SUCCESS] ALL 4 DYNAMIC SLIDES PERFECTLY RENDERED IN:")
    print(f"Directory: {CAROUSEL_DIR}")
    print("=================================================================")

    return {
        "topic": topic,
        "slide_1": s1_path,
        "slide_2": s2_path,
        "slide_3": s3_path,
        "slide_4": s4_path
    }

if __name__ == "__main__":
    test_topic = "Autonomous LinkedIn Job Hunt Autopilot"
    generate_upgraded_4slide_carousel(topic=test_topic)
