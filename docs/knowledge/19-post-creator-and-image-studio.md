# 19 — Post Creator & High-Res Image Studio MCP Subsystem

## Overview
A 100% isolated daily LinkedIn content and high-resolution image rendering subsystem (`tools/post_creator/`).
It generates structured LinkedIn post copy paired with photorealistic visuals comparable to Imagen 3 / FLUX.1.

## Key Components
- **`tools/post_creator/image_studio.py`**: Image generation engine using **FLUX.1 [schnell/dev]** via Pollinations REST API (100% free, no API key required) and Google Imagen 3 API fallback (`GEMINI_API_KEY`).
- **`tools/post_creator/post_generator.py`**: Formats copy into high-engaging LinkedIn post structures and drafts matching visual prompts.
- **`tools/post_creator/linkedin_publisher.py`**: Packages post copy and high-res image into ready JSON packages in `output/posts/packages/`.
- **`tools/post_creator/mcp_server.py`**: Standalone MCP server registered as `mcp-post-studio` in `.mcp.json`.
- **`tools/post_creator/daily_post_scheduler.ps1`**: PowerShell runner for one-command or scheduled daily post pipeline execution.

## Master Skill: `viral-architecture-visualizer`
- **Location**: `.agents/skills/viral-architecture-visualizer/`
- **Slide 1**: Hero 3D Command Center AI Visual based on [`ai_robot_human_command_center_diagram.png`](file:///d:/linkdin%20automation/output/posts/images/ai_robot_human_command_center_diagram.png).
- **Slide 2**: Space Grotesk 5-Layer Core Architecture Specs Card with exact code paths & protocol pills.
- **Slide 3**: Dual 3D Character Avatars (`stressed_manual_job_hunter.png` on Left vs `happy_automated_job_hunter.png` on Right).
- **Slide 4**: Space Grotesk Operational Execution Roadmap + Embedded 3D Robot Hologram Flowchart (`roadmap_execution_robot_flow.png`).
- **Master Script**: `tools/post_creator/generate_4slide_carousel.py`

## MCP Ecosystem Integration
- **`mcp-post-studio`**: Generates post copy & 4-slide visual carousel pack (`tools/post_creator/mcp_server.py`).
- **`mcp-server-linkedin`**: Receives ready post packages from `mcp-post-studio` and dispatches live posts onto LinkedIn via the stdio MCP protocol (`mcp-server-linkedin@latest`). Zero standalone Playwright script overhead required!
