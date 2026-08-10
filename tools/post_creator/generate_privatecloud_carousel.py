import os
import sys
import shutil
import subprocess
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
POST_CREATOR_DIR = os.path.join(PROJECT_ROOT, "tools", "post_creator")
CAROUSEL_DIR = os.path.join(PROJECT_ROOT, "output", "posts", "carousel_bundle_privatecloud")
IMAGES_DIR = os.path.join(PROJECT_ROOT, "output", "posts", "images")
EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

os.makedirs(CAROUSEL_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

# Slide 1 HTML (Private Cloud Hero)
SLIDE1_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@700;800;900&family=Fira+Code:wght@700&display=swap');
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    width: 1080px;
    height: 1350px;
    background: #030712;
    background-image: 
      radial-gradient(circle at 50% 20%, rgba(0, 229, 255, 0.25) 0%, transparent 60%),
      radial-gradient(circle at 85% 85%, rgba(147, 51, 234, 0.2) 0%, transparent 50%),
      linear-gradient(rgba(0, 229, 255, 0.04) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0, 229, 255, 0.04) 1px, transparent 1px);
    background-size: 100% 100%, 100% 100%, 30px 30px, 30px 30px;
    font-family: 'Space Grotesk', sans-serif;
    color: #ffffff;
    padding: 30px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    overflow: hidden;
  }
  .outer-frame {
    border: 3px solid #00e5ff;
    box-shadow: 0 0 35px rgba(0, 229, 255, 0.35), inset 0 0 20px rgba(0, 229, 255, 0.1);
    border-radius: 20px;
    height: 100%;
    padding: 35px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    background: rgba(3, 7, 18, 0.85);
  }
  .header {
    text-align: center;
  }
  .tag {
    display: inline-block;
    background: linear-gradient(90deg, #00e5ff, #3b82f6);
    color: #030712;
    font-weight: 900;
    padding: 8px 20px;
    border-radius: 30px;
    font-size: 18px;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 15px;
  }
  h1 {
    font-size: 46px;
    font-weight: 900;
    line-height: 1.15;
    background: linear-gradient(135deg, #ffffff 30%, #00e5ff 70%, #a855f7 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 10px;
  }
  .sub {
    font-size: 22px;
    color: #94a3b8;
    font-weight: 700;
  }
  .visual-card {
    background: #0f172a;
    border: 2px solid rgba(0, 229, 255, 0.3);
    border-radius: 16px;
    padding: 25px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.5);
  }
  .grid-2 {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-top: 15px;
  }
  .box {
    background: rgba(15, 23, 42, 0.8);
    border: 1px solid rgba(0, 229, 255, 0.2);
    border-radius: 12px;
    padding: 20px;
  }
  .box-title {
    color: #00e5ff;
    font-size: 20px;
    font-weight: 800;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .box-body {
    color: #cbd5e1;
    font-size: 17px;
    line-height: 1.5;
  }
  .footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top: 2px solid rgba(0, 229, 255, 0.2);
    padding-top: 20px;
  }
  .tech-stack {
    font-family: 'Fira Code', monospace;
    color: #facc15;
    font-size: 16px;
  }
  .swipe {
    color: #00e5ff;
    font-weight: 900;
    font-size: 20px;
  }
</style>
</head>
<body>
<div class="outer-frame">
  <div class="header">
    <div class="tag">☁️ AZNA-CLOUD PLATFORM</div>
    <h1>SELF-HOSTED PRIVATE CLOUD ARCHITECTURE</h1>
    <div class="sub">Proxmox VE · 8 Docker Services · 5 Ansible Roles · AI ChatOps</div>
  </div>

  <div class="visual-card">
    <div style="text-align: center; color: #facc15; font-size: 22px; font-weight: 800; margin-bottom: 15px;">
      ⚡ How the Platform Solves University Compute Chaos
    </div>
    <div class="grid-2">
      <div class="box">
        <div class="box-title">🎓 For Students</div>
        <div class="box-body">
          • 1-Click VM deployment from clean golden templates<br>
          • Dedicated GPU compute access at 2 AM<br>
          • In-browser terminal & remote desktop access<br>
          • Daily resource quotas & isolation
        </div>
      </div>
      <div class="box">
        <div class="box-title">👨‍🏫 For Teachers</div>
        <div class="box-body">
          • Pre-configured lab environments in seconds<br>
          • Zero "doesn't work on my laptop" setup delays<br>
          • Class management & student resource limits<br>
          • Full cluster health & audit logging
        </div>
      </div>
    </div>
  </div>

  <div class="grid-2">
    <div class="box" style="border-color: #a855f7;">
      <div class="box-title" style="color: #a855f7;">🤖 AI ChatOps Console</div>
      <div class="box-body">
        OpenAI function-calling agent deploys and resizes VMs via natural language commands.
      </div>
    </div>
    <div class="box" style="border-color: #22c55e;">
      <div class="box-title" style="color: #22c55e;">🔒 Security & Locks</div>
      <div class="box-body">
        Redis distributed locks for race-free VMID allocation + Fernet encrypted secrets.
      </div>
    </div>
  </div>

  <div class="footer">
    <div class="tech-stack">FastAPI · Proxmox · Celery · Guacamole · React · Jenkins</div>
    <div class="swipe">SWIPE FOR SPECS ➔</div>
  </div>
</div>
</body>
</html>
"""

# Slide 2 HTML (5-Layer Core Architecture Specs)
SLIDE2_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@700;800;900&family=Fira+Code:wght@700&display=swap');
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    width: 1080px;
    height: 1350px;
    background: #030712;
    background-image: 
      radial-gradient(circle at 85% 15%, rgba(250, 204, 21, 0.2) 0%, transparent 45%),
      radial-gradient(circle at 15% 85%, rgba(0, 229, 255, 0.2) 0%, transparent 45%),
      linear-gradient(rgba(0, 229, 255, 0.04) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0, 229, 255, 0.04) 1px, transparent 1px);
    background-size: 100% 100%, 100% 100%, 30px 30px, 30px 30px;
    font-family: 'Space Grotesk', sans-serif;
    color: #ffffff;
    padding: 30px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    overflow: hidden;
  }
  .outer-frame {
    border: 3px solid #facc15;
    box-shadow: 0 0 35px rgba(250, 204, 21, 0.35);
    border-radius: 20px;
    height: 100%;
    padding: 35px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    background: rgba(3, 7, 18, 0.85);
  }
  .title { text-align: center; color: #facc15; font-size: 38px; font-weight: 900; }
  .subtitle { text-align: center; color: #94a3b8; font-size: 20px; margin-bottom: 20px; }
  .layer {
    border-radius: 12px;
    padding: 18px 22px;
    margin-bottom: 14px;
    border: 2px solid transparent;
  }
  .l-title { font-size: 20px; font-weight: 900; margin-bottom: 6px; display: flex; justify-content: space-between; }
  .l-desc { font-size: 16px; color: #e2e8f0; line-height: 1.4; }
  .l1 { background: rgba(245, 158, 11, 0.15); border-color: #f59e0b; }
  .l2 { background: rgba(6, 182, 212, 0.15); border-color: #06b6d4; }
  .l3 { background: rgba(16, 185, 129, 0.15); border-color: #10b981; }
  .l4 { background: rgba(168, 85, 247, 0.15); border-color: #a855f7; }
  .l5 { background: rgba(239, 68, 68, 0.15); border-color: #ef4444; }
  .footer { display: flex; justify-content: space-between; color: #00e5ff; font-weight: 800; font-size: 18px; border-top: 2px solid rgba(0,229,255,0.2); padding-top: 15px; }
</style>
</head>
<body>
<div class="outer-frame">
  <div>
    <div class="title">📐 5-LAYER PRIVATE CLOUD ARCHITECTURE</div>
    <div class="subtitle">Full-Stack Virtualization Platform Blueprint</div>

    <div class="layer l1">
      <div class="l-title" style="color: #f59e0b;"><span>LAYER 1: CLIENT & INTERFACE</span><span>[React + Vite + TS]</span></div>
      <div class="l-desc">Aether Cloud Orchestrator UI + Admin Command Center dashboard. Live cluster health node topology, quota meters, and browser-based remote access.</div>
    </div>

    <div class="layer l2">
      <div class="l-title" style="color: #06b6d4;"><span>LAYER 2: API GATEWAY & SECURITY</span><span>[FastAPI + Pydantic]</span></div>
      <div class="l-desc">JWT authentication, daily quota enforcement, rate limiting, and Fernet symmetric encryption for Proxmox and database credentials.</div>
    </div>

    <div class="layer l3">
      <div class="l-title" style="color: #10b981;"><span>LAYER 3: PROVISIONING ENGINE</span><span>[Proxmox VE + Celery + Redis]</span></div>
      <div class="l-desc">Custom 865-line Proxmox API client. Async Celery workers handle template cloning & resizing. Redis distributed locks guarantee race-free VMID assignment.</div>
    </div>

    <div class="layer l4">
      <div class="l-title" style="color: #a855f7;"><span>LAYER 4: AI & KNOWLEDGE</span><span>[OpenAI + ChromaDB + ONNX]</span></div>
      <div class="l-desc">Agentic ChatOps orchestrator translating natural language into execution trees. Local vector store (all-MiniLM-L6-v2) for self-service platform documentation.</div>
    </div>

    <div class="layer l5">
      <div class="l-title" style="color: #ef4444;"><span>LAYER 5: DATA & AUTOMATION</span><span>[PostgreSQL 16 + Ansible + Jenkins]</span></div>
      <div class="l-desc">Raw psycopg2 connection pool + audit logging. 5 Ansible roles automate host setup to golden template creation. 4-stage Jenkins CI/CD pipeline.</div>
    </div>
  </div>

  <div class="footer">
    <div>AZNA-CLOUD SPECS</div>
    <div>SWIPE FOR COMPARISON ➔</div>
  </div>
</div>
</body>
</html>
"""

# Slide 3 HTML (Before vs After)
SLIDE3_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@700;800;900&display=swap');
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    width: 1080px;
    height: 1350px;
    background: #030712;
    font-family: 'Space Grotesk', sans-serif;
    color: #ffffff;
    padding: 30px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    overflow: hidden;
  }
  .outer-frame {
    border: 3px solid #00e5ff;
    box-shadow: 0 0 35px rgba(0, 229, 255, 0.35);
    border-radius: 20px;
    height: 100%;
    padding: 35px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    background: rgba(3, 7, 18, 0.85);
  }
  .title { text-align: center; color: #00e5ff; font-size: 38px; font-weight: 900; margin-bottom: 20px; }
  .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 25px; height: 80%; }
  .col-before {
    background: rgba(239, 68, 68, 0.1);
    border: 2px solid #ef4444;
    border-radius: 16px;
    padding: 25px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }
  .col-after {
    background: rgba(34, 197, 94, 0.1);
    border: 2px solid #22c55e;
    border-radius: 16px;
    padding: 25px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }
  .col-header { font-size: 24px; font-weight: 900; text-align: center; padding-bottom: 15px; border-bottom: 2px solid rgba(255,255,255,0.1); }
  .item { font-size: 17px; margin-bottom: 16px; line-height: 1.4; }
  .footer { display: flex; justify-content: space-between; color: #00e5ff; font-weight: 800; font-size: 18px; border-top: 2px solid rgba(0,229,255,0.2); padding-top: 15px; }
</style>
</head>
<body>
<div class="outer-frame">
  <div class="title">⚡ BEFORE VS AFTER — COMPUTE PLATFORM</div>
  <div class="grid-2">
    <div class="col-before">
      <div class="col-header" style="color: #ef4444;">❌ MANUAL LAB SERVER</div>
      <div class="item">❌ 30 students SSHing into one un-isolated Proxmox node</div>
      <div class="item">❌ Wrong CUDA/PyTorch package breaks everyone's environment</div>
      <div class="item">❌ Student hangs GPU node since Tuesday; deadline blocked</div>
      <div class="item">❌ First 20 mins of lab lost to "doesn't work on my laptop"</div>
      <div class="item">❌ Zero visibility into who launched what or resource usage</div>
    </div>
    <div class="col-after">
      <div class="col-header" style="color: #22c55e;">✅ AZNA-CLOUD PLATFORM</div>
      <div class="item">✅ Clean, isolated VM in seconds per student from golden template</div>
      <div class="item">✅ Dedicated GPU compute allocation with daily resource quotas</div>
      <div class="item">✅ In-browser terminal (ttyd) + RDP (Guacamole); zero VPN</div>
      <div class="item">✅ Teacher clones lab template in 1-click; lab starts on time</div>
      <div class="item">✅ AI ChatOps + full admin dashboard with cluster health & audit logs</div>
    </div>
  </div>
  <div class="footer">
    <div>AZNA-CLOUD IMPACT</div>
    <div>SWIPE FOR ROADMAP ➔</div>
  </div>
</div>
</body>
</html>
"""

# Slide 4 HTML (Roadmap & Stack)
SLIDE4_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@700;800;900&display=swap');
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    width: 1080px;
    height: 1350px;
    background: #030712;
    font-family: 'Space Grotesk', sans-serif;
    color: #ffffff;
    padding: 30px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    overflow: hidden;
  }
  .outer-frame {
    border: 3px solid #a855f7;
    box-shadow: 0 0 35px rgba(168, 85, 247, 0.35);
    border-radius: 20px;
    height: 100%;
    padding: 35px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    background: rgba(3, 7, 18, 0.85);
  }
  .title { text-align: center; color: #a855f7; font-size: 38px; font-weight: 900; margin-bottom: 20px; }
  .step { background: rgba(15, 23, 42, 0.9); border: 2px solid rgba(168, 85, 247, 0.4); border-radius: 14px; padding: 18px; margin-bottom: 14px; }
  .s-title { font-size: 19px; font-weight: 900; color: #00e5ff; margin-bottom: 4px; }
  .s-body { font-size: 16px; color: #cbd5e1; }
  .footer { display: flex; justify-content: space-between; color: #a855f7; font-weight: 800; font-size: 18px; border-top: 2px solid rgba(168,85,247,0.2); padding-top: 15px; }
</style>
</head>
<body>
<div class="outer-frame">
  <div>
    <div class="title">🗺️ PLATFORM EXECUTION ROADMAP</div>
    
    <div class="step">
      <div class="s-title">STEP 1: BARE-METAL ANSIBLE PROVISIONING</div>
      <div class="s-body">5 Ansible roles configure Proxmox host, Admin VM, Jenkins node, and Linux/Windows golden templates automatically.</div>
    </div>

    <div class="step">
      <div class="s-title">STEP 2: 8-SERVICE DOCKER COMPOSE ORCHESTRATION</div>
      <div class="s-body">Single `docker compose up` starts Postgres, Redis, FastAPI, Celery, Guacamole, guacd, MySQL, and Nginx React frontend.</div>
    </div>

    <div class="step">
      <div class="s-title">STEP 3: ASYNC CELERY & REDIS DISTRIBUTED LOCKS</div>
      <div class="s-body">Provisioning tasks execute asynchronously. Redis locks guarantee zero race conditions during VMID assignment under load.</div>
    </div>

    <div class="step">
      <div class="s-title">STEP 4: AI CHATOPS & RAG KNOWLEDGE BASE</div>
      <div class="s-body">OpenAI function-calling agent deploys VMs from text instructions. Local ChromaDB vector store answers platform documentation queries.</div>
    </div>

    <div class="step">
      <div class="s-title">STEP 5: AUTOMATED JENKINS CI/CD DEPLOYMENT</div>
      <div class="s-body">GitHub webhook triggers parallel Docker image builds, pushes to Docker Hub, and executes SSH deployment with health checks.</div>
    </div>
  </div>

  <div class="footer">
    <div>AZNA-CLOUD ROADMAP</div>
    <div>PROXMOX · FASTAPI · REACT</div>
  </div>
</div>
</body>
</html>
"""

def generate_slides():
    html_files = [
        ("slide1.html", SLIDE1_HTML, "slide_1_hero_command_center.png"),
        ("slide2.html", SLIDE2_HTML, "slide_2_core_architecture_details.png"),
        ("slide3.html", SLIDE3_HTML, "slide_3_before_vs_after_comparison.png"),
        ("slide4.html", SLIDE4_HTML, "slide_4_operational_roadmap_cta.png")
    ]

    for fname, html_content, out_png in html_files:
        h_path = os.path.join(CAROUSEL_DIR, fname)
        with open(h_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        png_path = os.path.join(CAROUSEL_DIR, out_png)
        print(f"Rendering {out_png} via Edge Headless...")
        cmd = [
            EDGE_PATH,
            "--headless",
            "--disable-gpu",
            f"--screenshot={png_path}",
            "--window-size=1080,1350",
            h_path
        ]
        subprocess.run(cmd, check=True)
        print(f"[OK] Rendered: {png_path}")

        # Also copy to output/posts/carousel_bundle/ so both folders are updated
        main_bundle = os.path.join(PROJECT_ROOT, "output", "posts", "carousel_bundle", out_png)
        shutil.copy2(png_path, main_bundle)

if __name__ == "__main__":
    generate_slides()
