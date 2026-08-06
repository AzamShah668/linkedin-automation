"""
Ultimate Cybernetic HUD Architecture Generator (FLUX.1 & Gemini Engine)
Combines 3D engineer character + lightbulb idea + futuristic cybernetic HUD blueprint dashboard layout.
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from image_studio import create_high_res_image

CYBERNETIC_MASTER_PROMPT = (
    'A masterclass 3D tech infographic and high-tech cybernetic blueprint dashboard UI on a dark cybernetic background (#050B18). '
    'At the top, the title "HOW IT WORKS: THE CORE ARCHITECTURE" glows in bright cyan neon text. '
    'On the right side: A 3D tech engineer character standing, taking digital notes on a tablet, with a bright glowing yellow lightbulb idea icon, '
    'floating thinking cloud, and glowing code symbols (</>) around him. '
    'In the center: 5 stacked futuristic cybernetic HUD blueprint glass container panels connected by glowing blue and gold circuit data pipelines with downward arrows. '
    'Each panel features sleek sci-fi telemetry frames, HUD glowing widgets, and exact text in double quotes: '
    'Panel 1 (Warm Amber Border): "CLIENT & INTERFACE" with "mobile app" and "dashboard" buttons. '
    'Panel 2 (Cyan Border): "PROTOCOL GATEWAY" with "MCP server hub" button. '
    'Panel 3 (Emerald Green Border): "CORE SERVICES" with "daily discovery" and "stealth sender" buttons. '
    'Panel 4 (Purple Border): "AI & VISUAL CREATOR" with "FLUX.1" and "Imagen 3" buttons. '
    'Panel 5 (Crimson Red Border): "DATA STORAGE" with "Notion database" and "SQLite3 DB" buttons. '
    'Background is enriched with glowing blue HUD telemetry panels, golden circuit lines, glowing gears, sci-fi blueprint grids, 8k resolution, aspect ratio 4:5.'
)

def run_generation():
    print("[Cybernetic Studio] Rendering Ultimate Cybernetic HUD Architecture Diagram...")
    result = create_high_res_image(
        prompt=CYBERNETIC_MASTER_PROMPT,
        aspect_ratio="4:5",
        filename="ultimate_cybernetic_architecture_diagram.png",
        style_preset="none"
    )
    print("\n[SUCCESS] Image generated successfully!")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    run_generation()
