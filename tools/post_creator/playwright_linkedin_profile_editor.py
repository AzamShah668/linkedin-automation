"""
LinkedIn Profile Editor v6 — TARGETED.
The headline is a TipTap ProseMirror contenteditable div (class="tiptap ProseMirror ...").
It's inside the "Edit intro" modal, between the name fields and Industry.
Strategy: open modal -> scroll to reveal the ProseMirror editor -> click -> Ctrl+A -> type new headline -> Save.
"""
import os, time
from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
USER_DATA_DIR = os.path.join(PROJECT_ROOT, ".pw_browser", "linkedin_user_data")

NEW_HEADLINE = "DevOps & AI Engineer | Kubernetes \u00b7 Docker \u00b7 Jenkins \u00b7 Ansible \u00b7 RAG \u00b7 LLMs | Built a 7-service private cloud + GPU K8s cluster | Open to work"

def edit_profile():
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

        # ── Open Edit Intro modal ──
        print("[2] Clicking edit pencil...")
        page.mouse.click(825, 315)
        time.sleep(4)

        # ── Scroll modal so the ProseMirror editor is in view ──
        # The ProseMirror div was at top=872 when modal was scrolled to top.
        # We need to scroll the modal down a bit from the initial position.
        print("[3] Scrolling modal to reveal headline editor...")
        page.mouse.move(630, 400)
        # Scroll down slowly to bring the ProseMirror field into view
        page.mouse.wheel(0, 300)
        time.sleep(1)

        # ── Find and click the ProseMirror editor ──
        print("[4] Locating TipTap ProseMirror contenteditable div...")
        
        prosemirror = page.locator("div.tiptap.ProseMirror, div.ProseMirror[contenteditable='true']").first
        
        try:
            if prosemirror.is_visible(timeout=5000):
                current_text = prosemirror.inner_text(timeout=3000)
                print(f"    Found! Current text: {current_text[:80]}...")
                
                # Click to focus
                prosemirror.click()
                time.sleep(0.5)
                
                # Select all text and replace
                page.keyboard.press("Control+a")
                time.sleep(0.3)
                page.keyboard.press("Backspace")
                time.sleep(0.3)
                
                # Type new headline
                page.keyboard.type(NEW_HEADLINE, delay=10)
                time.sleep(1)
                
                # Verify
                new_text = prosemirror.inner_text(timeout=3000)
                print(f"    New text: {new_text[:80]}...")
                print(f"    HEADLINE FILLED!")
                filled = True
            else:
                print("    ProseMirror not visible, trying scroll + retry...")
                # Scroll more
                page.mouse.wheel(0, 300)
                time.sleep(1.5)
                
                prosemirror = page.locator("div.tiptap.ProseMirror, div.ProseMirror[contenteditable='true']").first
                if prosemirror.is_visible(timeout=5000):
                    prosemirror.click()
                    time.sleep(0.5)
                    page.keyboard.press("Control+a")
                    time.sleep(0.3)
                    page.keyboard.press("Backspace")
                    time.sleep(0.3)
                    page.keyboard.type(NEW_HEADLINE, delay=10)
                    filled = True
                    print(f"    HEADLINE FILLED after extra scroll!")
                else:
                    print("    Still not visible. Trying JS scroll into view...")
                    page.evaluate("""() => {
                        const el = document.querySelector('div.tiptap.ProseMirror, div.ProseMirror[contenteditable]');
                        if (el) el.scrollIntoView({behavior: 'smooth', block: 'center'});
                    }""")
                    time.sleep(2)
                    prosemirror.click()
                    page.keyboard.press("Control+a")
                    time.sleep(0.3)
                    page.keyboard.press("Backspace")
                    time.sleep(0.3)
                    page.keyboard.type(NEW_HEADLINE, delay=10)
                    filled = True
                    print(f"    HEADLINE FILLED via JS scroll!")
        except Exception as e:
            print(f"    Error: {e}")
            filled = False

        # ── Screenshot the filled state ──
        ss = os.path.join(PROJECT_ROOT, "output", "linkedin", "modal_v6_filled.png")
        os.makedirs(os.path.dirname(ss), exist_ok=True)
        page.screenshot(path=ss)
        print(f"\n[5] Modal screenshot: {ss}")

        # ── Click Save ──
        if filled:
            print("[6] Clicking Save...")
            save_btns = page.locator("button:has-text('Save')")
            for i in range(save_btns.count()):
                btn = save_btns.nth(i)
                if btn.is_visible():
                    btn.click()
                    print(f"    Save clicked!")
                    time.sleep(5)
                    break

            # ── Final screenshot ──
            page.goto("https://www.linkedin.com/in/me/", wait_until="domcontentloaded", timeout=30000)
            time.sleep(4)
            final = os.path.join(PROJECT_ROOT, "output", "linkedin", "profile_after_headline.png")
            page.screenshot(path=final)
            print(f"[7] Final profile: {final}")
        else:
            print("[6] Skipping save - headline not filled")

        ctx.close()
        print(f"\nHeadline filled: {filled}")

if __name__ == "__main__":
    edit_profile()
