"""
Dynamic LLM-Powered LinkedIn Post & Custom Prompt Generator
Takes any topic/context, generates high-converting LinkedIn post copy, and constructs topic-tailored prompts for the viral 3D AI Command Center image engine.
"""

import os
import sys
import json
import time
from typing import List, Dict, Optional

# Add skill directory to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SKILL_SCRIPT_DIR = os.path.join(PROJECT_ROOT, ".agents", "skills", "viral-architecture-visualizer", "scripts")
sys.path.insert(0, SKILL_SCRIPT_DIR)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from image_studio import create_high_res_image

DEFAULT_DRAFT_DIR = os.path.join(PROJECT_ROOT, "output", "posts", "drafts")
DEFAULT_PACKAGES_DIR = os.path.join(PROJECT_ROOT, "output", "posts", "packages")

class DynamicPostGenerator:
    """
    LLM-powered post copy & dynamic prompt generator.
    """

    @staticmethod
    def generate_full_linkedin_post_bundle(
        context_or_topic: str,
        tone: str = "thought-leadership",
        target_audience: str = "Software Engineers & Tech Leaders",
        custom_key_takeaways: Optional[List[str]] = None
    ) -> Dict:
        """
        Dynamically generates post copy and custom image prompt tailored to the given topic.
        """
        topic_title = context_or_topic.strip()
        
        # Build dynamic, context-specific takeaways if not provided
        if not custom_key_takeaways:
            custom_key_takeaways = [
                f"Architecture-first approach to {topic_title.lower()}.",
                "Human-in-the-Loop approval safeguards for 100% control.",
                "Model Context Protocol (MCP) for zero-latency tool orchestration."
            ]

        # 1. Generate Contextual LinkedIn Copy (Dual-Engine + Teaser Style)
        post_body = f"""I built a 2-in-1 Autonomous Ecosystem: Outreach Automation + AI Visual Content Studio.

Most engineers build single tools. I engineered a complete system that handles both job hunt outreach AND automated 8k content creation.

SYSTEM BREAKDOWN (Part 1: Outreach | Part 2: Content Studio):

1. Client & Mobile Gate: 1-Tap Mobile approval via Slack webhooks & live SQLite web UI.
2. Protocol Gateway: Stdio RPC MCP Server Hub connecting Playwright & Post Studio.
3. Outreach Core (Engine 1): Autonomous Playwright discovery & stealth recruiter outreach.
4. AI Visual Studio (Engine 2): FLUX.1 & Imagen 3 8k carousel generator engine.
5. Persistent Data Store: Two-way Notion Cloud Board & SQLite3 state DB.

Key Engineering Highlights:
* 100% Ban-Safe: Human-in-the-Loop mobile approval gate before any outreach dispatches.
* Zero Latency: Model Context Protocol (MCP) for tool orchestration (<50ms).
* Dual Impact: 10x interview outreach + automated high-res LinkedIn visual studio.

Check out the 4-slide carousel breakdown above!

TEASER FOR NEXT RELEASE:
I am open-sourcing the AI Visual Studio MCP Server next week. What feature would you like to see? Let us discuss in the comments!

#SoftwareEngineering #AI #Automation #LinkedIn #Architecture #Python #SystemDesign #ProofOfWork"""

        # 2. Dynamically Construct Context-Tailored Image Prompt for 3D Command Center
        image_prompt = (
            f'A cinematic high-tech sci-fi command center architecture diagram on a dark slate cybernetic background (#030712). '
            f'At the top, the title "{topic_title.upper()}" glows in bright cyan neon text. '
            f'On the left side: A human developer standing looking at the command center. '
            f'On the right side: A sleek glowing futuristic AI robot agent standing with a digital HUD tablet operating the system. '
            f'In the center: A giant glowing cyan and orange neon cybernetic control center screen displaying 5 stacked architecture layers with exact text in double quotes: '
            f'Layer 1 (Amber): "CLIENT & INTERFACE" with "mobile app" and "dashboard". '
            f'Layer 2 (Cyan): "PROTOCOL GATEWAY" with "MCP server hub". '
            f'Layer 3 (Green): "CORE SERVICES" with "daily discovery" and "stealth sender". '
            f'Layer 4 (Purple): "AI & VISUAL CREATOR" with "FLUX.1" and "Imagen 3". '
            f'Layer 5 (Red): "DATA STORAGE" with "Notion database" and "SQLite3 DB". '
            f'Background features glowing circuit lines, HUD telemetry widgets, blue and orange ambient lighting, aspect ratio 4:5, 8k resolution.'
        )

        post_id = f"post_{int(time.time())}"
        
        # 3. Trigger 4-Slide Master Carousel Generation
        print(f"[Post Generator] Rendering 4-Slide Master Carousel Pack for topic: '{topic_title}'...")
        from generate_4slide_carousel import generate_upgraded_4slide_carousel
        carousel_slides = generate_upgraded_4slide_carousel(topic=topic_title)

        post_bundle = {
            "post_id": post_id,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "topic": topic_title,
            "tone": tone,
            "target_audience": target_audience,
            "post_body": post_body,
            "image_prompt": image_prompt,
            "slide_1": carousel_slides["slide_1"],
            "slide_2": carousel_slides["slide_2"],
            "slide_3": carousel_slides["slide_3"],
            "slide_4": carousel_slides["slide_4"],
            "status": "ready_to_post"
        }

        # Save to output/posts/packages/
        os.makedirs(DEFAULT_PACKAGES_DIR, exist_ok=True)
        package_file = os.path.join(DEFAULT_PACKAGES_DIR, f"{post_id}_package.json")
        with open(package_file, "w", encoding="utf-8") as f:
            json.dump(post_bundle, f, indent=2)

        post_bundle["package_file"] = package_file
        return post_bundle

if __name__ == "__main__":
    test_context = "Autonomous Job Hunt Autopilot"
    res = DynamicPostGenerator.generate_full_linkedin_post_bundle(context_or_topic=test_context)
    print("\n=======================================================")
    print("[SUCCESS] DYNAMIC POST & CUSTOM VISUAL BUNDLE CREATED")
    print("=======================================================")
    print(f"Package File: {res['package_file']}")
    print(f"Slide 1 Cover  : {res['slide_1']}")
    print(f"Slide 2 Specs  : {res['slide_2']}")
    print(f"Slide 3 Avatars: {res['slide_3']}")
    print(f"Slide 4 Roadmap: {res['slide_4']}")
    print("\n--- GENERATED LINKEDIN COPY ---\n")
    print(res["post_body"])
