"""
MCP Server: LinkedIn Content & High-Res Image Studio (mcp-post-studio)
Protocol: Model Context Protocol (JSON-RPC over stdio)
Exposes tools for high-res image generation (FLUX.1 / Imagen 3), post copywriting, and daily automated publishing.
"""

import sys
import os
import json
import traceback

# Ensure current folder is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from image_studio import create_high_res_image
from post_generator import LinkedInPostGenerator, DynamicPostGenerator
from linkedin_publisher import LinkedInPublisher

SERVER_NAME = "mcp-post-studio"
SERVER_VERSION = "1.0.0"

# Tool Definitions
TOOLS = [
    {
        "name": "create_high_res_image",
        "description": "Generates a top-tier photorealistic or stylized image (FLUX.1 / Imagen 3 quality) optimized for LinkedIn.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Detailed image prompt describing the scene, lighting, and style."},
                "aspect_ratio": {"type": "string", "enum": ["4:5", "1:1", "16:9", "banner"], "default": "4:5", "description": "Image aspect ratio. 4:5 recommended for vertical mobile feed."},
                "style_preset": {"type": "string", "enum": ["photorealistic", "minimalist", "3d-render"], "default": "photorealistic", "description": "Visual style preset."},
                "engine": {"type": "string", "enum": ["auto", "flux", "imagen-3"], "default": "auto", "description": "AI rendering engine choice. 'auto' uses FLUX.1 (free/no-key) with Imagen 3 fallback if key set."}
            },
            "required": ["prompt"]
        }
    },
    {
        "name": "draft_linkedin_post",
        "description": "Generates structured viral LinkedIn post copy (Hook, Story, Bullets, Call To Action, Hashtags) and visual prompt.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "The main topic or subject of the LinkedIn post."},
                "tone": {"type": "string", "enum": ["thought-leadership", "storytelling", "bold", "informative"], "default": "thought-leadership"},
                "key_points": {"type": "array", "items": {"type": "string"}, "description": "Optional list of specific bullet points/insights to include."},
                "target_audience": {"type": "string", "default": "Tech Professionals & Engineers"}
            },
            "required": ["topic"]
        }
    },
    {
        "name": "run_daily_post_pipeline",
        "description": "Executes full end-to-end pipeline: drafts post copy, renders FLUX.1 high-res visual, and bundles post package.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Topic of the daily post."},
                "tone": {"type": "string", "default": "thought-leadership"},
                "aspect_ratio": {"type": "string", "default": "4:5"}
            },
            "required": ["topic"]
        }
    }
]

def handle_request(request: dict) -> dict:
    method = request.get("method")
    req_id = request.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": SERVER_NAME,
                    "version": SERVER_VERSION
                }
            }
        }

    elif method == "notifications/initialized":
        return None

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": TOOLS
            }
        }

    elif method == "tools/call":
        params = request.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        try:
            if tool_name == "create_high_res_image":
                prompt = arguments.get("prompt")
                aspect_ratio = arguments.get("aspect_ratio", "4:5")
                style_preset = arguments.get("style_preset", "photorealistic")
                engine = arguments.get("engine", "auto")

                result = create_high_res_image(
                    prompt=prompt,
                    aspect_ratio=aspect_ratio,
                    style_preset=style_preset,
                    engine=engine
                )

                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Successfully generated high-res image via {result['engine_used']}.\nFile Path: {result['file_path']}\nDimensions: {result['width']}x{result['height']} ({result['aspect_ratio']})"
                            }
                        ]
                    }
                }

            elif tool_name == "draft_linkedin_post":
                topic = arguments.get("topic")
                tone = arguments.get("tone", "thought-leadership")

                bundle = DynamicPostGenerator.generate_full_linkedin_post_bundle(
                    context_or_topic=topic,
                    tone=tone
                )

                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Successfully created LinkedIn Post & Custom Visual Package!\n\n"
                                        f"• Package Saved: {bundle['package_file']}\n"
                                        f"• Image Rendered: {bundle['image_file']}\n\n"
                                        f"--- GENERATED LINKEDIN COPY ---\n{bundle['post_body']}"
                            }
                        ]
                    }
                }

            elif tool_name == "run_daily_post_pipeline":
                topic = arguments.get("topic", "Autonomous LinkedIn Job Hunt Autopilot")
                tone = arguments.get("tone", "thought-leadership")

                # Single-call dynamic MCP pipeline: generates copy + 4-slide carousel + packages for mcp-server-linkedin
                bundle = DynamicPostGenerator.generate_full_linkedin_post_bundle(
                    context_or_topic=topic,
                    tone=tone
                )

                # Delegate to mcp-server-linkedin integration protocol
                pub_result = LinkedInPublisher.publish_package(bundle)

                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"🎉 Daily Post Pipeline Executed via LinkedIn MCP!\n\n"
                                        f"• Topic/Context: {topic}\n"
                                        f"• Slide 1 Cover: {bundle['slide_1']}\n"
                                        f"• Slide 2 Specs: {bundle['slide_2']}\n"
                                        f"• Slide 3 Avatars: {bundle['slide_3']}\n"
                                        f"• Slide 4 Roadmap: {bundle['slide_4']}\n"
                                        f"• Package Saved: {bundle['package_file']}\n"
                                        f"• Target MCP Server: mcp-server-linkedin@latest\n\n"
                                        f"--- GENERATED LINKEDIN COPY ---\n{bundle['post_body']}"
                            }
                        ]
                    }
                }

            else:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": f"Unknown tool: {tool_name}"
                    }
                }

        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32000,
                    "message": f"Tool execution failed: {str(e)}\n{traceback.format_exc()}"
                }
            }

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {
            "code": -32601,
            "message": f"Unhandled method: {method}"
        }
    }

def main():
    """stdio JSON-RPC loop"""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = handle_request(request)
            if response:
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
        except Exception as e:
            err_res = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {str(e)}"}
            }
            sys.stdout.write(json.dumps(err_res) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main()
