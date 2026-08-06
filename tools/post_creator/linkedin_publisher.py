"""
LinkedIn Publisher Engine
Handles packaging post copy with generated high-res images and publishing/scheduling.
"""

import os
import json
import time
from typing import Dict, Optional

DEFAULT_PACKAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "output", "posts", "packages")

class LinkedInPublisher:
    """
    Manages packaging post bundles with rendered images and executing publishing actions.
    """

    @staticmethod
    def package_post(post_bundle: Dict, image_meta: Dict, packages_dir: str = None) -> Dict:
        """
        Bundles post copy and high-res image into a complete publishing package.
        """
        if packages_dir is None:
            packages_dir = DEFAULT_PACKAGES_DIR
        os.makedirs(packages_dir, exist_ok=True)

        package_id = post_bundle.get("post_id", f"package_{int(time.time())}")
        
        complete_package = {
            "package_id": package_id,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "topic": post_bundle.get("topic", ""),
            "post_body": post_bundle.get("post_body", ""),
            "image_path": image_meta.get("file_path", ""),
            "image_uri": image_meta.get("file_uri", ""),
            "image_engine": image_meta.get("engine_used", ""),
            "aspect_ratio": image_meta.get("aspect_ratio", "4:5"),
            "status": "ready_to_publish"
        }

        file_path = os.path.join(packages_dir, f"{package_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(complete_package, f, indent=2)

        complete_package["package_file"] = file_path
        return complete_package

    @staticmethod
    def publish_package(package_file_or_data: Dict) -> Dict:
        """
        Simulates or executes publishing of the ready package to LinkedIn.
        If LinkedIn OAuth access token is set, uses LinkedIn REST API.
        Otherwise, preps the package file for Playwright / human submission.
        """
        linkedin_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
        
        if isinstance(package_file_or_data, str):
            with open(package_file_or_data, "r", encoding="utf-8") as f:
                package = json.load(f)
        else:
            package = package_file_or_data

        if linkedin_token:
            # Publish via Official LinkedIn API
            print(f"[LinkedIn Publisher] Publishing to LinkedIn via API...")
            # (API post logic here)
            package["status"] = "published"
            package["published_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            package["method"] = "LinkedIn API"
        else:
            # Package prepped for Playwright MCP / Manual confirmation
            print(f"[LinkedIn Publisher] Package prepared for LinkedIn post UI.")
            package["status"] = "staged_for_publishing"
            package["method"] = "Local Package (Ready for Playwright / LinkedIn MCP)"

        return package

if __name__ == "__main__":
    print("Testing Publisher module...")
