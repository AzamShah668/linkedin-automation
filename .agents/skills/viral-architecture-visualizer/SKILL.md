---
name: viral-architecture-visualizer
description: Generates high-converting 4-slide LinkedIn carousel packs. Features Slide 1 (3D Command Center AI Visual), Slide 2 (Space Grotesk 5-Layer Core Architecture Specs), Slide 3 (Dual 3D Character Avatars - Stressed Manual Developer vs Happy Automated Developer), and Slide 4 (3D Robot Hologram Flowchart & Space Grotesk Operational Roadmap).
---

# Master 4-Slide LinkedIn Carousel Skill (`viral-architecture-visualizer`)

This skill defines the rules, regulations, and multi-slide design blueprint for generating high-converting 4-slide LinkedIn carousel packs.

## Multi-Slide Master Blueprint

### 1. Slide 1 (Cover / Hero Visual)
- **Style**: 3D Pixar-style Command Center AI visual based on `ai_robot_human_command_center_diagram.png`.
- **Layout**: Human Developer on Left + 3D AI Robot Agent on Right + Giant Glowing Cyan/Orange Neon Command Center Display Screen in Center.

### 2. Slide 2 (Core Architecture Technical Specs)
- **Typography**: Google Font `'Space Grotesk'` (bold, modern, futuristic).
- **Layout**: 5 stacked full-width neon container boxes (`Amber`, `Cyan`, `Emerald`, `Purple`, `Red`).
- **Content Packing**: Zero empty gaps inside containers; packed with exact code paths (`web/`, `.mcp.json`, `daily-discovery.ps1`, `image_studio.py`, `board_db.py`), protocol pills (`SLACK WEBHOOK API`, `STDIO JSON-RPC 2.0`, `PLAYWRIGHT CHROMIUM`, `FLUX.1 ENGINE`, `NOTION REST API`), and 2-line technical descriptions.

### 3. Slide 3 (Before vs After Comparison & Dual 3D Character Avatars)
- **Rule**: Never leave empty side margins in comparison cards. Always embed dedicated 3D character avatars at the top of each column:
  - **Left Column (Manual Job Hunt)**: Embedded 3D Avatar of a **Stressed, Frustrated Developer** (`stressed_manual_job_hunter.png`) overwhelmed by cluttered screens and coffee cups.
  - **Right Column (Job Hunt Autopilot)**: Embedded 3D Avatar of a **Happy, Confident Developer** (`happy_automated_job_hunter.png`) holding a glowing tablet with 10x interview stats.

### 4. Slide 4 (Operational Execution Roadmap & 3D Robot Flowchart)
- **Typography**: Google Font `'Space Grotesk'` (bold, modern, tech typography).
- **Visual Diagram**: Embedded 3D Pixar-style visual banner of a **Futuristic AI Robot Engineer** operating a 4-step glowing neon holographic execution flowchart (`roadmap_execution_robot_flow.png`).
- **Layout**: 4 interlocking horizontal stage panels (`01. Autonomous Daily Discovery`, `02. Notion DB & SQLite Sync`, `03. 1-Tap Mobile Phone Review`, `04. Stealth Outreach & FLUX.1 Visuals`).
- **Background Elements**: Floating lightbulb idea badges (`💡`), gear symbols (`⚙️`), monospace code badges (`</>`).

---

## Master Generator Script

Run the master script to render the complete 4-slide carousel pack:
```powershell
python tools/post_creator/generate_4slide_carousel.py
```
Outputs are saved to `output/posts/carousel_bundle/`.
