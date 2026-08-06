# LinkedIn Content & High-Res Image Studio (`tools/post_creator/`)

An isolated, top-tier LinkedIn post generation and high-resolution image rendering system built with MCP (Model Context Protocol).

## Features

- 📸 **High-Resolution Image Generation**:
  - Primary Engine: **FLUX.1 [schnell/dev]** via Pollinations REST API (100% Free, Unlimited, No API key needed).
  - Secondary Engine: **Google Imagen 3** via Google AI Studio (`GEMINI_API_KEY`).
  - Supports LinkedIn aspect ratios: `4:5` (mobile vertical), `1:1` (square), `16:9` (banner).
- ✍️ **Viral LinkedIn Copywriting**:
  - Generates structured post copy (Hook, Story, Bullet points, Call To Action, Hashtags).
  - Automatically matches post tone with custom visual prompts.
- 🔌 **Standalone MCP Server (`mcp-post-studio`)**:
  - Exposes tools directly to AI Agents (Antigravity, Claude, Cursor):
    - `create_high_res_image`
    - `draft_linkedin_post`
    - `run_daily_post_pipeline`
- 📅 **Automated Daily Pipeline**:
  - Single PowerShell execution (`daily_post_scheduler.ps1`) for scheduled daily posts.

## Direct CLI Usage

### Generate high-res image directly:
```bash
python tools/post_creator/image_studio.py
```

### Run daily post pipeline:
```powershell
powershell -ExecutionPolicy Bypass -File tools/post_creator/daily_post_scheduler.ps1 -Topic "Autonomous AI Agents in Production"
```

## Output Locations

- **Rendered Images**: `output/posts/images/`
- **Post Drafts**: `output/posts/drafts/`
- **Complete Bundles**: `output/posts/packages/`
