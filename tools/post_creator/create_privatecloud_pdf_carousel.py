import os
import sys
from PIL import Image, ImageOps

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CAROUSEL_DIR = os.path.join(PROJECT_ROOT, "output", "posts", "carousel_bundle_privatecloud")

IMAGE_FILES = [
    ("screen_1_dashboard.png", "AZNA-CLOUD Main Dashboard UI"),
    ("screen_2_deploy.png", "Deploy Compute Instance UI"),
    ("screen_3_admin_command_center.png", "Admin Command Center UI"),
    ("screen_4_chatops.png", "AI Cognitive Engine ChatOps Console"),
    ("slide_2_core_architecture_details.png", "5-Layer Core Architecture Specs"),
    ("slide_3_before_vs_after_comparison.png", "Before vs After Compute Platform")
]

TARGET_WIDTH = 1080
TARGET_HEIGHT = 1350
BG_COLOR = (3, 7, 18) # #030712

def process_and_create_pdf():
    processed_images = []
    
    for f, label in IMAGE_FILES:
        path = os.path.join(CAROUSEL_DIR, f)
        if not os.path.exists(path):
            print(f"Warning: {f} missing")
            continue

        img = Image.open(path).convert("RGB")
        w, h = img.size

        # Create canvas 1080x1350
        canvas = Image.new("RGB", (TARGET_WIDTH, TARGET_HEIGHT), BG_COLOR)

        if w == TARGET_WIDTH and h == TARGET_HEIGHT:
            canvas.paste(img, (0, 0))
        else:
            # Resize landscape image (1920x869) to fit width 1080, centered vertically
            scale = TARGET_WIDTH / float(w)
            new_h = int(h * scale)
            resized = img.resize((TARGET_WIDTH, new_h), Image.Resampling.LANCZOS)
            
            # Center vertically
            y_offset = (TARGET_HEIGHT - new_h) // 2
            canvas.paste(resized, (0, y_offset))

        # Save individual uniform page png
        out_page_png = os.path.join(CAROUSEL_DIR, f"uniform_{f}")
        canvas.save(out_page_png)
        processed_images.append(canvas)
        print(f"[OK] Processed page: {label} -> uniform_{f}")

    if not processed_images:
        print("No images processed.")
        return None

    # Save as PDF using PIL
    pdf_path = os.path.join(CAROUSEL_DIR, "AZNA_CLOUD_PrivateCloud_Carousel.pdf")
    processed_images[0].save(
        pdf_path,
        "PDF",
        resolution=100.0,
        save_all=True,
        append_images=processed_images[1:]
    )
    print(f"\n[SUCCESS] Single PDF Document Carousel Generated: {pdf_path}")
    return pdf_path

if __name__ == "__main__":
    process_and_create_pdf()
