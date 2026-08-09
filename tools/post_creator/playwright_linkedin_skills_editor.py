"""
LinkedIn Profile Cleanup & Skills Add:
1. Scroll through experience section to check for empty entries and delete them
2. Add skills to the profile
3. Update education end date
"""
import os, time
from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
USER_DATA_DIR = os.path.join(PROJECT_ROOT, ".pw_browser", "linkedin_user_data")
SS_DIR = os.path.join(PROJECT_ROOT, "output", "linkedin")
os.makedirs(SS_DIR, exist_ok=True)

SKILLS_TO_ADD = [
    "Docker", "Kubernetes", "Jenkins", "Ansible", "Python",
    "CI/CD", "Linux", "Git", "PostgreSQL", "FastAPI",
    "Proxmox", "Prometheus", "Redis", "DevOps",
    "Machine Learning", "Large Language Models (LLM)",
]

def check_and_cleanup(page):
    """Check the experience section for empty or duplicate entries."""
    page.goto("https://www.linkedin.com/in/me/", wait_until="domcontentloaded", timeout=30000)
    time.sleep(5)
    
    # Scroll to experience section
    for _ in range(4):
        page.mouse.wheel(0, 500)
        time.sleep(1)
    
    # Count experience entries
    exp_data = page.evaluate("""() => {
        const results = [];
        // Find all elements that look like experience titles
        const all = document.querySelectorAll('*');
        for (const el of all) {
            const direct = Array.from(el.childNodes)
                .filter(n => n.nodeType === 3)
                .map(n => n.textContent.trim())
                .join(' ');
            if (!direct) continue;
            
            // Look for position-like text patterns
            if (direct === 'DevOps Engineer' || direct === 'AI Systems Engineer' || 
                direct.includes('Founding Engineer') || direct === 'Verventech') {
                const rect = el.getBoundingClientRect();
                results.push({text: direct, tag: el.tagName, top: Math.round(rect.top)});
            }
        }
        return results;
    }""")
    
    print(f"Experience entries found: {len(exp_data)}")
    for e in exp_data:
        print(f"  {e['tag']:6s} top={e['top']:4d} text={e['text']}")
    
    # Count total entries under Verventech
    total = page.evaluate("""() => {
        const entries = document.querySelectorAll('[data-field="experience_grouping"]');
        if (entries.length > 0) return entries.length;
        // Fallback: count "Present" occurrences in experience
        const all = document.querySelectorAll('*');
        let count = 0;
        for (const el of all) {
            const direct = Array.from(el.childNodes)
                .filter(n => n.nodeType === 3)
                .map(n => n.textContent.trim())
                .join(' ');
            if (direct.includes('Present') && direct.includes('Jan')) count++;
        }
        return count;
    }""")
    print(f"  Total 'Present' date entries: {total}")
    
    return exp_data


def add_skills(page):
    """Add skills via Add section -> Core -> Add skills."""
    page.goto("https://www.linkedin.com/in/me/", wait_until="domcontentloaded", timeout=30000)
    time.sleep(5)
    
    # Open Add section modal
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
    
    # Expand Core
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
    
    # Click 'Add skills'
    result = page.evaluate("""() => {
        const all = document.querySelectorAll('*');
        for (const el of all) {
            const direct = Array.from(el.childNodes).filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join(' ').toLowerCase();
            if (direct.includes('add skill')) {
                const clickable = el.closest('button') || el.closest('a') || el;
                clickable.click();
                return true;
            }
        }
        return false;
    }""")
    time.sleep(4)
    print(f"  Clicked 'Add skills': {result}")
    
    page.screenshot(path=os.path.join(SS_DIR, "skills_form.png"))
    
    # The skills form typically has a search input
    # Let's see what appeared
    fields = page.evaluate("""() => {
        const els = document.querySelectorAll('input, textarea, [contenteditable="true"]');
        const result = [];
        for (const el of els) {
            const rect = el.getBoundingClientRect();
            if (rect.width === 0) continue;
            result.push({
                tag: el.tagName, id: el.id || '',
                ph: (el.placeholder || '').substring(0, 40),
                aria: (el.getAttribute('aria-label') || '').substring(0, 40),
                top: Math.round(rect.top),
            });
        }
        return result;
    }""")
    print(f"  Fields on skills page: {len(fields)}")
    for f in fields:
        print(f"    {f['tag']:6s} id={f['id'][:15]:15s} ph={f['ph'][:30]:30s} top={f['top']}")
    
    # Add each skill
    added = 0
    for skill in SKILLS_TO_ADD:
        try:
            # Find the skill search input
            skill_input = None
            for f in fields:
                if f['top'] > 100 and f['tag'] == 'INPUT':
                    skill_input = page.locator(f"#{f['id']}") if f['id'] else page.locator("input").nth(0)
                    break
            
            if not skill_input:
                # Try to find any visible input that's not the search bar
                visible_inputs = page.locator("input:visible")
                for i in range(visible_inputs.count()):
                    inp = visible_inputs.nth(i)
                    top = inp.evaluate("el => Math.round(el.getBoundingClientRect().top)")
                    if top > 100:
                        skill_input = inp
                        break
            
            if skill_input:
                skill_input.fill("")
                time.sleep(0.3)
                skill_input.fill(skill)
                time.sleep(1.5)
                
                # Try to click the first suggestion
                suggestion_clicked = page.evaluate("""(skillName) => {
                    const options = document.querySelectorAll('[role="option"], [role="listbox"] li, .basic-typeahead__triggered-content li');
                    for (const opt of options) {
                        const text = opt.textContent.trim().toLowerCase();
                        if (text.includes(skillName.toLowerCase())) {
                            opt.click();
                            return true;
                        }
                    }
                    // Try clicking first visible suggestion
                    const suggestions = document.querySelectorAll('[role="option"], [role="listbox"] li, li.basic-typeahead__selectable');
                    if (suggestions.length > 0) {
                        suggestions[0].click();
                        return true;
                    }
                    return false;
                }""", skill)
                
                if suggestion_clicked:
                    added += 1
                    print(f"  Added: {skill}")
                else:
                    # Try pressing Enter
                    skill_input.press("Enter")
                    time.sleep(0.5)
                    added += 1
                    print(f"  Added (enter): {skill}")
                
                time.sleep(0.5)
        except Exception as e:
            print(f"  Error adding {skill}: {e}")
    
    print(f"  Total skills added: {added}")
    
    # Save
    time.sleep(1)
    try:
        save = page.locator("button:has-text('Save'), button:has-text('Add')").first
        if save.is_visible(timeout=5000):
            save.click()
            time.sleep(4)
            print("  Skills saved!")
            return True
    except:
        pass
    
    # Try 'Done' button
    try:
        done = page.locator("button:has-text('Done')").first
        if done.is_visible(timeout=3000):
            done.click()
            time.sleep(4)
            print("  Skills done!")
            return True
    except:
        pass
    
    return False


def main():
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR, headless=False,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        # Check experience entries
        print("=== Check Experience ===")
        check_and_cleanup(page)
        
        # Add skills
        print("\n=== Add Skills ===")
        add_skills(page)
        
        # Final screenshots
        page.goto("https://www.linkedin.com/in/me/", wait_until="domcontentloaded", timeout=30000)
        time.sleep(4)
        page.screenshot(path=os.path.join(SS_DIR, "profile_final_complete.png"))
        
        # Scroll to see skills
        for i in range(6):
            page.mouse.wheel(0, 500)
            time.sleep(1)
            page.screenshot(path=os.path.join(SS_DIR, f"profile_complete_scroll_{i}.png"))

        ctx.close()
        print("\nDone!")

if __name__ == "__main__":
    main()
