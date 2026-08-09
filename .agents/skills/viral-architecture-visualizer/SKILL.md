---
name: viral-architecture-visualizer
description: Generates high-converting 4-slide LinkedIn carousel packs. Features Slide 1 (3D Command Center AI Visual), Slide 2 (Space Grotesk 5-Layer Core Architecture Specs), Slide 3 (Dual 3D Character Avatars - Stressed Manual Developer vs Happy Automated Developer), and Slide 4 (3D Robot Hologram Flowchart & Space Grotesk Operational Roadmap).
---

# Master 4-Slide LinkedIn Carousel Skill (`viral-architecture-visualizer`)

This skill defines the complete rules, design system, rendering pipeline, content rules,
and hard-won lessons for generating 4-slide LinkedIn carousel packs.

---

## ⚠️ Critical Rules (Read First — Every Time)

### Rule 1: NEVER trust AI to render readable text
AI image generators (FLUX.1, Imagen 3, DALL-E) **always** produce gibberish when asked to
render small text labels. This is a known, unfixable limitation.

**The solution**: The **Hybrid Vector/3D Method**:
1. Generate a 3D background scene via FLUX.1 with **no text** in the prompt (or text in quotes as a hint, but expect it to fail)
2. Overlay crisp vector text via **Edge headless HTML-to-PNG** rendering on top

Slide 1 uses this hybrid method. Slides 2, 3, 4 are 100% HTML-rendered (no AI image generation needed for text).

### Rule 2: Post copy = showcase what was BUILT, not results
- ✅ Describe the engines, architecture, stack, and what each component does
- ❌ Never include personal metrics (e.g., "62 jobs found", "5 applied", "0 bounces")
- ❌ Never include debugging war stories (e.g., "browser profile lock cost me an hour")
- **Rationale**: User directive (2026-08-09). The post is a portfolio showcase, not a progress report.

### Rule 3: Every post gets a UNIQUE Slide 1
When generating multiple posts, each MUST have a visually distinct Slide 1. Never reuse
the same hero image across different posts — it was flagged as a critical failure.

### Rule 4: Windows encoding
Always run Python scripts with `$env:PYTHONIOENCODING="utf-8"` on Windows. The default
`cp1252` codec cannot encode emoji or Unicode arrows (→, ✅, etc.) and the script will crash.

### Rule 5: I cannot post to LinkedIn directly
The `mcp-server-linkedin` is registered in `.mcp.json` for Claude Desktop/Code — not for
Antigravity. The browser subagent is also blocked from LinkedIn by safety policy. Posting
must be done by Claude or manually by the user.

---

## Multi-Slide Design System

### Slide 1: Cover / Hero Visual (Hybrid AI + Vector)

**Rendering method**: AI-generated 3D base artwork + HTML vector overlay via Edge headless.

**3D Base Prompt** (no text — scene only):
```
Pixar-style 3D rendered futuristic command center scene, dark navy blue background.
LEFT: male software engineer in futuristic suit, arms crossed.
CENTER: massive glowing holographic screen with 5 neon-bordered panels (amber, cyan, green, purple, red).
RIGHT: tall humanoid AI robot with glowing cyan eyes holding a transparent tablet.
Floating HUD elements, circuit board traces on floor glowing cyan, volumetric light rays.
Ultra-detailed Octane render. No text anywhere.
```

**Vector overlay**: Edge headless renders an HTML page (1080×1350) with:
- Header bar: topic title in Space Grotesk 900
- The 3D artwork fills the center as an `<img>` with `object-fit: cover`
- Four corner badges: `🤖 AI AGENT OPERATED`, `🛡️ 100% BAN-SAFE`, `🎨 FLUX.1 VISUAL ENGINE`, `⚡ 5 SCHEDULED TASKS`
- Stats banner at bottom: tech stack pills (FLUX.1 / MCP / Playwright / SQLite)
- Footer CTA bar: gradient banner with one-liner

**Existing 3D artwork** (`output/posts/images/ai_robot_human_command_center_diagram.png`, 819KB)
can be reused if it exists and is >500KB. Only regenerate if missing.

### Slide 2: Core Architecture Technical Specs

**Rendering method**: 100% HTML via Edge headless (no AI image generation).

| Element | Spec |
|---------|------|
| Typography | Google Font `Space Grotesk` (weights: 600-900) + `Fira Code` (monospace) |
| Background | `#030712` with cyan/gold radial gradients + 30px grid lines |
| Layout | 5 stacked full-width neon container boxes |
| Colors | Amber `#ff9100`, Cyan `#00e5ff`, Green `#00e676`, Purple `#e040fb`, Red `#ff1744` |
| Each box | Layer name (colored) + file code badge (yellow monospace) + 2-line description + protocol pills row |
| Footer | 4-column stats bar showing tech features (not metrics!) |
| Floating symbols | `💡` (top-right), `⚙️` (mid-left, bottom-left), `</>` (bottom-right, monospace cyan) |

**Content packing rule**: Zero empty gaps inside containers. Every box has: heading, file paths, description, AND pill badges.

### Slide 3: Before vs After Comparison (Dual 3D Avatars)

**Rendering method**: HTML template + embedded 3D avatar images.

| Element | Spec |
|---------|------|
| Typography | Google Font `Plus Jakarta Sans` (700-900) |
| Layout | 2-column grid. Left = red border (old way). Right = cyan border (autopilot). |
| Avatars | 200px height containers at top of each column |
| Left avatar | `stressed_manual_job_hunter.png` — frustrated developer drowning in browser tabs |
| Right avatar | `happy_automated_job_hunter.png` — confident developer with glowing tablet |
| Bullet items | 6 per column. Left uses ❌ icons. Right uses colored emoji icons (⚡🧠📱🎨✉️🛡️) |
| Status boxes | Left: red "EXHAUSTING & UNPREDICTABLE". Right: cyan "10X OUTPUT & INTERVIEWS" |
| Bottom banner | Purple gradient: motivational one-liner CTA |

**Avatar generation prompts** (only if missing):
- Stressed: `3D Pixar-style frustrated male developer, 40 browser tabs, coffee cups, blue screen errors, dark office, moody lighting, Octane render`
- Happy: `3D Pixar-style confident happy male developer, glowing tablet, green checkmarks, clean desk, warm lighting, robot assistant in background, Octane render`

### Slide 4: Operational Roadmap (Task Cards + 3D Robot)

**Rendering method**: HTML template + embedded 3D robot flowchart banner.

| Element | Spec |
|---------|------|
| Typography | Google Font `Outfit` (700-900) + `Fira Code` |
| Background | `#030712` with purple/cyan radial gradients + 28px grid |
| Frame border | `#e040fb` (magenta) with glow |
| Robot banner | 210px height, `roadmap_execution_robot_flow.png`, cyan border |
| Task cards | 5 stacked cards, each with: numbered badge, title, schedule tag, description |
| Card colors | Cyan, Magenta, Green, Yellow, Orange (in order) |
| Floating symbols | `❓` (purple, top-right + bottom-left), `💡` (yellow, bottom-right) |
| Bottom CTA | Cyan banner: "5 TASKS • 0 CLOUD BILLS • RUNS ON YOUR LAPTOP WHILE YOU SLEEP" |

**Task card content rule**: Describe *what the task does*, not its results. No "RESULT: ..." lines.

**Robot flowchart prompt** (only if missing):
```
3D Pixar-style futuristic AI robot engineer standing in front of glowing neon
holographic 4-step execution flowchart, data ingest to analysis to execution
to result checkmark, dark command center background, cyan and purple neon lighting,
Octane render, no text
```

---

## Canonical Generator Script

The **single canonical script** for generating a complete post is:

```powershell
$env:PYTHONIOENCODING="utf-8"; py -3 tools/post_creator/generate_unified_post.py
```

**Output**: `output/posts/unified_post/`
- `slide_1_hero.png` — Hybrid 3D + vector overlay
- `slide_2_architecture.png` — 5-layer specs card
- `slide_3_comparison.png` — Before vs After
- `slide_4_roadmap.png` — 5 scheduled tasks
- `unified_post_package.json` — Complete bundle (copy + slide paths + metadata)

The older scripts (`generate_4slide_carousel.py`, `generate_post1_job_hunt_carousel.py`,
`render_hybrid_slide1_covers.py`, etc.) are **deprecated**. Use `generate_unified_post.py` only.

---

## Post Copy Framework

The post body follows a **3-section structure** (no results, no war stories):

```
[One-line hook: what you automated]

Here is what I built:

🔍 ENGINE 1: [NAME]
→ [step-by-step what it does, 8-10 bullets]

🎨 ENGINE 2: [NAME]
→ [step-by-step what it does, 5-6 bullets]
→ "This very post and its carousel were generated by this system" (meta-proof)

THE STACK:
[One-line comma-separated tech list]

[One-line closing: "Everything runs on my laptop. No cloud. No bill."]

[CTA question inviting comments]

[Hashtags]
```

---

## 3D Asset Inventory (Reusable)

| Asset | File | Size | Reusable? |
|-------|------|------|-----------|
| Command Center scene | `output/posts/images/ai_robot_human_command_center_diagram.png` | 819KB | ✅ Yes — high quality |
| Stressed developer avatar | `output/posts/images/stressed_manual_job_hunter.png` | 804KB | ✅ Yes |
| Happy developer avatar | `output/posts/images/happy_automated_job_hunter.png` | 782KB | ✅ Yes |
| Robot flowchart banner | `output/posts/images/roadmap_execution_robot_flow.png` | 861KB | ✅ Yes |

Only regenerate these if they're missing or <100KB (corrupted).

---

## Dispatch Options

| Method | Who | How |
|--------|-----|-----|
| Claude + mcp-server-linkedin | User's Claude Desktop | `Post this package: output/posts/unified_post/unified_post_package.json` |
| Manual | User | Upload 4 slides + paste copy text in LinkedIn post editor |
| Playwright poster (fallback) | Script | `py -3 tools/post_creator/playwright_linkedin_poster.py` (needs logged-in browser profile) |

**Antigravity cannot post directly** — LinkedIn is blocked by browser safety policy and `mcp-server-linkedin` is not available as an Antigravity MCP tool.

---

## Common Failure Modes & Fixes

| Failure | Cause | Fix |
|---------|-------|-----|
| `UnicodeEncodeError: charmap` | Windows cp1252 can't encode → or ✅ | Set `$env:PYTHONIOENCODING="utf-8"` before running |
| Slide 1 has gibberish text | FLUX.1 tried to render text labels | Use hybrid method: AI scene (no text) + HTML vector overlay |
| Two posts share identical Slide 1 | Script copied instead of generating unique art | Each post needs a unique 3D base or unique overlay content |
| `shutil` import missing | Forgotten import in pipeline scripts | Always import `shutil` at top of any file-copy script |
| Edge headless doesn't render fonts | Google Fonts need network fetch | Ensure `@import url(...)` is in the HTML `<style>` block and machine has internet |
