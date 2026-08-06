"""
High-Resolution Image Generation Studio
Engine A: FLUX.1 via Pollinations REST API (100% Free, Unlimited, No API key required)
Engine B: Google Imagen 3 via Google AI Studio API (Optional, if GEMINI_API_KEY set)
Engine C: Hugging Face FLUX.1-schnell Serverless (Optional, if HF_TOKEN set)
"""

import os
import sys
import time
import json
import urllib.parse
import urllib.request
import random

# Default output directory
DEFAULT_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "output", "posts", "images")

# Aspect ratio map for LinkedIn
ASPECT_RATIOS = {
    "4:5": (1080, 1350),   # Recommended for LinkedIn mobile feed (vertical)
    "1:1": (1080, 1080),   # Standard square
    "16:9": (1200, 675),   # Banner / horizontal
    "banner": (1200, 628)  # Article header / cover
}

def generate_image_pollinations(prompt: str, width: int = 1080, height: int = 1350, model: str = "flux", enhance: bool = True, seed: int = None) -> bytes:
    """
    Generates high-res image using Pollinations FLUX.1 REST API.
    Zero API key required, 100% free, top-tier quality.
    """
    # Clean prompt string to prevent URL length limits
    clean_prompt = " ".join(prompt.split())
    if len(clean_prompt) > 800:
        clean_prompt = clean_prompt[:800]

    encoded_prompt = urllib.parse.quote(clean_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&model={model}&nologo=true&enhance={'true' if enhance else 'false'}&seed={seed}"
    
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    )
    
    with urllib.request.urlopen(req, timeout=60) as response:
        if response.status == 200:
            return response.read()
        else:
            raise RuntimeError(f"Pollinations returned HTTP status {response.status}")

def generate_image_google_imagen(prompt: str, api_key: str, aspect_ratio: str = "4:5") -> bytes:
    """
    Generates image using Google AI Studio Imagen 3 API.
    Requires GEMINI_API_KEY environment variable.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict?key={api_key}"
    payload = {
        "instances": [{"prompt": prompt}],
        "parameters": {
            "sampleCount": 1,
            "aspectRatio": aspect_ratio,
            "outputMimeType": "image/jpeg"
        }
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    
    with urllib.request.urlopen(req, timeout=60) as response:
        res_json = json.loads(response.read().decode("utf-8"))
        predictions = res_json.get("predictions", [])
        if predictions and "bytesBase64Encoded" in predictions[0]:
            import base64
            return base64.b64decode(predictions[0]["bytesBase64Encoded"])
        raise RuntimeError("No image bytes returned from Google Imagen API")

def create_high_res_image(
    prompt: str,
    aspect_ratio: str = "4:5",
    engine: str = "auto",
    output_dir: str = None,
    filename: str = None,
    style_preset: str = "photorealistic"
) -> dict:
    """
    Main entry point for generating high quality images.
    Returns dictionary with file path, dimensions, engine used, and metadata.
    """
    if output_dir is None:
        output_dir = DEFAULT_OUTPUT_DIR
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Format width and height based on aspect ratio
    width, height = ASPECT_RATIOS.get(aspect_ratio, (1080, 1350))
    
    # Enhance prompt based on style preset
    enhanced_prompt = prompt
    if style_preset == "photorealistic":
        if "photorealistic" not in prompt.lower():
            enhanced_prompt = f"Professional studio photography, 8k resolution, highly detailed, realistic lighting: {prompt}"
    elif style_preset == "minimalist":
        enhanced_prompt = f"Clean modern minimalist digital illustration, professional vector graphics, 8k: {prompt}"
    elif style_preset == "3d-render":
        enhanced_prompt = f"3D render, Octane render, smooth lighting, modern aesthetic: {prompt}"

    timestamp = int(time.time())
    if not filename:
        filename = f"post_img_{timestamp}.png"
    elif not filename.endswith((".png", ".jpg", ".jpeg")):
        filename += ".png"
        
    file_path = os.path.join(output_dir, filename)
    image_bytes = None
    engine_used = ""

    gemini_key = os.getenv("GEMINI_API_KEY")

    # Try Google Imagen 3 if specified or requested and key is available
    if (engine == "imagen-3" or (engine == "auto" and gemini_key)):
        if gemini_key:
            try:
                print(f"[Image Studio] Generating via Google Imagen 3...")
                image_bytes = generate_image_google_imagen(enhanced_prompt, gemini_key, aspect_ratio=aspect_ratio)
                engine_used = "Google Imagen 3"
            except Exception as e:
                print(f"[Image Studio] Google Imagen failed ({e}), falling back to FLUX.1 (Pollinations)...")

    # Fallback/Default: FLUX.1 via Pollinations
    if not image_bytes:
        try:
            print(f"[Image Studio] Generating via FLUX.1 (Pollinations Engine)...")
            image_bytes = generate_image_pollinations(enhanced_prompt, width=width, height=height, model="flux", enhance=True)
            engine_used = "FLUX.1 (Pollinations)"
        except Exception as e:
            raise RuntimeError(f"Failed to generate image via FLUX.1: {e}")

    with open(file_path, "wb") as f:
        f.write(image_bytes)

    return {
        "status": "success",
        "file_path": file_path,
        "file_uri": f"file:///{file_path.replace(os.sep, '/')}",
        "width": width,
        "height": height,
        "aspect_ratio": aspect_ratio,
        "engine_used": engine_used,
        "prompt": prompt,
        "enhanced_prompt": enhanced_prompt,
        "file_size_bytes": len(image_bytes)
    }

if __name__ == "__main__":
    print("Testing Image Studio with FLUX.1...")
    test_prompt = "A high tech modern workspace setup with a neon holographic code display, sleek laptop, dark aesthetic, professional photography"
    res = create_high_res_image(test_prompt, aspect_ratio="4:5", filename="test_flux_render.png")
    print(json.dumps(res, indent=2))
