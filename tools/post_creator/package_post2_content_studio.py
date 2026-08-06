"""
Post 2 Packager — AI Visual Content Studio
Packages the ALREADY-BUILT 4-slide carousel with the approved Post 2 copy.
This post goes out FIRST as a teaser.
"""

import os
import json
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CAROUSEL_DIR = os.path.join(PROJECT_ROOT, "output", "posts", "carousel_bundle")
PACKAGES_DIR = os.path.join(PROJECT_ROOT, "output", "posts", "packages")

POST_2_COPY = """I got tired of posting on LinkedIn with generic stock images and AI-written walls of text.

So I built an AI Visual Content Studio that generates both the post copy AND custom 8K carousel visuals — automatically.

Here is how the pipeline works:

INPUT: A topic or context (e.g., "Scaling RAG Pipelines with Vector DBs")

STAGE 1: CONTENT ENGINE
-> Researches the topic against my real engineering projects
-> Generates LinkedIn copy in a proven 5-part framework (Hook -> Problem -> Architecture -> Takeaways -> CTA)
-> Frames everything as personal proof-of-work, never generic thought leadership

STAGE 2: VISUAL STUDIO
-> Generates a 3D Command Center hero cover image via FLUX.1 / Imagen 3
-> Renders a high-density architecture specs card (Space Grotesk typography, real code file paths)
-> Creates dual 3D character avatars for before/after comparison
-> Builds an operational roadmap card with embedded 3D robot flowchart

STAGE 3: PACKAGING
-> Bundles post copy + 4 carousel slides into a ready-to-publish JSON package
-> Dispatches via MCP server protocol — no manual file handling

The engineering behind the visuals:
* Edge headless HTML-to-PNG rendering for pixel-perfect vector cards
* Google Font embedding (Space Grotesk, Outfit) for premium typography
* AI image generation with text-inside-quotes prompting for crisp label rendering
* Zero dead margins — every pixel of every slide is intentional

The system that made this post also made this carousel. Meta, right?

COMING NEXT: The autonomous job hunt autopilot that this studio was built to serve. 62 jobs discovered. 5 applied. 0 bounces. Stay tuned.

What content workflow would you automate if you could? Drop your ideas below.

#AI #ContentCreation #Automation #LinkedIn #Python #MCP #VisualDesign #SoftwareEngineering"""


def package_post_2():
    os.makedirs(PACKAGES_DIR, exist_ok=True)
    post_id = f"post2_content_studio_{int(time.time())}"

    bundle = {
        "post_id": post_id,
        "series": "LinkedIn Two-Post Series",
        "post_number": 2,
        "post_title": "AI Visual Content Studio",
        "posting_order": "FIRST (teaser)",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "post_body": POST_2_COPY,
        "carousel_slides": [
            {"slide": 1, "file": os.path.join(CAROUSEL_DIR, "slide_1_hero_command_center.png"), "desc": "3D Command Center Hero Cover"},
            {"slide": 2, "file": os.path.join(CAROUSEL_DIR, "slide_2_core_architecture_details.png"), "desc": "Space Grotesk 5-Layer Specs Card"},
            {"slide": 3, "file": os.path.join(CAROUSEL_DIR, "slide_3_before_vs_after_comparison.png"), "desc": "Dual 3D Avatars: Stressed vs Happy"},
            {"slide": 4, "file": os.path.join(CAROUSEL_DIR, "slide_4_operational_roadmap_cta.png"), "desc": "3D Robot Flowchart + Outfit Roadmap"},
        ],
        "status": "ready_to_post",
        "teaser_for": "Post 1 — Autonomous Job Hunt Autopilot (drops 2-3 days later)"
    }

    pkg_path = os.path.join(PACKAGES_DIR, f"{post_id}_package.json")
    with open(pkg_path, "w", encoding="utf-8") as f:
        json.dump(bundle, f, indent=2)

    # Verify all slides exist
    missing = [s for s in bundle["carousel_slides"] if not os.path.exists(s["file"])]

    print("=================================================================")
    print("[POST 2] AI Visual Content Studio — PACKAGE READY")
    print("=================================================================")
    print(f"Package: {pkg_path}")
    for s in bundle["carousel_slides"]:
        exists = "OK" if os.path.exists(s["file"]) else "MISSING"
        print(f"  Slide {s['slide']}: [{exists}] {s['file']}")

    if missing:
        print(f"\n[WARNING] {len(missing)} slide(s) missing!")
    else:
        print("\n[OK] All 4 slides verified on disk.")

    print("\n--- POST 2 COPY (dispatch FIRST as teaser) ---\n")
    print(POST_2_COPY)
    return pkg_path


if __name__ == "__main__":
    package_post_2()
