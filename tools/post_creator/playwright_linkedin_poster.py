"""
Automated Playwright LinkedIn Post Dispatcher
Uses Playwright browser automation to launch LinkedIn, navigate to the post editor, attach the 4 carousel slide images, enter the post text, and post automatically!
"""

import os
import sys
import time
import json
from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CAROUSEL_DIR = os.path.join(PROJECT_ROOT, "output", "posts", "carousel_bundle")
USER_DATA_DIR = os.path.join(PROJECT_ROOT, ".pw_browser", "linkedin_user_data")

def auto_post_to_linkedin(
    post_copy: str = None,
    slide_paths: list = None,
    headless: bool = False
) -> dict:
    """
    Automates posting to LinkedIn using Playwright Chromium with persistent user profile.
    """
    if not slide_paths:
        slide_paths = [
            os.path.join(CAROUSEL_DIR, "slide_1_hero_command_center.png"),
            os.path.join(CAROUSEL_DIR, "slide_2_core_architecture_details.png"),
            os.path.join(CAROUSEL_DIR, "slide_3_before_vs_after_comparison.png"),
            os.path.join(CAROUSEL_DIR, "slide_4_operational_roadmap_cta.png")
        ]

    if not post_copy:
        post_copy = (
            "Here is the exact system architecture behind my Autonomous LinkedIn Job Hunt Autopilot.\n\n"
            "Building scalable automation requires clear separation of concerns, persistent state tracking, and agentic protocols.\n\n"
            "Here is how the 5 layers connect:\n\n"
            "1. Client & Interface: 1-Tap Mobile approval via Slack webhooks & live web dashboard.\n"
            "2. Protocol Gateway: Stdio RPC MCP Server Hub managing browser tools.\n"
            "3. Core Services: Autonomous Playwright discovery & stealth outreach runners.\n"
            "4. AI & Visual Creator: FLUX.1 & Imagen 3 visual studio engine.\n"
            "5. Data Storage: Two-way Notion cloud database & SQLite3 state store.\n\n"
            "Key Insights:\n"
            "• Architecture-first approach to autonomous job hunt autopilot.\n"
            "• Human-in-the-Loop approval safeguards for 100% control.\n"
            "• Model Context Protocol (MCP) for zero-latency tool orchestration.\n\n"
            "Check out the 4-slide breakdown in the carousel images below! What workflow are you building this week? Let us discuss in the comments!\n\n"
            "#SoftwareEngineering #AI #Automation #LinkedIn #Architecture #Python"
        )

    os.makedirs(USER_DATA_DIR, exist_ok=True)
    print("=================================================================")
    print("[Automated LinkedIn Poster] Launching Playwright Browser...")
    print("=================================================================")

    with sync_playwright() as p:
        # Launch browser with persistent session context so login cookies are preserved
        browser_context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=headless,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"]
        )

        page = browser_context.pages[0] if browser_context.pages else browser_context.new_page()
        print("[Playwright] Navigating to LinkedIn Feed...")
        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=60000)
        time.sleep(4)

        # Check if user needs to log in
        if "login" in page.url or "signup" in page.url or page.locator("input#username").is_visible():
            print("\n[ATTENTION] LinkedIn session not logged in yet.")
            print("[Playwright] Please log into your LinkedIn account in the browser window...")
            page.wait_for_url("**/feed/**", timeout=120000)
            time.sleep(3)

        print("[Playwright] Logged in successfully! Clicking 'Start a post'...")
        
        # Click start a post button
        try:
            page.click("button:has-text('Start a post')", timeout=10000)
        except Exception:
            page.click(".share-mb__starter", timeout=10000)

        time.sleep(2)

        # Click media upload / photo button
        print("[Playwright] Attaching 4 Carousel Slide Images...")
        try:
            # Upload media files directly to file input
            file_input = page.locator("input[type='file']")
            file_input.set_input_files(slide_paths)
            time.sleep(3)
        except Exception as e:
            print(f"[Warning] Direct file upload element error: {e}")

        # Click Next if media modal pops up
        try:
            if page.locator("button:has-text('Next')").is_visible():
                page.click("button:has-text('Next')")
                time.sleep(2)
        except Exception:
            pass

        # Enter Post Text
        print("[Playwright] Entering Post Text Copy...")
        try:
            editor = page.locator(".ql-editor, div[contenteditable='true']").first
            editor.fill(post_copy)
            time.sleep(2)
        except Exception as e:
            print(f"[Error] Text fill failed: {e}")

        # Final Post Action
        print("[Playwright] Clicking 'Post' Button...")
        try:
            post_button = page.locator("button.share-actions__primary-action, button:has-text('Post')").first
            if post_button.is_enabled():
                post_button.click()
                print("🎉 [SUCCESS] POST SUCCESSFULLY DISPATCHED TO LINKEDIN!")
                time.sleep(5)
                browser_context.close()
                return {"status": "success", "message": "Post dispatchedd to LinkedIn live!"}
            else:
                print("[Info] Post button ready for final manual confirmation.")
        except Exception as e:
            print(f"[Notice] Final click ready: {e}")

        time.sleep(5)
        browser_context.close()
        return {"status": "prepared", "message": "Post prepped in LinkedIn editor!"}

if __name__ == "__main__":
    auto_post_to_linkedin(headless=False)
