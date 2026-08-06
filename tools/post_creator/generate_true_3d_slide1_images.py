"""
True 3D AI Command Center Slide 1 Image Generator
Follows the master skill viral-architecture-visualizer to generate 2 brand-new, photorealistic 3D Command Center hero images directly via FLUX.1 / Imagen 3.
- Post 1 Slide 1: Autonomous Job Hunt Autopilot
- Post 2 Slide 1: AI Visual Content Studio
"""

import os
import sys
import shutil

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
POST_CREATOR_DIR = os.path.join(PROJECT_ROOT, "tools", "post_creator")
sys.path.insert(0, POST_CREATOR_DIR)

from image_studio import create_high_res_image

POST1_CAROUSEL_DIR = os.path.join(PROJECT_ROOT, "output", "posts", "carousel_bundle_post1")
POST2_CAROUSEL_DIR = os.path.join(PROJECT_ROOT, "output", "posts", "carousel_bundle")

def generate_true_3d_slide1_covers():
    os.makedirs(POST1_CAROUSEL_DIR, exist_ok=True)
    os.makedirs(POST2_CAROUSEL_DIR, exist_ok=True)

    print("=================================================================")
    print("[3D AI Visual Studio] Generating True 3D AI Command Center Covers...")
    print("=================================================================")

    # 1. Post 1 Slide 1: Autonomous Job Hunt Autopilot
    print("\n[Post 1 Slide 1] Generating 3D AI Command Center via FLUX.1 for Job Hunt Autopilot...")
    p1_prompt = (
        'A cinematic high-tech sci-fi command center architecture diagram on a dark slate cybernetic background (#030712). '
        'At the top, the title "AUTONOMOUS JOB HUNT AUTOPILOT" glows in bright cyan neon text. '
        'On the left side: A 3D human developer standing looking at the command center with determination. '
        'On the right side: A sleek glowing futuristic AI robot agent standing with a digital HUD tablet operating the recruitment system. '
        'In the center: A giant glowing cyan and orange neon cybernetic control center screen displaying 5 stacked architecture layers labeled: '
        'Layer 1: "CLIENT & SLACK APPROVAL GATE". Layer 2: "AUTOMATED DISCOVERY ENGINE". Layer 3: "AI RESEARCH & CV TAILORING". Layer 4: "TWO-STAGE OUTREACH DISPATCH". Layer 5: "STATE STORE & TRACKING ENGINE". '
        'Background features glowing circuit lines, HUD telemetry widgets with "62 JOBS" and "0 BOUNCES" stats, blue and orange ambient lighting, aspect ratio 4:5, 8k resolution, photorealistic 3D render.'
    )
    p1_meta = create_high_res_image(prompt=p1_prompt, aspect_ratio="4:5", filename="post1_slide_1_hero.png")
    p1_path = os.path.join(POST1_CAROUSEL_DIR, "post1_slide_1_hero.png")
    if p1_meta["file_path"] != p1_path:
        shutil.copy(p1_meta["file_path"], p1_path)
    print(f"[OK] Post 1 Slide 1 3D Artwork Generated: {p1_path}")

    # 2. Post 2 Slide 1: AI Visual Content Studio
    print("\n[Post 2 Slide 1] Generating 3D AI Command Center via FLUX.1 for AI Content Studio...")
    p2_prompt = (
        'A cinematic high-tech sci-fi command center architecture diagram on a dark slate cybernetic background (#030712). '
        'At the top, the title "AI VISUAL CONTENT STUDIO" glows in bright cyan neon text. '
        'On the left side: A 3D human developer standing looking at the command center with determination. '
        'On the right side: A sleek glowing futuristic AI robot agent standing with a digital HUD tablet operating the visual studio engine. '
        'In the center: A giant glowing cyan and purple neon cybernetic control center screen displaying 5 stacked architecture layers labeled: '
        'Layer 1: "LLM PROOF COPYWRITER". Layer 2: "EDGE VECTOR RENDERER". Layer 3: "FLUX.1 & IMAGEN 3 ENGINE". Layer 4: "4-SLIDE CAROUSEL PACKAGER". Layer 5: "STDIO RPC MCP GATEWAY". '
        'Background features glowing circuit lines, HUD telemetry widgets with "8K HIGH-RES" and "MCP PROTOCOL" stats, blue and purple ambient lighting, aspect ratio 4:5, 8k resolution, photorealistic 3D render.'
    )
    p2_meta = create_high_res_image(prompt=p2_prompt, aspect_ratio="4:5", filename="slide_1_hero_command_center.png")
    p2_path = os.path.join(POST2_CAROUSEL_DIR, "slide_1_hero_command_center.png")
    if p2_meta["file_path"] != p2_path:
        shutil.copy(p2_meta["file_path"], p2_path)
    print(f"[OK] Post 2 Slide 1 3D Artwork Generated: {p2_path}")

    print("\n=================================================================")
    print("[SUCCESS] BOTH 3D AI COMMAND CENTER SLIDE 1 IMAGES GENERATED!")
    print("=================================================================")

if __name__ == "__main__":
    generate_true_3d_slide1_covers()
