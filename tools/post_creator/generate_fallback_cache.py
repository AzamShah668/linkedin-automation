#!/usr/bin/env python3
"""Pre-generate a cache of 10 fallback hero images for when FLUX.1 is unavailable.

    py -3 tools/post_creator/generate_fallback_cache.py

These are generic tech-aesthetic images (no text, no specific project branding)
that can be used as a last-resort visual for any post type.
"""
from __future__ import annotations

import os
import sys
import json
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from image_studio import create_high_res_image

CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "output" / "posts" / "fallback_cache"

FALLBACK_PROMPTS = [
    "A sleek dark workspace with a single ultrawide monitor displaying glowing cyan code. Volumetric light rays, dark background #030712, minimalist tech aesthetic. 8k, no text.",
    "A futuristic 3D neural network visualization floating in space. Glowing blue and orange nodes connected by pulsing data streams. Dark void background. 8k, no text.",
    "A dramatic overhead view of a modern developer desk with multiple screens, mechanical keyboard, and ambient LED lighting in purple and blue tones. Cinematic photography, 8k.",
    "A 3D render of a crystalline data structure rotating in dark space. Cyan wireframe geometry with particle effects. Clean, futuristic, premium aesthetic. 8k, no text.",
    "A contemplative scene of a laptop on a minimalist desk near a window at golden hour. Screen shows a terminal with green output. Warm and cool tones blended. 8k.",
    "A holographic architecture diagram floating above a dark surface. Glowing layers in cyan, amber, green, purple, and red. Sci-fi command center aesthetic. 8k, no text.",
    "An abstract 3D render of interconnected hexagonal modules forming a platform. Electric blue glow, dark background, particle effects. Premium tech visualization. 8k.",
    "A split composition: left side shows chaotic tangled wires, right side shows elegant organized cable management. Dramatic lighting, metaphor for code refactoring. 8k.",
    "A close-up of a robotic hand delicately placing the final piece of a glowing circuit board puzzle. Soft volumetric light, dark background, premium tech aesthetics. 8k.",
    "An aerial view of a vast server farm rendered in 3D with glowing rows of data racks stretching into the distance. Cool blue lighting, cinematic fog. 8k, no text.",
]


def main() -> None:
    os.makedirs(str(CACHE_DIR), exist_ok=True)

    existing = list(CACHE_DIR.glob("fallback_*.png"))
    if len(existing) >= 10:
        print(f"[Cache] Already have {len(existing)} fallback images. Use --force to regenerate.")
        if "--force" not in sys.argv:
            return

    print(f"[Cache] Generating {len(FALLBACK_PROMPTS)} fallback hero images...")
    print(f"[Cache] Output: {CACHE_DIR}\n")

    for i, prompt in enumerate(FALLBACK_PROMPTS):
        filename = f"fallback_{i+1:02d}.png"
        filepath = CACHE_DIR / filename

        if filepath.exists() and "--force" not in sys.argv:
            print(f"  [{i+1}/10] Skipping {filename} (exists)")
            continue

        print(f"  [{i+1}/10] Generating {filename}...")
        try:
            result = create_high_res_image(
                prompt=prompt,
                aspect_ratio="4:5",
                output_dir=str(CACHE_DIR),
                filename=filename,
                style_preset="3d-render",
            )
            size_kb = result["file_size_bytes"] / 1024
            print(f"         Saved ({size_kb:.0f} KB) via {result['engine_used']}")
        except Exception as e:
            print(f"         [FAIL] {e}")

    final_count = len(list(CACHE_DIR.glob("fallback_*.png")))
    print(f"\n[Cache] Done. {final_count} fallback images available in {CACHE_DIR}")


if __name__ == "__main__":
    main()
