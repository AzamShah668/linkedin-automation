#!/usr/bin/env python3
"""Unified LinkedIn Content Dispatch Engine.

    py -3 tools/post_creator/dispatch_engine.py --dry-run      # preview what would post
    py -3 tools/post_creator/dispatch_engine.py --post-id 5    # dispatch a specific post
    py -3 tools/post_creator/dispatch_engine.py                # dispatch today's approved post
    py -3 tools/post_creator/dispatch_engine.py --generate-image --post-id 5  # generate image only

Reads the Content Hub database, finds today's approved post, generates the
hero image (or uses a pre-built PDF carousel for project posts), and dispatches
to LinkedIn via Playwright. Updates status to 'posted' on success.

Stdlib + Pillow + Playwright.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import random
import sys
from pathlib import Path

# Setup paths
TOOLS_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = TOOLS_DIR.parent
sys.path.insert(0, str(TOOLS_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from content_hub_db import connect, get_todays_post, mark_posted, approve_post, _get_post  # noqa: E402

TEMPLATES_PATH = Path(__file__).resolve().parent / "prompt_templates.json"
OUTPUT_DIR = PROJECT_ROOT / "output" / "posts"
USER_DATA_DIR = PROJECT_ROOT / ".pw_browser" / "linkedin_user_data"


def load_templates() -> dict:
    """Load image prompt templates."""
    with open(TEMPLATES_PATH, encoding="utf-8") as f:
        return json.load(f)


def build_image_prompt(post: dict, templates: dict) -> str:
    """Build a randomized image prompt based on the post type."""
    post_type = post.get("post_type", "daily-build")
    template_data = templates.get(post_type)

    if not template_data or template_data.get("format") == "pdf-carousel":
        return ""  # Project posts use PDF carousels, not generated images

    prompt_template = template_data["prompt_template"]
    variables = template_data.get("variables", {})

    # Randomly select one value for each variable
    replacements = {}
    for var_name, options in variables.items():
        replacements[var_name] = random.choice(options)

    # Apply replacements
    prompt = prompt_template
    for var_name, value in replacements.items():
        prompt = prompt.replace(f"{{{var_name}}}", value)

    return prompt


def generate_hero_image(prompt: str, post_id: int) -> str:
    """Generate a hero image using the image studio. Returns the file path."""
    from image_studio import create_high_res_image

    output_dir = str(OUTPUT_DIR / "hero_images")
    filename = f"hero_post_{post_id}_{int(dt.datetime.now().timestamp())}.png"

    print(f"[Dispatch] Generating hero image via FLUX.1...")
    result = create_high_res_image(
        prompt=prompt,
        aspect_ratio="4:5",
        output_dir=output_dir,
        filename=filename,
        style_preset="3d-render",
    )
    print(f"[Dispatch] Image saved: {result['file_path']}")
    return result["file_path"]


def dispatch_to_linkedin(
    post_copy: str,
    media_paths: list[str],
    headless: bool = False,
) -> dict:
    """Post to LinkedIn via Playwright with persistent browser session."""
    from playwright.sync_api import sync_playwright
    import time

    os.makedirs(str(USER_DATA_DIR), exist_ok=True)

    print("[Dispatch] Launching Playwright browser...")
    with sync_playwright() as p:
        browser_context = p.chromium.launch_persistent_context(
            user_data_dir=str(USER_DATA_DIR),
            headless=headless,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )

        page = browser_context.pages[0] if browser_context.pages else browser_context.new_page()
        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=60000)
        time.sleep(4)

        # Check login
        if "login" in page.url or "signup" in page.url:
            print("[Dispatch] LinkedIn session not logged in. Please log in manually.")
            page.wait_for_url("**/feed/**", timeout=120000)
            time.sleep(3)

        # Click Start a post
        print("[Dispatch] Opening post editor...")
        try:
            page.click("button:has-text('Start a post')", timeout=10000)
        except Exception:
            page.click(".share-mb__starter", timeout=10000)
        time.sleep(2)

        # Upload media
        if media_paths:
            print(f"[Dispatch] Attaching {len(media_paths)} media file(s)...")
            try:
                file_input = page.locator("input[type='file']")
                file_input.set_input_files(media_paths)
                time.sleep(3)
            except Exception as e:
                print(f"[Warning] File upload: {e}")

            # Click Next if modal appears
            try:
                if page.locator("button:has-text('Next')").is_visible():
                    page.click("button:has-text('Next')")
                    time.sleep(2)
            except Exception:
                pass

        # Enter post text
        print("[Dispatch] Entering post copy...")
        try:
            editor = page.locator(".ql-editor, div[contenteditable='true']").first
            editor.fill(post_copy)
            time.sleep(2)
        except Exception as e:
            print(f"[Error] Text fill failed: {e}")
            browser_context.close()
            return {"status": "error", "message": str(e)}

        # Click Post
        print("[Dispatch] Clicking Post button...")
        try:
            post_button = page.locator(
                "button.share-actions__primary-action, button:has-text('Post')"
            ).first
            if post_button.is_enabled():
                post_button.click()
                print("[Dispatch] POST DISPATCHED TO LINKEDIN!")
                time.sleep(5)
                browser_context.close()
                return {"status": "success", "message": "Post dispatched to LinkedIn"}
        except Exception as e:
            print(f"[Notice] Post button: {e}")

        time.sleep(3)
        browser_context.close()
        return {"status": "prepared", "message": "Post prepared in LinkedIn editor"}


def send_slack_notification(post: dict, status: str) -> None:
    """Send a Slack notification about the post status."""
    try:
        env_path = PROJECT_ROOT / ".env"
        token = None
        channel = None
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                if line.startswith("SLACK_BOT_TOKEN="):
                    token = line.partition("=")[2].strip()
                elif line.startswith("SLACK_CHANNEL_ID="):
                    channel = line.partition("=")[2].strip()

        if not token or not channel:
            return

        emoji = {"drafted": "pencil", "approved": "white_check_mark",
                 "posted": "rocket", "error": "x"}.get(status, "bell")

        text = (
            f":{emoji}: *LinkedIn Content Hub*\n"
            f"*{post['title']}*\n"
            f"Type: `{post['post_type']}` | Status: `{status}`\n"
        )
        if status == "drafted":
            text += "_Ready for your approval in Notion._"

        payload = json.dumps({"channel": channel, "text": text}).encode("utf-8")
        req = urllib.request.Request(
            "https://slack.com/api/chat.postMessage",
            data=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )
        import urllib.request
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"[Slack] Notification failed: {e}")


def main() -> None:
    parser = argparse.ArgumentParser(description="LinkedIn Content Dispatch Engine")
    parser.add_argument("--post-id", type=int, help="Dispatch a specific post by ID")
    parser.add_argument("--dry-run", action="store_true", help="Preview without posting")
    parser.add_argument("--generate-image", action="store_true", help="Generate image only (no post)")
    parser.add_argument("--headless", action="store_true", help="Run browser headless")
    parser.add_argument("--approve-and-post", action="store_true",
                        help="Auto-approve then post (for scheduled tasks)")
    args = parser.parse_args()

    conn = connect()
    templates = load_templates()

    # Get the post to dispatch
    if args.post_id:
        post = _get_post(conn, args.post_id)
        if not post:
            print(f"[Error] Post #{args.post_id} not found.")
            sys.exit(1)
    else:
        post = get_todays_post(conn)
        if not post:
            print("[Info] No approved post for today. Nothing to dispatch.")
            print("  Use: py -3 tools/log_experience.py --list  to see all posts")
            print("  Use: py -3 tools/post_creator/dispatch_engine.py --post-id N  for a specific post")
            sys.exit(0)

    print(f"[Dispatch] Post #{post['id']}: {post['title']}")
    print(f"  Type: {post['post_type']} | Status: {post['status']}")

    # Auto-approve if requested
    if args.approve_and_post and post["status"] in ("idea", "drafted"):
        print(f"[Dispatch] Auto-approving post #{post['id']}...")
        post = approve_post(conn, post["id"])

    # Determine media strategy
    is_project = post["post_type"] == "project"
    media_paths: list[str] = []

    if is_project:
        # Project posts use PDF carousel or existing screenshots
        carousel_dir = OUTPUT_DIR / "carousel_bundle"
        if post.get("media_path") and os.path.exists(post["media_path"]):
            media_paths = [post["media_path"]]
        elif carousel_dir.exists():
            pdfs = list(carousel_dir.glob("*.pdf"))
            if pdfs:
                media_paths = [str(pdfs[0])]
        print(f"  Media: PDF Carousel ({len(media_paths)} file(s))")
    else:
        # Non-project posts get a generated hero image
        image_prompt = build_image_prompt(post, templates)
        if image_prompt:
            if args.dry_run:
                print(f"\n[DRY RUN] Would generate image with prompt:")
                print(f"  {image_prompt[:200]}...")
            else:
                image_path = generate_hero_image(image_prompt, post["id"])
                media_paths = [image_path]
        print(f"  Media: Hero Image ({len(media_paths)} file(s))")

    # Build the copy
    post_copy = post.get("copy") or ""
    if not post_copy:
        # Minimal fallback copy from title + insight
        post_copy = f"{post['title']}\n\n{post.get('insight', '')}"
        if post.get("hashtags"):
            post_copy += f"\n\n{post['hashtags']}"

    if args.dry_run:
        print(f"\n[DRY RUN] Would dispatch:")
        print(f"  Title: {post['title']}")
        print(f"  Type:  {post['post_type']}")
        print(f"  Media: {media_paths or '(none)'}")
        print(f"  Copy preview ({len(post_copy)} chars):")
        print(f"  {post_copy[:300]}...")
        return

    if args.generate_image:
        print("[Done] Image generated. Not posting.")
        return

    # Dispatch to LinkedIn
    result = dispatch_to_linkedin(
        post_copy=post_copy,
        media_paths=media_paths,
        headless=args.headless,
    )

    if result["status"] == "success":
        updated = mark_posted(
            conn, post["id"],
            image_path=media_paths[0] if media_paths else None,
            media_path=media_paths[0] if media_paths else None,
        )
        send_slack_notification(post, "posted")
        print(f"\n[SUCCESS] Post #{post['id']} dispatched and marked as posted!")
    else:
        print(f"\n[{result['status'].upper()}] {result['message']}")


if __name__ == "__main__":
    main()
