"""
ComfyUI Custom Nodes & Web Extension for That DAM AI (https://thatdamai.com)
Bidirectional ComfyUI Integration:
  1. ThatDAMAI_SaveImage — Streams generated images, prompts & full ComfyUI workflows into That DAM AI.
  2. ThatDAMAI_LoadAsset — Pulls cloud or hybrid assets, masks, prompts, seeds & workflows out of That DAM AI.
  3. WEB_DIRECTORY ("./web") — Adds an in-canvas "⚡ That DAM AI" Cloud Browser & One-Click Workflow Loader.
"""

from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
