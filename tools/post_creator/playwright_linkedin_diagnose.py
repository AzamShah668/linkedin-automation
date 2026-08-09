"""Quick check: scroll the profile to see the experience section."""
import os, time
from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
USER_DATA_DIR = os.path.join(PROJECT_ROOT, ".pw_browser", "linkedin_user_data")
SS_DIR = os.path.join(PROJECT_ROOT, "output", "linkedin")

def check():
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR, headless=False,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        
        page.goto("https://www.linkedin.com/in/me/", wait_until="domcontentloaded", timeout=60000)
        time.sleep(5)
        
        # Take multiple screenshots scrolling down
        for i in range(5):
            ss = os.path.join(SS_DIR, f"profile_scroll_{i}.png")
            page.screenshot(path=ss)
            print(f"Screenshot {i}: {ss}")
            page.mouse.wheel(0, 600)
            time.sleep(1.5)
        
        ctx.close()

if __name__ == "__main__":
    check()
