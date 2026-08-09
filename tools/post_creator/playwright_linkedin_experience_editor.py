"""
LinkedIn Experience Cleanup + Re-add v6
Step 1: Delete the 3 empty experience entries
Step 2: Re-add with position-based field filling (field[0]=Title, field[2]=Company)
"""
import os, time
from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
USER_DATA_DIR = os.path.join(PROJECT_ROOT, ".pw_browser", "linkedin_user_data")
SS_DIR = os.path.join(PROJECT_ROOT, "output", "linkedin")
os.makedirs(SS_DIR, exist_ok=True)

POSITIONS = [
    {
        "title": "DevOps Engineer",
        "company": "Verventech",
        "start_month": "January",
        "start_year": "2025",
        "current": True,
        "description": "Helping companies design, build, and ship CI/CD and containerized deployment pipelines.\n\n- Designed and implemented CI/CD pipelines for client projects using Jenkins and GitHub Actions, automating build, test, and deploy workflows that replaced manual release processes.\n- Containerized client applications with Docker and Docker Compose, setting up multi-service stacks with health checks, named volumes, and internal networking.\n- Wrote Ansible playbooks and roles for automated server provisioning and configuration management across client infrastructure.\n- Set up monitoring and alerting using Prometheus and helped teams adopt infrastructure-as-code practices.\n- Collaborated directly with client engineering teams to assess their deployment pain points and deliver production-ready DevOps tooling.",
    },
    {
        "title": "Founding Engineer - Infrastructure and Platform",
        "company": "Verventech",
        "start_month": "January",
        "start_year": "2024",
        "current": True,
        "description": "Building production infrastructure and shipping platform-grade systems:\n\nPrivateCloud - Self-Hosted VM Management Platform (B.Tech Capstone)\n- Built a browser-based platform that provisions and manages Proxmox VMs end to end, packaged as a 7-service Docker Compose stack.\n- Wrote 5 Ansible roles that take a bare Proxmox server to a fully running platform with one command.\n- Built a Jenkins CI/CD pipeline: parallel Docker builds, push to Docker Hub, SSH deploy with health checks.\n- Shipped clone-from-template feature with Redis distributed locks for race-free VMID allocation.\n- Production hardened: Fernet-encrypted secrets, Redis auth, rate-limited endpoints, 98 passing tests.\n\nRAG PDF MLOps - Production RAG on GPU Kubernetes\n- Stood up a 2-node K3s cluster (Intel NUC + RTX 3090) with NVIDIA device plugin for GPU scheduling.\n- Built an LLM-as-a-Judge CI quality gate in Jenkins that fails the build when quality drops.\n- Versioned data/models with DVC, logged every run in MLflow.",
    },
    {
        "title": "AI Systems Engineer",
        "company": "Verventech",
        "start_month": "January",
        "start_year": "2024",
        "current": True,
        "description": "Building autonomous AI agents and production automation pipelines:\n\nContent Automation Platforms\n- Designed fault-tolerant, self-healing pipelines (100+ Python tools) that run unattended on a schedule.\n- Made runs crash-safe with idempotent state-machine checkpointing.\n- Built a never-degrade quality gate with auto-rollback on regression.\n- Ran local GPU inference with a VRAM lifecycle manager on a single RTX 3090.\n\nDesktop Agent - Computer-Use Vision Agent\n- Built a Windows screen-control agent with swappable Claude/OpenRouter backends.\n- Safety-first: kill-switch, app allowlist, confirm-risky prompts, budget caps.\n\nMCP Servers and AI Developer Tooling\n- Built MCP servers for Google Workspace and Gemini media.\n- Designed the Three-Brain Knowledge Architecture for AI coding assistants. Measured 60-95x context-token reduction.",
    },
]


def delete_all_experience(page):
    """Delete all existing experience entries by navigating to the experience section."""
    page.goto("https://www.linkedin.com/in/me/", wait_until="domcontentloaded", timeout=30000)
    time.sleep(5)
    
    # Find and click experience edit pencil buttons
    # Experience section is typically below Analytics
    for attempt in range(6):
        page.mouse.wheel(0, 500)
        time.sleep(1)
    
    page.screenshot(path=os.path.join(SS_DIR, "experience_section.png"))
    
    # Look for experience entries with edit buttons
    exp_entries = page.evaluate("""() => {
        // Find all edit/pencil buttons within experience-like sections
        const all = document.querySelectorAll('*');
        const results = [];
        for (const el of all) {
            const text = el.textContent.trim().toLowerCase();
            const rect = el.getBoundingClientRect();
            if (rect.width === 0) continue;
            
            // Look for experience section header
            const direct = Array.from(el.childNodes)
                .filter(n => n.nodeType === 3)
                .map(n => n.textContent.trim())
                .join(' ');
            if (direct === 'Experience' || direct === 'experience') {
                results.push({type: 'header', tag: el.tagName, top: Math.round(rect.top)});
            }
        }
        
        // Also look for Verventech or any company names
        for (const el of all) {
            const direct = Array.from(el.childNodes)
                .filter(n => n.nodeType === 3)
                .map(n => n.textContent.trim())
                .join(' ');
            if (direct && (direct.includes('Verventech') || direct.includes('Present'))) {
                const rect = el.getBoundingClientRect();
                results.push({type: 'entry', text: direct.substring(0, 40), top: Math.round(rect.top)});
            }
        }
        return results;
    }""")
    
    print(f"Experience entries found: {exp_entries}")
    
    # Try to find and click delete on each entry
    deleted = 0
    for _ in range(3):
        # Look for experience entry edit buttons
        edit_result = page.evaluate("""() => {
            // Find experience list items with delete option
            const sections = document.querySelectorAll('section, div[id*="experience"], [data-section="experience"]');
            for (const sec of sections) {
                const heading = sec.querySelector('h2, h3');
                if (heading && heading.textContent.trim().toLowerCase().includes('experience')) {
                    // Found experience section - look for edit buttons
                    const btns = sec.querySelectorAll('button');
                    for (const btn of btns) {
                        const aria = btn.getAttribute('aria-label') || '';
                        if (aria.toLowerCase().includes('edit') || aria.toLowerCase().includes('delete')) {
                            btn.click();
                            return {clicked: true, aria: aria};
                        }
                    }
                    // Click first pencil button
                    const editBtns = sec.querySelectorAll('button svg');
                    if (editBtns.length > 0) {
                        editBtns[0].closest('button').click();
                        return {clicked: true, type: 'svg_button'};
                    }
                }
            }
            return {clicked: false};
        }""")
        
        if not edit_result.get('clicked'):
            break
        
        time.sleep(2)
        
        # Look for delete button in the edit modal/form
        del_result = page.evaluate("""() => {
            const btns = document.querySelectorAll('button');
            for (const btn of btns) {
                const text = btn.textContent.trim().toLowerCase();
                if (text === 'delete experience' || text === 'delete' || text === 'delete position') {
                    btn.click();
                    return {deleted: true, text: btn.textContent.trim()};
                }
            }
            return {deleted: false};
        }""")
        
        if del_result.get('deleted'):
            time.sleep(2)
            # Confirm delete if there's a confirmation dialog
            page.evaluate("""() => {
                const btns = document.querySelectorAll('button');
                for (const btn of btns) {
                    const text = btn.textContent.trim().toLowerCase();
                    if (text === 'yes, delete' || text === 'delete' || text === 'confirm') {
                        btn.click();
                        return true;
                    }
                }
                return false;
            }""")
            time.sleep(3)
            deleted += 1
            print(f"  Deleted entry {deleted}")
    
    print(f"Total deleted: {deleted}")
    return deleted


def navigate_to_add_position(page):
    """Add section -> Core -> Add position."""
    page.evaluate("window.scrollTo(0, 200)")
    time.sleep(1)
    
    # Click 'Add section' via JS
    page.evaluate("""() => {
        const links = document.querySelectorAll('a, button');
        for (const el of links) {
            if (el.textContent.trim() === 'Add section') {
                const rect = el.getBoundingClientRect();
                if (rect.top > 100) { el.click(); return; }
            }
        }
    }""")
    time.sleep(3)
    
    # Expand 'Core'
    page.evaluate("""() => {
        const all = document.querySelectorAll('*');
        for (const el of all) {
            const direct = Array.from(el.childNodes).filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join(' ');
            if (direct === 'Core') {
                const clickable = el.closest('button') || el.closest('[role="button"]') || el.parentElement;
                if (clickable) clickable.click();
                else el.click();
                return;
            }
        }
    }""")
    time.sleep(2)
    
    # Click 'Add position'
    result = page.evaluate("""() => {
        const all = document.querySelectorAll('*');
        for (const el of all) {
            const direct = Array.from(el.childNodes).filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join(' ').toLowerCase();
            if (direct.includes('add position') || direct === 'position') {
                const clickable = el.closest('button') || el.closest('a') || el;
                clickable.click();
                return true;
            }
        }
        return false;
    }""")
    time.sleep(4)
    return result


def fill_position(page, pos, idx):
    """Fill the experience form using POSITION-BASED field indexing."""
    print(f"\n=== Position {idx+1}: {pos['title']} ===")
    time.sleep(2)
    
    page.screenshot(path=os.path.join(SS_DIR, f"exp_v6_form_{idx+1}.png"))
    
    # Get all visible INPUT fields (not select, not hidden)
    visible_inputs = page.locator("input[type='text']:visible, input:not([type]):visible")
    input_count = visible_inputs.count()
    print(f"  Visible text inputs: {input_count}")
    
    # From the form screenshot we know:
    # Input[0] = Title (placeholder: "Ex: Retail Sales Manager") 
    # Input[1] = Company (placeholder: "Ex: Microsoft")
    # The form might also have Location and other inputs
    
    # Fill Title — FIRST visible text input in the form area
    if input_count >= 1:
        # Filter out the search bar (which has placeholder "Search" or is at top=9)
        for i in range(input_count):
            inp = visible_inputs.nth(i)
            try:
                top = inp.evaluate("el => Math.round(el.getBoundingClientRect().top)")
                ph = inp.evaluate("el => el.placeholder || ''")
                if top > 100:  # Skip the search bar at top=9
                    inp.fill(pos['title'])
                    print(f"  Title: '{pos['title']}' (input #{i}, top={top}, ph={ph})")
                    break
            except:
                continue
    time.sleep(1)
    
    # Fill Company — the input with "Ex: Microsoft" placeholder or the next input after Title
    for i in range(input_count):
        inp = visible_inputs.nth(i)
        try:
            top = inp.evaluate("el => Math.round(el.getBoundingClientRect().top)")
            ph = inp.evaluate("el => el.placeholder || ''")
            val = inp.evaluate("el => el.value || ''")
            if top > 100 and not val and ph.lower().startswith('ex:'):
                inp.fill(pos['company'])
                time.sleep(2)
                page.keyboard.press("Escape")  # Dismiss autocomplete
                print(f"  Company: '{pos['company']}' (input #{i}, top={top})")
                break
        except:
            continue
    time.sleep(1)
    
    # Check 'I currently work here'
    if pos.get('current'):
        try:
            cbs = page.locator("input[type='checkbox']:visible")
            for i in range(cbs.count()):
                cb = cbs.nth(i)
                if not cb.is_checked():
                    cb.check()
                    print("  Currently working: checked")
                    break
        except:
            pass
    time.sleep(0.5)
    
    # Fill dates via selects
    try:
        selects = page.locator("select:visible")
        month_done = False
        year_done = False
        for i in range(selects.count()):
            sel = selects.nth(i)
            opts = sel.evaluate("el => Array.from(el.options).map(o => o.text).join('|')")
            if not month_done and 'January' in opts:
                sel.select_option(label=pos['start_month'])
                month_done = True
                print(f"  Month: {pos['start_month']}")
            elif not year_done and pos['start_year'] in opts:
                sel.select_option(label=pos['start_year'])
                year_done = True
                print(f"  Year: {pos['start_year']}")
    except Exception as e:
        print(f"  Dates: {e}")
    
    # Scroll down to description
    page.mouse.move(630, 400)
    page.mouse.wheel(0, 400)
    time.sleep(1)
    
    # Fill description
    try:
        pm = page.locator("div.tiptap.ProseMirror, div.ProseMirror[contenteditable='true']").first
        if pm.is_visible(timeout=5000):
            pm.scroll_into_view_if_needed()
            time.sleep(0.5)
            pm.click()
            time.sleep(0.3)
            page.keyboard.press("Control+a")
            time.sleep(0.2)
            page.keyboard.press("Backspace")
            time.sleep(0.2)
            page.keyboard.type(pos['description'], delay=2)
            print(f"  Description: OK ({len(pos['description'])} chars)")
    except Exception as e:
        print(f"  Description: {e}")
    
    time.sleep(1)
    
    # Screenshot before save
    page.screenshot(path=os.path.join(SS_DIR, f"exp_v6_filled_{idx+1}.png"))
    
    # Save
    try:
        save = page.locator("button:has-text('Save')").first
        if save.is_visible(timeout=5000):
            save.click()
            time.sleep(6)
            print(f"  SAVED!")
            return True
    except:
        pass
    
    print("  Save NOT found")
    return False


def main():
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR, headless=False,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        # Step 1: Delete existing empty entries
        print("=== STEP 1: Delete empty entries ===")
        delete_all_experience(page)
        
        # Step 2: Re-add positions properly
        print("\n=== STEP 2: Add positions ===")
        results = []
        for i, pos in enumerate(POSITIONS):
            page.goto("https://www.linkedin.com/in/me/", wait_until="domcontentloaded", timeout=30000)
            time.sleep(5)
            
            if navigate_to_add_position(page):
                ok = fill_position(page, pos, i)
                results.append({"title": pos["title"], "ok": ok})
            else:
                results.append({"title": pos["title"], "ok": False})
                print(f"  FORM NOT OPENED")
            time.sleep(2)

        # Final screenshot
        page.goto("https://www.linkedin.com/in/me/", wait_until="domcontentloaded", timeout=30000)
        time.sleep(4)
        # Scroll down to experience section
        for _ in range(4):
            page.mouse.wheel(0, 500)
            time.sleep(1)
        page.screenshot(path=os.path.join(SS_DIR, "profile_final_v6.png"))
        
        ctx.close()
        
        print("\n=== RESULTS ===")
        for r in results:
            print(f"  {'OK' if r['ok'] else 'FAIL'}: {r['title']}")

if __name__ == "__main__":
    main()
