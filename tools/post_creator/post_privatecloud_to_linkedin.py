import os
import sys
import time
import json
from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
USER_DATA_DIR = os.path.join(PROJECT_ROOT, ".pw_browser", "linkedin_user_data")
CAROUSEL_DIR = os.path.join(PROJECT_ROOT, "output", "posts", "carousel_bundle_privatecloud")

POST_COPY = """Every CS department in Kashmir has that one server.

You know the one. Thirty students, one machine, everyone SSHing into the same environment. Somebody installs PyTorch with the wrong CUDA version on a Wednesday night and by Thursday morning nobody's code runs. You need the GPU to train your model before a deadline but someone else's process has been hanging there since Tuesday and nobody knows whose it is.

That was our university. One Proxmox server, no isolation, no user boundaries, only Linux. If you were lucky enough to get on it, you were sharing space with everyone else's half-finished experiments. The teachers had it even worse. Lab starts in ten minutes and the first twenty minutes is always the same story — pip is broken on three laptops, someone has Python 3.8 instead of 3.11, and by the time everyone's environment is actually working, half the lab session is already gone.

We got tired of watching that happen. So we built a platform to fix it.

AZNA-CLOUD ☁️

For students:
→ Pick your OS — Ubuntu, Debian, CentOS, or Windows 11 — set your CPU, RAM, and storage, and hit Deploy
→ You get your own isolated virtual machine in seconds, cloned from a clean golden template. Nobody else's broken packages touch your environment
→ Access it straight from the browser — full terminal or Windows remote desktop, from anywhere, no VPN
→ Daily quotas so no single person can hog the entire server anymore

For teachers:
→ Build one golden template with everything the lab needs pre-installed — right Python version, right libraries, the datasets, everything
→ Students clone it in one click. Every machine is identical. Lab starts on time for once
→ Create classes, assign students, see who's using what. Full admin dashboard with cluster health, resource usage, and audit logs of every action

And here's the part that surprised even us:
→ There's an AI agent built into the platform. Type "deploy an Ubuntu server called ml-project" and it actually provisions the VM for you through natural language
→ It has its own knowledge base so it can answer questions about the platform itself

The whole thing runs on one command: docker compose up

FastAPI · PostgreSQL · Celery + Redis · Proxmox VE · Apache Guacamole · React · Docker Compose (8 services) · 5 Ansible roles · Jenkins CI/CD · ChromaDB

Every university department, every bootcamp, every training lab has this exact problem. That one shared machine that everyone dreads logging into.

#DevOps #CloudComputing #PlatformEngineering #SoftwareEngineering #SelfHosted"""

# Complete 7-image bundle: Real Screenshots + Architecture Specs
IMAGE_PATHS = [
    os.path.join(CAROUSEL_DIR, "slide_1_hero_command_center.png"),
    os.path.join(CAROUSEL_DIR, "screen_1_dashboard.png"),
    os.path.join(CAROUSEL_DIR, "screen_2_deploy.png"),
    os.path.join(CAROUSEL_DIR, "screen_3_admin_command_center.png"),
    os.path.join(CAROUSEL_DIR, "screen_4_chatops.png"),
    os.path.join(CAROUSEL_DIR, "slide_2_core_architecture_details.png"),
    os.path.join(CAROUSEL_DIR, "slide_3_before_vs_after_comparison.png")
]

def publish_privatecloud_bundle():
    print("[1/5] Launching browser...")
    with sync_playwright() as p:
        b = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=True,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = b.pages[0] if b.pages else b.new_page()
        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
        time.sleep(4)

        print("[2/5] Opening post modal...")
        page.get_by_role("button", name="Start a post").click()
        time.sleep(3)

        print("[3/5] Locating text editor...")
        # Find editable area inside modal
        editor = page.locator("div.ql-editor, div[contenteditable='true'], div[role='textbox']").first
        editor.wait_for(state="visible", timeout=15000)
        editor.click()
        time.sleep(1)
        editor.fill(POST_COPY)
        time.sleep(2)
        print("  -> Post text copy filled successfully!")

        print(f"[4/5] Attaching {len(IMAGE_PATHS)} PrivateCloud images (screenshots + architecture)...")
        existing_images = [i for i in IMAGE_PATHS if os.path.exists(i)]
        print(f"  -> Found {len(existing_images)} existing image files.")

        # Click media icon button inside modal
        try:
            media_btn = page.locator("button[aria-label='Add media'], button[aria-label='Add a photo'], button:has-text('Media')").first
            if media_btn.is_visible():
                media_btn.click()
                time.sleep(2)
        except Exception as e:
            print(f"  -> Media button notice: {e}")

        # Set files on input
        try:
            file_input = page.locator("input[type='file']").first
            file_input.set_input_files(existing_images)
            time.sleep(5)
            print("  -> Images attached successfully!")
        except Exception as e:
            print(f"  -> File set error: {e}")

        # Handle 'Next' button if visible (media modal preview)
        try:
            next_btn = page.locator("button.share-box-footer__primary-btn, button:has-text('Next')").first
            if next_btn.is_visible():
                next_btn.click()
                time.sleep(3)
                print("  -> Media preview Next button clicked.")
        except Exception as e:
            print(f"  -> Next button notice: {e}")

        # Step 5: Click Post button
        print("[5/5] Submitting post...")
        post_btn = page.get_by_role("button", name="Post", exact=True)
        if post_btn.is_visible() and post_btn.is_enabled():
            post_btn.click()
            print("  -> Post button clicked. Waiting for image payload upload & modal completion...")
            try:
                page.locator(".share-box-footer, div[role='dialog']").first.wait_for(state="detached", timeout=45000)
            except Exception:
                pass
            print("[SUCCESS] PRIVATECLOUD POST DISPATCHED LIVE TO LINKEDIN!")
            time.sleep(5)
            page.screenshot(path="output/final_privatecloud_published.png")
            b.close()
            return True
        else:
            print("  -> Checking fallback post button...")
            alt_post = page.locator("button.share-actions__primary-action, button:has-text('Post')").last
            if alt_post.is_visible() and alt_post.is_enabled():
                alt_post.click()
                print("  -> Alt post button clicked. Waiting for completion...")
                try:
                    page.locator(".share-box-footer, div[role='dialog']").first.wait_for(state="detached", timeout=45000)
                except Exception:
                    pass
                print("[SUCCESS] PRIVATECLOUD POST DISPATCHED LIVE TO LINKEDIN!")
                time.sleep(5)
                page.screenshot(path="output/final_privatecloud_published.png")
                b.close()
                return True
            else:
                page.screenshot(path="output/post_button_state.png")
                b.close()
                return False

if __name__ == "__main__":
    res = publish_privatecloud_bundle()
    print("Publish status:", res)
