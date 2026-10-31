/**
 * packages/comfyui-thatdamai/web/thatdamai_sidebar.js
 * ComfyUI Web Extension for That DAM AI (http://localhost:3200 & https://thatdamai.com)
 * Adds a "⚡ That DAM AI" button to the ComfyUI menu bar to browse Local/Cloud Images & Videos,
 * import local ComfyUI output files, and reconstruct full ComfyUI node workflows onto the canvas.
 */

import { app } from "../../scripts/app.js";

app.registerExtension({
  name: "ThatDAMAI.AssetBrowser",
  async setup() {
    const btn = document.createElement("button");
    btn.textContent = "⚡ That DAM AI";
    btn.title = "Browse That DAM AI Images & Local Videos, Import Outputs, and Load Workflows";
    btn.style.cssText =
      "background:linear-gradient(135deg,#8b5cf6,#6366f1);color:#fff;border:none;border-radius:6px;padding:4px 10px;cursor:pointer;font-weight:600;margin-left:6px;";

    btn.addEventListener("click", () => openThatDamAiDrawer());

    const menu = document.querySelector(".comfy-menu");
    if (menu) {
      menu.appendChild(btn);
    } else {
      document.body.appendChild(btn);
      btn.style.position = "fixed";
      btn.style.bottom = "16px";
      btn.style.right = "16px";
      btn.style.zIndex = "9999";
    }
  },
});

function openThatDamAiDrawer() {
  let existing = document.getElementById("thatdamai-comfy-drawer");
  if (existing) {
    existing.style.display = existing.style.display === "none" ? "flex" : "none";
    return;
  }

  const savedUrl = localStorage.getItem("thatdamai_api_url") || "http://localhost:3200";
  const savedToken = localStorage.getItem("thatdamai_jwt_or_key") || "";

  const drawer = document.createElement("div");
  drawer.id = "thatdamai-comfy-drawer";
  drawer.style.cssText =
    "position:fixed;top:0;right:0;width:440px;height:100vh;background:#11131e;color:#f3f4f6;border-left:1px solid #252a40;z-index:10000;display:flex;flex-direction:column;font-family:sans-serif;box-shadow:-8px 0 30px rgba(0,0,0,0.6);";

  drawer.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;padding:14px 16px;border-bottom:1px solid #252a40;background:#171a29;">
      <strong style="font-size:0.96rem;">⚡ That DAM AI — Images & Local Videos</strong>
      <button id="tdam-close-btn" style="background:none;border:none;color:#9ca3af;cursor:pointer;font-size:1.1rem;">✕</button>
    </div>
    <div style="padding:12px;border-bottom:1px solid #252a40;display:flex;flex-direction:column;gap:8px;">
      <div style="display:flex;gap:6px;">
        <input id="tdam-url-input" type="text" value="${savedUrl}" placeholder="http://localhost:3200 or https://thatdamai.com" style="flex:1;background:#090a0f;border:1px solid #252a40;color:#fff;padding:7px 10px;border-radius:6px;font-size:0.78rem;" />
        <button id="tdam-preset-local" title="Switch to Local That DAM AI" style="background:#1e293b;color:#e2e8f0;border:1px solid #334155;border-radius:6px;padding:0 8px;cursor:pointer;font-size:0.72rem;">🏠 Local</button>
        <button id="tdam-preset-cloud" title="Switch to Cloud That DAM AI" style="background:#1e293b;color:#e2e8f0;border:1px solid #334155;border-radius:6px;padding:0 8px;cursor:pointer;font-size:0.72rem;">☁️ Cloud</button>
      </div>
      <input id="tdam-token-input" type="password" value="${savedToken}" placeholder="Optional API Key (tdai_live_... for Cloud)" style="background:#090a0f;border:1px solid #252a40;color:#fff;padding:7px 10px;border-radius:6px;font-size:0.78rem;" />
      <div style="display:flex;gap:6px;">
        <input id="tdam-search-input" type="text" placeholder="Search prompt, model, filename..." style="flex:1;background:#090a0f;border:1px solid #252a40;color:#fff;padding:7px 10px;border-radius:6px;font-size:0.78rem;" />
        <select id="tdam-media-select" style="background:#090a0f;border:1px solid #252a40;color:#fff;padding:7px 8px;border-radius:6px;font-size:0.76rem;">
          <option value="">All Media</option>
          <option value="image">🖼️ Images</option>
          <option value="video">🎬 Videos</option>
        </select>
        <button id="tdam-fetch-btn" style="background:#8b5cf6;color:#fff;border:none;border-radius:6px;padding:7px 12px;cursor:pointer;font-weight:600;font-size:0.78rem;">Fetch</button>
      </div>
      <div style="display:flex;gap:6px;padding-top:4px;border-top:1px solid #1e2336;">
        <input id="tdam-import-path" type="text" placeholder="Local file path (.mp4 / .webm / .png) to import..." style="flex:1;background:#090a0f;border:1px solid #252a40;color:#fff;padding:6px 10px;border-radius:6px;font-size:0.75rem;" />
        <button id="tdam-import-btn" style="background:#10b981;color:#fff;border:none;border-radius:6px;padding:6px 10px;cursor:pointer;font-weight:600;font-size:0.75rem;">📥 Import Local</button>
      </div>
    </div>
    <div id="tdam-assets-list" style="flex:1;overflow-y:auto;padding:12px;display:grid;grid-template-columns:1fr 1fr;gap:10px;"></div>
  `;

  document.body.appendChild(drawer);

  document.getElementById("tdam-close-btn").addEventListener("click", () => {
    drawer.style.display = "none";
  });

  document.getElementById("tdam-preset-local").addEventListener("click", () => {
    document.getElementById("tdam-url-input").value = "http://localhost:3200";
    loadAssets();
  });

  document.getElementById("tdam-preset-cloud").addEventListener("click", () => {
    document.getElementById("tdam-url-input").value = "https://thatdamai.com";
    loadAssets();
  });

  const loadAssets = async () => {
    const apiUrl = document.getElementById("tdam-url-input").value.trim().replace(/\/+$/, "");
    const token = document.getElementById("tdam-token-input").value.trim();
    const search = document.getElementById("tdam-search-input").value.trim();
    const mediaType = document.getElementById("tdam-media-select").value;
    localStorage.setItem("thatdamai_api_url", apiUrl);
    localStorage.setItem("thatdamai_jwt_or_key", token);

    const listEl = document.getElementById("tdam-assets-list");
    listEl.innerHTML = `<div style="grid-column:1/-1;color:#9ca3af;font-size:0.82rem;">⏳ Loading assets from ${apiUrl}...</div>`;

    try {
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const qs = new URLSearchParams();
      if (search) qs.set("search", search);
      if (mediaType) qs.set("mediaType", mediaType);
      const endpoint = token && !apiUrl.includes("localhost")
        ? `${apiUrl}/api/v1/images?${qs.toString()}`
        : `${apiUrl}/api/images?${qs.toString()}`;
      const res = await fetch(endpoint, { headers });
      const data = await res.json();
      const images = data.images || [];

      if (images.length === 0) {
        listEl.innerHTML = `<div style="grid-column:1/-1;color:#9ca3af;font-size:0.82rem;">No matching assets found.</div>`;
        return;
      }

      listEl.innerHTML = "";
      for (const img of images) {
        const isVideo = img.media_type === "video" || /\.(mp4|webm|mov|gif)$/i.test(img.file_name || "");
        const card = document.createElement("div");
        card.style.cssText =
          "background:#171a29;border:1px solid #252a40;border-radius:8px;overflow:hidden;display:flex;flex-direction:column;justify-content:space-between;position:relative;";
        const thumbSrc = img.cloud_object_key
          ? `${apiUrl}/r2/${encodeURIComponent(img.cloud_object_key)}`
          : `${apiUrl}/api/images/thumb/${img.id}`;

        const badgeHtml = isVideo
          ? `<span style="position:absolute;top:6px;right:6px;background:rgba(15,23,42,0.9);color:#38bdf8;border:1px solid rgba(56,189,248,0.4);border-radius:4px;padding:2px 5px;font-size:0.65rem;font-weight:700;">🎬 VIDEO${img.duration ? " " + Number(img.duration).toFixed(1) + "s" : ""}</span>`
          : "";

        card.innerHTML = `
          ${badgeHtml}
          <img src="${thumbSrc}" style="width:100%;height:130px;object-fit:cover;background:#090a0f;" />
          <div style="padding:8px;font-size:0.75rem;">
            <div style="font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title="${img.file_name}">${img.file_name}</div>
            <div style="color:#9ca3af;margin:3px 0;">ID: #${img.id} ${img.model_name ? "• " + img.model_name : ""}</div>
            <button class="tdam-load-wf-btn" style="width:100%;margin-top:4px;background:#252a40;color:#fff;border:none;border-radius:4px;padding:5px;cursor:pointer;font-size:0.72rem;">⚡ Load Workflow into Canvas</button>
          </div>
        `;

        card.querySelector(".tdam-load-wf-btn").addEventListener("click", async () => {
          try {
            let wf = img.raw_workflow_json || img.workflow_json;
            let pr = img.raw_prompt_json || img.prompt_json;
            // Fetch full single asset details if workflow_json wasn't included in list view
            if (!wf && !pr) {
              const detailRes = await fetch(`${apiUrl}/api/images/${img.id}`, { headers });
              if (detailRes.ok) {
                const detailData = await detailRes.json();
                wf = detailData.raw_workflow_json || detailData.workflow_json;
                pr = detailData.raw_prompt_json || detailData.prompt_json;
              }
            }
            const graphData = wf || pr;
            if (graphData && typeof app.loadGraphData === "function") {
              app.loadGraphData(typeof graphData === "string" ? JSON.parse(graphData) : graphData);
            } else {
              alert(`Asset #${img.id} does not contain an embedded ComfyUI workflow JSON.`);
            }
          } catch (e) {
            alert(`Failed to load workflow: ${e.message}`);
          }
        });

        listEl.appendChild(card);
      }
    } catch (err) {
      listEl.innerHTML = `<div style="grid-column:1/-1;color:#f87171;font-size:0.8rem;">Error connecting to ${apiUrl}: ${err.message}</div>`;
    }
  };

  document.getElementById("tdam-import-btn").addEventListener("click", async () => {
    const apiUrl = document.getElementById("tdam-url-input").value.trim().replace(/\/+$/, "");
    const filePath = document.getElementById("tdam-import-path").value.trim();
    if (!filePath) {
      alert("Enter a local file path (.mp4, .webm, .mov, .gif, .png) first.");
      return;
    }
    try {
      let workflowJson = null;
      if (app.graph && typeof app.graph.serialize === "function") {
        workflowJson = app.graph.serialize();
      }
      const res = await fetch(`${apiUrl}/api/images/import-local`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          file_path: filePath,
          workflow_json: workflowJson,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Import failed");
      document.getElementById("tdam-import-path").value = "";
      loadAssets();
    } catch (e) {
      alert("Local import error: " + e.message);
    }
  });

  document.getElementById("tdam-fetch-btn").addEventListener("click", loadAssets);
  document.getElementById("tdam-media-select").addEventListener("change", loadAssets);
  loadAssets();
}
