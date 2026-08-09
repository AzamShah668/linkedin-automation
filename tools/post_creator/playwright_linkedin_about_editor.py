"""
LinkedIn Profile Editor — Add About Section.
The profile page shows "Write a summary to highlight your personality or work experience"
with an "Add a summary" button. Click that to open the About editor.
"""
import os, time
from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
USER_DATA_DIR = os.path.join(PROJECT_ROOT, ".pw_browser", "linkedin_user_data")

NEW_ABOUT = """I build cloud infrastructure and the AI systems that run on it \u2014 and I've spent the last two years shipping both to production, not just studying them.

B.Tech Computer Science graduate from Central University of Kashmir. DevOps Engineer at Verventech, where I help companies build and ship CI/CD and container pipelines.

What I've built and shipped:

\u2192 A 7-service private cloud on Proxmox that goes from a bare host to a running platform in a single ansible-playbook run \u2014 5 Ansible roles, Fernet-encrypted secrets, 98 passing tests, Redis distributed locks for race-free VM allocation.

\u2192 Production RAG on a 2-node GPU Kubernetes cluster (K3s + RTX 3090), with hybrid retrieval (vector + BM25 + cross-encoder reranking), DVC/MLflow versioning, and an LLM-as-a-Judge CI gate in Jenkins that blocks bad deploys automatically.

\u2192 18+ shipped projects and 100+ production Python tools across DevOps automation, RAG platforms, and autonomous agents \u2014 crash-safe, self-healing, quality-gated.

\u2192 Contributor to Everything Claude Code (140K+ stars, Anthropic Hackathon winner) \u2014 designed a knowledge architecture that cut AI agent context tokens by 60-95x.

\u2192 Custom MCP servers (Google Workspace, Gemini media), computer-use vision agents, and multi-agent orchestrators with intent routing and budget controls.

My stack: Docker, Kubernetes, Jenkins, Ansible, Proxmox, Python, FastAPI, PostgreSQL, RAG/LLMs, MCP protocol, GPU orchestration, CI/CD, Prometheus.

Open to DevOps / Platform / SRE / MLOps / AI Engineer roles (India + Remote).
If you're building infrastructure or applied-AI systems and want someone who owns the whole stack end to end \u2014 azamshah25809@gmail.com"""


def add_about():
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR, headless=False,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        print("[1] Navigating to profile...")
        page.goto("https://www.linkedin.com/in/me/", wait_until="domcontentloaded", timeout=60000)
        time.sleep(5)

        # ── Look for "Add a summary" button or link ──
        print("[2] Looking for 'Add a summary' button...")
        
        # Try clicking "Add a summary" button
        add_summary_clicked = False
        
        # Approach 1: Direct text match
        try:
            btn = page.locator("button:has-text('Add a summary'), a:has-text('Add a summary')").first
            if btn.is_visible(timeout=5000):
                btn.click()
                add_summary_clicked = True
                print("    Clicked 'Add a summary'!")
        except Exception:
            pass

        # Approach 2: Try "Add section" button then look for "About" or "Summary"
        if not add_summary_clicked:
            try:
                print("    Trying 'Add section' -> 'About'...")
                add_section = page.locator("button:has-text('Add section')").first
                if add_section.is_visible(timeout=3000):
                    add_section.click()
                    time.sleep(2)
                    
                    # Look for About option in the dropdown
                    about_option = page.locator("text=About, text=Summary, text=Add about").first
                    if about_option.is_visible(timeout=5000):
                        about_option.click()
                        add_summary_clicked = True
                        print("    Clicked About from Add section dropdown!")
            except Exception as e:
                print(f"    Add section approach: {e}")

        # Approach 3: Navigate directly to the about edit URL
        if not add_summary_clicked:
            print("    Trying direct URL approach...")
            page.goto("https://www.linkedin.com/in/me/edit/forms/summary/new/", wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)
            add_summary_clicked = True
            print("    Navigated to about edit URL")

        time.sleep(3)

        # ── Find the editor and fill it ──
        print("[3] Looking for About editor...")
        
        # Take a screenshot to see what's on screen
        ss1 = os.path.join(PROJECT_ROOT, "output", "linkedin", "about_editor_state.png")
        os.makedirs(os.path.dirname(ss1), exist_ok=True)
        page.screenshot(path=ss1)
        print(f"    State screenshot: {ss1}")
        
        filled = False
        
        # Try ProseMirror (same as headline)
        try:
            prosemirror = page.locator("div.tiptap.ProseMirror, div.ProseMirror[contenteditable='true']").first
            if prosemirror.is_visible(timeout=5000):
                prosemirror.click()
                time.sleep(0.5)
                page.keyboard.press("Control+a")
                time.sleep(0.3)
                page.keyboard.press("Backspace")
                time.sleep(0.3)
                page.keyboard.type(NEW_ABOUT, delay=5)
                filled = True
                print("    Filled via ProseMirror!")
        except Exception:
            pass

        # Try textarea
        if not filled:
            try:
                ta = page.locator("textarea").first
                if ta.is_visible(timeout=5000):
                    ta.fill(NEW_ABOUT)
                    filled = True
                    print("    Filled via textarea!")
            except Exception:
                pass

        # Try contenteditable div (generic)
        if not filled:
            try:
                editable = page.locator("[contenteditable='true']").first
                if editable.is_visible(timeout=5000):
                    editable.click()
                    time.sleep(0.3)
                    page.keyboard.press("Control+a")
                    time.sleep(0.3)
                    page.keyboard.press("Backspace")
                    time.sleep(0.3)
                    page.keyboard.type(NEW_ABOUT, delay=5)
                    filled = True
                    print("    Filled via contenteditable!")
            except Exception:
                pass
        
        if not filled:
            # Dump what's on the page
            print("    Could not find editor. Dumping page state...")
            field_dump = page.evaluate("""() => {
                const fields = document.querySelectorAll('input, textarea, [contenteditable="true"]');
                return Array.from(fields).map(f => ({
                    tag: f.tagName, id: f.id || '', 
                    class: (f.className || '').substring(0, 50),
                    visible: f.getBoundingClientRect().width > 0,
                    editable: f.contentEditable,
                }));
            }""")
            for f in field_dump:
                print(f"      {f}")

        # ── Screenshot ──
        ss2 = os.path.join(PROJECT_ROOT, "output", "linkedin", "about_filled.png")
        page.screenshot(path=ss2)
        print(f"\n[4] Filled screenshot: {ss2}")

        # ── Save ──
        if filled:
            print("[5] Clicking Save...")
            try:
                save_btn = page.locator("button:has-text('Save')").first
                if save_btn.is_visible(timeout=5000):
                    save_btn.click()
                    time.sleep(5)
                    print("    Saved!")
            except Exception as e:
                print(f"    Save error: {e}")

            # Final screenshot
            page.goto("https://www.linkedin.com/in/me/", wait_until="domcontentloaded", timeout=30000)
            time.sleep(4)
            final = os.path.join(PROJECT_ROOT, "output", "linkedin", "profile_with_about.png")
            page.screenshot(path=final)
            print(f"[6] Final: {final}")

        ctx.close()
        print(f"\nAbout filled: {filled}")

if __name__ == "__main__":
    add_about()
