"""
Automated Viral Architecture Infographic Generator
Skill: viral-architecture-visualizer
Target Visual Style: ai_robot_human_command_center_diagram.png
Renders 3D Human Developer (Left) + 3D AI Robot Agent (Right) + Giant Glowing Cyan/Orange Command Screen (Center).
"""

import os
import sys
import json
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
POST_CREATOR_DIR = os.path.join(PROJECT_ROOT, "tools", "post_creator")
sys.path.insert(0, POST_CREATOR_DIR)

from image_studio import create_high_res_image

COMMAND_CENTER_MASTER_PROMPT = (
    'A cinematic high-tech sci-fi command center architecture diagram on a dark slate cybernetic background (#030712). '
    'At the top, the title "HOW IT WORKS: THE CORE ARCHITECTURE" glows in bright cyan neon text. '
    'On the left side: A human developer standing looking at the command center. '
    'On the right side: A sleek glowing futuristic AI robot agent standing with a digital HUD tablet operating the system. '
    'In the center: A giant glowing cyan and orange neon cybernetic control center screen displaying 5 stacked architecture layers with exact text in double quotes: '
    'Layer 1 (Amber): "CLIENT & INTERFACE" with "mobile app" and "dashboard". '
    'Layer 2 (Cyan): "PROTOCOL GATEWAY" with "MCP server hub". '
    'Layer 3 (Green): "CORE SERVICES" with "daily discovery" and "stealth sender". '
    'Layer 4 (Purple): "AI & VISUAL CREATOR" with "FLUX.1" and "Imagen 3". '
    'Layer 5 (Red): "DATA STORAGE" with "Notion database" and "SQLite3 DB". '
    'Background features glowing circuit lines, HUD telemetry widgets, blue and orange ambient lighting, aspect ratio 4:5, 8k resolution.'
)

def generate_command_center_diagram(
    output_filename: str = None,
    custom_title: str = "HOW IT WORKS: THE CORE ARCHITECTURE"
) -> dict:
    """
    Generates a high-converting 3D Command Center architecture diagram matching ai_robot_human_command_center_diagram.png.
    """
    if not output_filename:
        output_filename = f"ai_command_center_{int(time.time())}.png"

    prompt = COMMAND_CENTER_MASTER_PROMPT
    if custom_title != "HOW IT WORKS: THE CORE ARCHITECTURE":
        prompt = prompt.replace("HOW IT WORKS: THE CORE ARCHITECTURE", custom_title)

    print(f"[Skill Generator] Rendering AI Command Center Architecture Visual...")
    result = create_high_res_image(
        prompt=prompt,
        aspect_ratio="4:5",
        filename=output_filename,
        style_preset="none"
    )

    result["target_style"] = "ai_robot_human_command_center_diagram.png"
    return result

if __name__ == "__main__":
    res = generate_command_center_diagram()
    print(json.dumps(res, indent=2))
