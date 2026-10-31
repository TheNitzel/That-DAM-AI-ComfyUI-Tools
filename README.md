# ⚡ ComfyUI-ThatDAMAI

Official ComfyUI Custom Node Suite & In-Canvas Browser for **[That DAM AI](https://thatdamai.com)** (`http://localhost:3200` Local & `https://thatdamai.com` Cloud/Hybrid).

Supports **ComfyUI Images (`.png`, `.webp`)** and **ComfyUI Generated Videos (`.mp4`, `.webm`, `.mov`, `.gif` — local files only)** with full ComfyUI node workflow & prompt graph preservation.

---

## ✨ Features

1. **`That DAM AI — Save Image & Workflow (Local / Cloud)` (`ThatDAMAI_SaveImage`)**
   - Saves generated images with embedded `prompt` and `workflow` PNG chunks into your ComfyUI output directory and immediately registers them in your local That DAM AI instance (`http://localhost:3200/api/images/import-local`) and/or syncs them to your Cloud/Hybrid workspace (`https://thatdamai.com/api/v1/ingest/init`).
2. **`That DAM AI — Register Local Video & Workflow (VHS / Local Only)` (`ThatDAMAI_RegisterLocalVideo`)**
   - Plugs directly into **`VHS_VideoCombine` (`Filenames` / `VHS_FILENAMES` output)** or any local video file path (`.mp4`, `.webm`, `.mov`, `.gif`).
   - Automatically attaches the active ComfyUI `prompt` and `workflow` node graph, extracts video dimensions, FPS, duration, and frame thumbnail, and indexes the video in That DAM AI while keeping the video file **strictly local on disk**.
3. **`That DAM AI — Load Asset, Mask & Workflow` (`ThatDAMAI_LoadAsset`)**
   - Pulls any asset's `IMAGE` tensor, `MASK` tensor, `positive_prompt`, `negative_prompt`, `seed`, and `workflow_json` from That DAM AI directly into a running ComfyUI workflow.
4. **In-Canvas ComfyUI Drawer (`⚡ That DAM AI` button)**
   - Adds a **`⚡ That DAM AI`** button to the ComfyUI menu bar.
   - Switch between **🏠 Local (`http://localhost:3200`)** and **☁️ Cloud (`https://thatdamai.com`)**.
   - Filter by **All Media**, **🖼️ Images**, or **🎬 Videos**, import local files on demand, and click **⚡ Load Workflow into Canvas** on any image or video to restore its exact ComfyUI node graph.

---

## 🚀 Installation

### Option 1: Via ComfyUI Manager (Git URL)
1. Open **ComfyUI Manager** → **Install via Git URL**
2. Paste:
   ```text
   https://github.com/TheNitzelBot/ComfyUI-ThatDAMAI.git
   ```
3. Restart ComfyUI.

### Option 2: Manual `git clone`
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/TheNitzelBot/ComfyUI-ThatDAMAI.git
```

### Option 3: Direct `.zip` Download from That DAM AI
Download `ComfyUI-ThatDAMAI.zip` directly from your running That DAM AI server at:
- Local: `http://localhost:3200/api/v1/comfyui-plugin/download`
- Cloud: `https://thatdamai.com/api/v1/comfyui-plugin/download`
Extract into `ComfyUI/custom_nodes/ComfyUI-ThatDAMAI` and restart ComfyUI.
