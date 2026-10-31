import hashlib
import io
import json
import os
import urllib.request
import numpy as np
from PIL import Image, PngImagePlugin
import torch

try:
    import folder_paths
except ImportError:
    folder_paths = None


def _get_default_output_dir():
    if folder_paths is not None and hasattr(folder_paths, "get_output_directory"):
        return folder_paths.get_output_directory()
    return os.path.abspath("./output")


class ThatDAMAI_SaveImage:
    """
    Inbound ComfyUI Node: Saves generated images with full ComfyUI workflow & prompt JSON
    and imports them directly into That DAM AI (Local http://localhost:3200 and/or Cloud https://thatdamai.com).
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "local_url": ("STRING", {"default": os.environ.get("THATDAMAI_LOCAL_URL", "http://localhost:3200")}),
                "cloud_url": ("STRING", {"default": os.environ.get("THATDAMAI_URL", "https://thatdamai.com")}),
                "api_key": ("STRING", {"default": os.environ.get("THATDAMAI_API_KEY", "")}),
                "target_mode": (["local_only", "local_and_cloud", "cloud_only", "hybrid_thumbs_cloud_raw_onprem"],),
                "subfolder": ("STRING", {"default": "ThatDAMAI"}),
            },
            "optional": {
                "positive_prompt": ("STRING", {"default": ""}),
                "negative_prompt": ("STRING", {"default": ""}),
                "model_name": ("STRING", {"default": ""}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF}),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("images", "thatdamai_asset_ids")
    FUNCTION = "save_to_thatdamai"
    OUTPUT_NODE = True
    CATEGORY = "ThatDAMAI"

    def save_to_thatdamai(
        self,
        images,
        local_url,
        cloud_url,
        api_key,
        target_mode,
        subfolder,
        positive_prompt="",
        negative_prompt="",
        model_name="",
        seed=0,
        prompt=None,
        extra_pnginfo=None,
    ):
        local_base = (local_url or "http://localhost:3200").rstrip("/")
        cloud_base = (cloud_url or "https://thatdamai.com").rstrip("/")
        uploaded_ids = []

        out_root = _get_default_output_dir()
        target_dir = os.path.join(out_root, subfolder.strip("/\\")) if subfolder.strip("/\\") else out_root
        os.makedirs(target_dir, exist_ok=True)

        workflow_json = extra_pnginfo.get("workflow") if isinstance(extra_pnginfo, dict) else None

        for idx, image_tensor in enumerate(images):
            arr = 255.0 * image_tensor.cpu().numpy()
            pil_img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

            pnginfo = PngImagePlugin.PngInfo()
            if prompt is not None:
                pnginfo.add_text("prompt", json.dumps(prompt))
            if extra_pnginfo is not None:
                for k, v in extra_pnginfo.items():
                    pnginfo.add_text(k, json.dumps(v))

            buf = io.BytesIO()
            pil_img.save(buf, format="PNG", pnginfo=pnginfo)
            png_bytes = buf.getvalue()
            file_hash = hashlib.sha256(png_bytes).hexdigest()
            file_name = f"ThatDAMAI_{file_hash[:12]}_{idx}.png"
            local_file_path = os.path.abspath(os.path.join(target_dir, file_name))

            # 1. Save locally & register in local That DAM AI instance
            if target_mode in ("local_only", "local_and_cloud", "hybrid_thumbs_cloud_raw_onprem"):
                with open(local_file_path, "wb") as f:
                    f.write(png_bytes)

                local_payload = {
                    "file_path": local_file_path,
                    "positive_prompt": positive_prompt or None,
                    "negative_prompt": negative_prompt or None,
                    "model_name": model_name or None,
                    "seed": seed if seed else None,
                    "img_width": pil_img.width,
                    "img_height": pil_img.height,
                    "prompt_json": prompt,
                    "workflow_json": workflow_json,
                }
                try:
                    req = urllib.request.Request(
                        f"{local_base}/api/images/import-local",
                        data=json.dumps(local_payload).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    with urllib.request.urlopen(req, timeout=15) as resp:
                        res_data = json.loads(resp.read().decode("utf-8"))
                        rec = res_data.get("image") or {}
                        if rec.get("id"):
                            uploaded_ids.append(str(rec["id"]))
                except Exception as e:
                    print(f"[That DAM AI] Local import warning: {e}")

            # 2. Optionally upload to Cloud / Hybrid R2
            if target_mode in ("local_and_cloud", "cloud_only", "hybrid_thumbs_cloud_raw_onprem") and api_key.strip():
                storage_mode = (
                    "hybrid_thumbs_cloud_raw_onprem"
                    if target_mode == "hybrid_thumbs_cloud_raw_onprem"
                    else "full_cloud"
                )
                init_payload = {
                    "file_name": file_name,
                    "file_path": local_file_path if target_mode != "cloud_only" else f"{subfolder.rstrip('/')}/{file_name}",
                    "file_size": len(png_bytes),
                    "file_hash": file_hash,
                    "storage_mode": storage_mode,
                    "metadata": {
                        "media_type": "image",
                        "img_width": pil_img.width,
                        "img_height": pil_img.height,
                        "positive_prompt": positive_prompt,
                        "negative_prompt": negative_prompt,
                        "model_name": model_name,
                        "seed": seed,
                        "prompt_json": prompt,
                        "workflow_json": workflow_json,
                    },
                }
                try:
                    req = urllib.request.Request(
                        f"{cloud_base}/api/v1/ingest/init",
                        data=json.dumps(init_payload).encode("utf-8"),
                        headers={
                            "Authorization": f"Bearer {api_key.strip()}",
                            "Content-Type": "application/json",
                        },
                        method="POST",
                    )
                    with urllib.request.urlopen(req, timeout=30) as resp:
                        result = json.loads(resp.read().decode("utf-8"))

                    upload_url = result.get("uploadUrl")
                    if upload_url and storage_mode == "full_cloud":
                        put_req = urllib.request.Request(
                            upload_url,
                            data=png_bytes,
                            headers={"Content-Type": "image/png"},
                            method="PUT",
                        )
                        urllib.request.urlopen(put_req, timeout=60).close()

                    image_rec = result.get("image") or {}
                    if image_rec.get("id") and str(image_rec["id"]) not in uploaded_ids:
                        uploaded_ids.append(str(image_rec["id"]))
                except Exception as e:
                    print(f"[That DAM AI] Cloud sync warning: {e}")

        return (images, ",".join(uploaded_ids))


class ThatDAMAI_RegisterLocalVideo:
    """
    Inbound ComfyUI Video Node (Local Files Only):
    Connects directly to VHS_VideoCombine (`Filenames` / `VHS_FILENAMES`) or a local video path (.mp4, .webm, .mov, .gif)
    and imports the video + full ComfyUI node workflow & prompt metadata into That DAM AI.
    Raw video files remain strictly local on disk (never uploaded to cloud object storage).
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "local_url": ("STRING", {"default": os.environ.get("THATDAMAI_LOCAL_URL", "http://localhost:3200")}),
            },
            "optional": {
                "vhs_filenames": ("VHS_FILENAMES",),
                "video_file_path": ("STRING", {"default": ""}),
                "positive_prompt": ("STRING", {"default": ""}),
                "negative_prompt": ("STRING", {"default": ""}),
                "model_name": ("STRING", {"default": ""}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF}),
                "fps": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 240.0}),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("video_file_path", "thatdamai_asset_id")
    FUNCTION = "register_local_video"
    OUTPUT_NODE = True
    CATEGORY = "ThatDAMAI"

    def register_local_video(
        self,
        local_url,
        vhs_filenames=None,
        video_file_path="",
        positive_prompt="",
        negative_prompt="",
        model_name="",
        seed=0,
        fps=0.0,
        prompt=None,
        extra_pnginfo=None,
    ):
        local_base = (local_url or "http://localhost:3200").rstrip("/")
        resolved_video_paths = []

        # 1. Extract output video path(s) from VHS_VideoCombine tuple: (save_output: bool, [file1, file2, ...])
        if vhs_filenames is not None:
            if isinstance(vhs_filenames, (list, tuple)) and len(vhs_filenames) >= 2 and isinstance(vhs_filenames[1], (list, tuple)):
                for p in vhs_filenames[1]:
                    if isinstance(p, str) and p.lower().endswith((".mp4", ".webm", ".mov", ".gif", ".webp")):
                        resolved_video_paths.append(os.path.abspath(p))
            elif isinstance(vhs_filenames, (list, tuple)):
                for p in vhs_filenames:
                    if isinstance(p, str) and p.lower().endswith((".mp4", ".webm", ".mov", ".gif", ".webp")):
                        resolved_video_paths.append(os.path.abspath(p))

        # 2. Or explicit video_file_path string
        if video_file_path and isinstance(video_file_path, str) and video_file_path.strip():
            resolved_video_paths.append(os.path.abspath(video_file_path.strip()))

        workflow_json = extra_pnginfo.get("workflow") if isinstance(extra_pnginfo, dict) else None
        imported_ids = []
        primary_path = resolved_video_paths[-1] if resolved_video_paths else ""

        for vpath in resolved_video_paths:
            if not os.path.exists(vpath):
                continue

            payload = {
                "file_path": vpath,
                "positive_prompt": positive_prompt or None,
                "negative_prompt": negative_prompt or None,
                "model_name": model_name or None,
                "seed": seed if seed else None,
                "fps": fps if fps and fps > 0 else None,
                "prompt_json": prompt,
                "workflow_json": workflow_json,
            }

            try:
                req = urllib.request.Request(
                    f"{local_base}/api/images/import-local",
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=20) as resp:
                    res_data = json.loads(resp.read().decode("utf-8"))
                    rec = res_data.get("image") or {}
                    if rec.get("id"):
                        imported_ids.append(str(rec["id"]))
            except Exception as e:
                print(f"[That DAM AI] Failed to import local video {vpath}: {e}")

        return (primary_path, ",".join(imported_ids))


class ThatDAMAI_LoadAsset:
    """
    Outbound ComfyUI Node: Pulls an image, alpha mask, prompt, seed, and workflow JSON
    from That DAM AI (Local or Cloud) back into the ComfyUI execution graph.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "asset_id": ("STRING", {"default": "1"}),
                "api_url": ("STRING", {"default": os.environ.get("THATDAMAI_LOCAL_URL", "http://localhost:3200")}),
                "api_key": ("STRING", {"default": os.environ.get("THATDAMAI_API_KEY", "")}),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK", "STRING", "STRING", "INT", "STRING")
    RETURN_NAMES = ("image", "mask", "positive_prompt", "negative_prompt", "seed", "workflow_json")
    FUNCTION = "load_from_thatdamai"
    CATEGORY = "ThatDAMAI"

    def load_from_thatdamai(self, asset_id, api_url, api_key):
        base_url = (api_url or "http://localhost:3200").rstrip("/")
        headers = {"Authorization": f"Bearer {api_key.strip()}"} if api_key and api_key.strip() else {}

        meta_req = urllib.request.Request(f"{base_url}/api/images/{asset_id}", headers=headers)
        with urllib.request.urlopen(meta_req, timeout=20) as meta_resp:
            meta = json.loads(meta_resp.read().decode("utf-8"))

        file_req = urllib.request.Request(f"{base_url}/api/images/file/{asset_id}", headers=headers)
        with urllib.request.urlopen(file_req, timeout=60) as file_resp:
            img_bytes = file_resp.read()

        pil_img = Image.open(io.BytesIO(img_bytes))
        rgb = pil_img.convert("RGB")
        rgb_np = np.array(rgb).astype(np.float32) / 255.0
        image_tensor = torch.from_numpy(rgb_np)[None,]

        if "A" in pil_img.getbands():
            alpha_np = np.array(pil_img.getchannel("A")).astype(np.float32) / 255.0
            mask_tensor = 1.0 - torch.from_numpy(alpha_np)
        else:
            mask_tensor = torch.zeros((pil_img.height, pil_img.width), dtype=torch.float32)

        pos_prompt = meta.get("positive_prompt") or ""
        neg_prompt = meta.get("negative_prompt") or ""
        seed = int(meta.get("seed") or 0)
        wf = meta.get("raw_workflow_json") or meta.get("workflow_json") or "{}"
        workflow_str = wf if isinstance(wf, str) else json.dumps(wf)

        return (image_tensor, mask_tensor, pos_prompt, neg_prompt, seed, workflow_str)


NODE_CLASS_MAPPINGS = {
    "ThatDAMAI_SaveImage": ThatDAMAI_SaveImage,
    "ThatDAMAI_RegisterLocalVideo": ThatDAMAI_RegisterLocalVideo,
    "ThatDAMAI_LoadAsset": ThatDAMAI_LoadAsset,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ThatDAMAI_SaveImage": "That DAM AI — Save Image & Workflow (Local / Cloud)",
    "ThatDAMAI_RegisterLocalVideo": "That DAM AI — Register Local Video & Workflow (VHS / Local Only)",
    "ThatDAMAI_LoadAsset": "That DAM AI — Load Asset, Mask & Workflow",
}
