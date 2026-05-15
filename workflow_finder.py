#!/usr/bin/env python3
"""
ComfyUI Workflow Finder  v2.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Semantic search + visual graph preview for ComfyUI workflow JSON files.

Save to: C:\py\workflow_finder.py
Run:     python C:\py\workflow_finder.py

Requirements:
  pip install anthropic          (only needed for AI mode)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
import os
import re
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Optional

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

# ── Shared colour palette (used by WorkflowFinder and WildSearchWindow) ──────
BG   = "#111122"
PNL  = "#0c0c1e"
PNL2 = "#080818"
ACC  = "#6c72ff"
DIM  = "#3a3a66"
FG   = "#d4d4f0"
FG2  = "#8888bb"
MONO = ("Consolas", 10)
MONO_B = ("Consolas", 10, "bold")


# ─────────────────────────────────────────────────────────────────────────────
# Node-type → capability keyword map
# ─────────────────────────────────────────────────────────────────────────────
NODE_CAPS: dict = {
    "VHS_LoadVideo":                 "load video read video video input file",
    "VHS_LoadImages":                "load images batch video frames",
    "VHS_LoadImagePath":             "load image path",
    "VHS_VideoCombine":              "save video export video combine frames output",
    "VHS_LoadAudio":                 "load audio sound",
    "LoadVideo":                     "load video read video",
    "VideoPathLoader":               "load video path",
    "SaveVideo":                     "save video output",
    "VideoToImages":                 "video extract frames split",
    "LoadAudio":                     "load audio sound music",
    "SaveAudio":                     "save audio output",
    "LTXVAddAudio":                  "ltx audio video sync",
    "EmptyAudioLatent":              "audio latent generate",
    "LoadImage":                     "load image input",
    "LoadImageMask":                 "load image mask",
    "SaveImage":                     "save image output",
    "PreviewImage":                  "preview image",
    "ImageBatch":                    "batch multiple images",
    "ImageListToImageBatch":         "image list batch",
    "RepeatLatentBatch":             "repeat batch",
    "Florence2":                     "caption describe image vision generate prompt florence",
    "Florence2toCoordinates":        "florence caption detect coordinates",
    "WD14Tagger":                    "tag caption tagger wd14 booru danbooru",
    "BLIPCaption":                   "blip caption describe image",
    "LLaVALoader":                   "llava vision language model",
    "JoyCaptionAlpha":               "joycaption caption describe generate prompt",
    "JoyCaption":                    "joycaption caption describe",
    "Moondream":                     "moondream vision caption describe",
    "MoondreamBatchQueries":         "moondream vision caption batch",
    "LLMChat":                       "llm language model chat generate text prompt",
    "OllamaGenerate":                "ollama llm generate text prompt",
    "LLMPromptGenerator":            "llm generate prompt",
    "QwenVL":                        "qwen vision language caption describe image prompt",
    "aistudynow_QwenVLModel":        "qwen vision language caption describe",
    "aistudynow_QwenVLRun":          "qwen vision run caption describe",
    "CaptionToPrompt":               "caption to prompt convert generate",
    "ImageToPrompt":                 "image to prompt generate caption convert",
    "GPT4Vision":                    "gpt4 vision describe caption",
    "WanVideoPromptGenerator":       "wan video prompt generate",
    "CLIPInterrogator":              "clip interrogate caption reverse-prompt",
    "DeepDanbooru":                  "danbooru tag caption",
    "CLIPTextEncode":                "text prompt encode clip",
    "CLIPTextEncodeFlux":            "flux text prompt encode",
    "CLIPTextEncodeSD3":             "sd3 text prompt encode",
    "CLIPTextEncodeHunyuan":         "hunyuan text prompt encode",
    "CLIPTextEncodeWan":             "wan text prompt encode",
    "CLIPTextEncodeLTXV":            "ltx text prompt encode",
    "CheckpointLoaderSimple":        "checkpoint model sd sdxl load",
    "UNETLoader":                    "unet model flux load",
    "CLIPLoader":                    "clip text encoder load",
    "VAELoader":                     "vae load",
    "LoraLoader":                    "lora style fine-tune adapter",
    "LoraLoaderModelOnly":           "lora model adapter",
    "DualCLIPLoader":                "dual clip load flux sd3",
    "TripleCLIPLoader":              "triple clip load",
    "KSampler":                      "sample generate diffusion denoise",
    "KSamplerAdvanced":              "sample generate advanced diffusion",
    "SamplerCustomAdvanced":         "sample generate custom guider",
    "FluxGuidance":                  "flux cfg guidance",
    "ModelSamplingFlux":             "flux sampling",
    "LTXVLoader":                    "ltx ltx-video video generate load",
    "LTXVSampler":                   "ltx ltx-video video generate sample",
    "LTXVScheduler":                 "ltx ltx-video schedule",
    "LTXVConditioning":              "ltx conditioning",
    "LTXVImgToVideo":                "ltx image to video i2v",
    "WanVideoSampler":               "wan video generate sample",
    "WanVideoLoader":                "wan video model load",
    "WanVideoEncode":                "wan video encode",
    "HunyuanVideoSampler":           "hunyuan video generate sample",
    "HunyuanVideoLoader":            "hunyuan video model load",
    "ControlNetLoader":              "controlnet control load",
    "ControlNetApply":               "controlnet apply control",
    "ControlNetApplyAdvanced":       "controlnet apply advanced",
    "DWPose_Preprocessor":           "pose dwpose controlnet skeleton",
    "OpenposePreprocessor":          "openpose pose skeleton",
    "CannyEdgePreprocessor":         "canny edge lines",
    "DepthAnythingV2Preprocessor":   "depth depthmap",
    "IPAdapter":                     "ip-adapter style transfer face reference",
    "IPAdapterModelLoader":          "ip-adapter load",
    "IPAdapterAdvanced":             "ip-adapter advanced style",
    "IPAdapterFaceID":               "ip-adapter face id identity",
    "FaceRestoreWithModel":          "face restore fix",
    "ReActorFaceSwap":               "face swap reactor",
    "PulidModelLoader":              "pulid face id consistency",
    "InstantIDModelLoader":          "instantid face id consistency",
    "ImpactFaceDetailer":            "face detail fix refine",
    "SAMModelLoader":                "sam segment mask load",
    "SAMPredictor":                  "sam segment mask detect",
    "GroundingDinoSAMSegment":       "grounding dino segment detect object",
    "SegmentAnything2":              "sam2 segment mask video tracking",
    "InpaintModelConditioning":      "inpaint fill mask repair",
    "VAEEncodeForInpaint":           "inpaint vae encode",
    "GrowMask":                      "mask grow expand",
    "GrowMaskWithBlur":              "mask grow blur",
    "MaskToImage":                   "mask image convert",
    "LanPaintNode":                  "lanpaint inpaint",
    "ImageUpscaleWithModel":         "upscale super resolution enhance",
    "UpscaleModelLoader":            "upscale model load",
    "UltimateSDUpscale":             "upscale ultimate tile",
    "QwenImageEditLoader":           "qwen image edit load",
    "QwenImageEdit":                 "qwen image edit modify transform",
    "JoyAIImageEdit":                "joyai image edit modify",
    "JoyAILoader":                   "joyai load",
    "ReferenceLatent":               "reference latent conditioning consistent character",
    "VAEDecode":                     "vae decode image",
    "VAEEncode":                     "vae encode latent",
    "EmptyLatentImage":              "empty latent image",
    "LatentUpscale":                 "latent upscale",
    "ImageScale":                    "image resize scale",
    "ImageCrop":                     "image crop",
    "ConditioningConcat":            "conditioning combine concat",
    "ConditioningSetMask":           "conditioning mask region",
    "ImpactWildcardProcessor":       "wildcard prompt dynamic",
}


# ─────────────────────────────────────────────────────────────────────────────
# Node colour palette  (dark theme, keyed by node type)
# ─────────────────────────────────────────────────────────────────────────────
_NODE_COLORS: dict = {
    # Video I/O — teal
    "VHS_LoadVideo":"#0b3d36","VHS_VideoCombine":"#0b3d36",
    "VHS_LoadImages":"#0b3d36","VHS_LoadAudio":"#0b3d42",
    "LoadVideo":"#0b3d36","SaveVideo":"#0b3d36","VideoToImages":"#0b3d36",
    # Audio — slate blue
    "LoadAudio":"#1a2b3c","SaveAudio":"#1a2b3c",
    "LTXVAddAudio":"#1a2b3c","EmptyAudioLatent":"#1a2b3c",
    # Image I/O — navy
    "LoadImage":"#0d2855","SaveImage":"#0d2855",
    "PreviewImage":"#0d2855","LoadImageMask":"#0d2855",
    # Model loaders — deep purple
    "CheckpointLoaderSimple":"#2d0d55","UNETLoader":"#2d0d55",
    "CLIPLoader":"#2d0d55","VAELoader":"#2d0d55",
    "LoraLoader":"#2d0d55","LoraLoaderModelOnly":"#2d0d55",
    "DualCLIPLoader":"#2d0d55","TripleCLIPLoader":"#2d0d55",
    # Samplers — burnt orange
    "KSampler":"#5c2800","KSamplerAdvanced":"#5c2800",
    "SamplerCustomAdvanced":"#5c2800","LTXVSampler":"#5c2800",
    "WanVideoSampler":"#5c2800","HunyuanVideoSampler":"#5c2800",
    # CLIP / Text encode — forest green
    "CLIPTextEncode":"#0d3d0d","CLIPTextEncodeFlux":"#0d3d0d",
    "CLIPTextEncodeWan":"#0d3d0d","CLIPTextEncodeLTXV":"#0d3d0d",
    "CLIPTextEncodeSD3":"#0d3d0d","CLIPTextEncodeHunyuan":"#0d3d0d",
    # VAE — dark cyan
    "VAEDecode":"#003344","VAEEncode":"#003344","VAEEncodeForInpaint":"#003344",
    # Captioning / LLM — dark gold
    "Florence2":"#3d2e00","WD14Tagger":"#3d2e00","BLIPCaption":"#3d2e00",
    "JoyCaptionAlpha":"#3d2e00","JoyCaption":"#3d2e00","Moondream":"#3d2e00",
    "LLMChat":"#3d2e00","OllamaGenerate":"#3d2e00","QwenVL":"#3d2e00",
    "aistudynow_QwenVLModel":"#3d2e00","aistudynow_QwenVLRun":"#3d2e00",
    "ImageToPrompt":"#3d2e00","CaptionToPrompt":"#3d2e00","CLIPInterrogator":"#3d2e00",
    # ControlNet — dark magenta
    "ControlNetLoader":"#3d003d","ControlNetApply":"#3d003d",
    "ControlNetApplyAdvanced":"#3d003d","DWPose_Preprocessor":"#3d003d",
    "OpenposePreprocessor":"#3d003d","CannyEdgePreprocessor":"#3d003d",
    "DepthAnythingV2Preprocessor":"#3d003d",
    # SAM / Segmentation — dark rust
    "SAMModelLoader":"#3d1500","SAMPredictor":"#3d1500",
    "GroundingDinoSAMSegment":"#3d1500","SegmentAnything2":"#3d1500",
    # Mask / Inpaint — dark maroon
    "GrowMask":"#2a1500","GrowMaskWithBlur":"#2a1500",
    "MaskToImage":"#2a1500","InpaintModelConditioning":"#2a1500","LanPaintNode":"#2a1500",
    # LTX Video — dark teal-green
    "LTXVLoader":"#003333","LTXVScheduler":"#003333",
    "LTXVConditioning":"#003333","LTXVImgToVideo":"#003333",
    # Wan / Hunyuan Video
    "WanVideoLoader":"#003028","WanVideoEncode":"#003028","HunyuanVideoLoader":"#002830",
    # Flux
    "FluxGuidance":"#1a1500","ModelSamplingFlux":"#1a1500",
    # Upscale
    "ImageUpscaleWithModel":"#001a2a","UpscaleModelLoader":"#001a2a","UltimateSDUpscale":"#001a2a",
    # Qwen/Joy image edit — indigo
    "QwenImageEditLoader":"#1a0a3d","QwenImageEdit":"#1a0a3d",
    "JoyAIImageEdit":"#1a0a3d","JoyAILoader":"#1a0a3d",
    # IP-Adapter / Face — dark pink
    "IPAdapter":"#3d0025","IPAdapterModelLoader":"#3d0025","IPAdapterAdvanced":"#3d0025",
    "IPAdapterFaceID":"#3d0025","PulidModelLoader":"#3d0025","InstantIDModelLoader":"#3d0025",
    "ReActorFaceSwap":"#3d0025","FaceRestoreWithModel":"#3d0025","ImpactFaceDetailer":"#3d0025",
    # Reference / Conditioning
    "ReferenceLatent":"#001840","ConditioningConcat":"#001840","ConditioningSetMask":"#001840",
    # Default
    "default":"#1a1a35",
}

_LINK_COLORS: dict = {
    "IMAGE":"#2a7a55","LATENT":"#8a6a2a","MODEL":"#6a3a9a",
    "CLIP":"#4a6a3a","VAE":"#2a6a8a","CONDITIONING":"#2a5a7a",
    "VIDEO":"#2a7a6a","AUDIO":"#4a4a9a","MASK":"#8a3a2a",
}

HEADER_H_WORLD = 30
NODE_MIN_W     = 180
NODE_MIN_H     = 60


def _node_color(node_type: str) -> str:
    if node_type in _NODE_COLORS:
        return _NODE_COLORS[node_type]
    for k in _NODE_COLORS:
        if k != "default" and len(k) >= 5 and node_type.startswith(k[:min(8,len(k))]):
            return _NODE_COLORS[k]
    return _NODE_COLORS["default"]


def _link_color(ltype: str) -> str:
    lt = str(ltype).upper()
    for k, v in _LINK_COLORS.items():
        if k in lt:
            return v
    return "#3a3a6a"


def _lighten(hx: str, amt: int = 30) -> str:
    try:
        r = min(int(hx[1:3], 16) + amt, 255)
        g = min(int(hx[3:5], 16) + amt, 255)
        b = min(int(hx[5:7], 16) + amt, 255)
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return hx


# ─────────────────────────────────────────────────────────────────────────────
# Workflow JSON parsing
# ─────────────────────────────────────────────────────────────────────────────

def extract_workflow_fingerprint(json_path: str) -> Optional[dict]:
    try:
        with open(json_path, "r", encoding="utf-8", errors="ignore") as f:
            data = json.load(f)
    except Exception:
        return None

    nodes, titles, snippets = [], [], []

    def harvest(ntype, ntitle, wvals):
        if ntype: nodes.append(ntype)
        if ntitle and ntitle != ntype: titles.append(ntitle)
        for v in wvals:
            if isinstance(v, str) and 15 < len(v) < 600:
                snippets.append(v[:200])

    if isinstance(data, dict) and "nodes" in data:
        for n in data.get("nodes", []):
            if isinstance(n, dict):
                harvest(n.get("type",""), n.get("title",""), n.get("widgets_values",[]))
    elif isinstance(data, dict):
        for _id, n in data.items():
            if isinstance(n, dict):
                ct = n.get("class_type","")
                tl = n.get("_meta",{}).get("title","")
                vals = [v for v in n.get("inputs",{}).values() if isinstance(v, str)]
                harvest(ct, tl, vals)

    if not nodes:
        return None

    try:
        st = os.stat(json_path)
        created  = st.st_ctime   # creation time on Windows
        modified = st.st_mtime   # last modified (= last saved in ComfyUI)
    except Exception:
        created = modified = 0.0

    return {
        "path": json_path,
        "filename": Path(json_path).name,
        "nodes": list(dict.fromkeys(nodes)),
        "titles": list(dict.fromkeys(titles)),
        "text_snippets": snippets[:6],
        "node_count": len(nodes),
        "created":  created,
        "modified": modified,
        "score": 0.0,
        "matched_terms": [],
    }


def parse_graph_data(json_path: str) -> Optional[dict]:
    """Parse workflow into graph data. Returns error key if not renderable."""
    try:
        with open(json_path, "r", encoding="utf-8", errors="ignore") as f:
            data = json.load(f)
    except Exception:
        return None

    if not (isinstance(data, dict) and "nodes" in data):
        return {"error": "api_format"}

    raw_nodes = data.get("nodes", [])
    raw_links = data.get("links", [])

    if not any("pos" in n for n in raw_nodes if isinstance(n, dict)):
        return {"error": "no_positions"}

    node_map = {}
    for n in raw_nodes:
        if not isinstance(n, dict):
            continue
        nid = n.get("id")
        if nid is None:
            continue
        pos = n.get("pos", [0, 0])
        if isinstance(pos, dict):
            pos = [pos.get("0", 0), pos.get("1", 0)]
        pos = [float(pos[0]), float(pos[1])]

        size = n.get("size", {})
        if isinstance(size, dict):
            sw, sh = float(size.get("0", 200)), float(size.get("1", 80))
        elif isinstance(size, (list, tuple)) and len(size) >= 2:
            sw, sh = float(size[0]), float(size[1])
        else:
            sw, sh = 200.0, 80.0

        inputs  = n.get("inputs",  []) or []
        outputs = n.get("outputs", []) or []

        node_map[int(nid)] = {
            "id":          int(nid),
            "type":        n.get("type", "?"),
            "title":       n.get("title", "") or n.get("type", "?"),
            "x": pos[0], "y": pos[1],
            "w": max(sw, NODE_MIN_W), "h": max(sh, NODE_MIN_H),
            "num_inputs":  len(inputs),
            "num_outputs": len(outputs),
        }

    links = []
    for lk in raw_links:
        if isinstance(lk, (list, tuple)) and len(lk) >= 6:
            links.append({
                "from_id":   int(lk[1]),
                "from_slot": int(lk[2]),
                "to_id":     int(lk[3]),
                "to_slot":   int(lk[4]),
                "type":      str(lk[5]),
            })

    return {"nodes": node_map, "links": links}


# ─────────────────────────────────────────────────────────────────────────────
# Local search
# ─────────────────────────────────────────────────────────────────────────────

def _tok(text: str) -> set:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def score_local(fp: dict, query: str) -> dict:
    q = _tok(query)
    matched = set()
    score = 0.0
    for nt in fp["nodes"]:
        caps = NODE_CAPS.get(nt, re.sub(r"([A-Z])", r" \1", nt).lower())
        hits = q & _tok(caps)
        if hits:
            score += len(hits) * 2
            matched |= hits
    for t in fp["titles"]:
        hits = q & _tok(t)
        if hits:
            score += len(hits); matched |= hits
    for s in fp["text_snippets"]:
        if any(t in s.lower() for t in q if len(t) > 3):
            score += 0.5
    fn_hits = q & _tok(fp["filename"])
    score += len(fn_hits) * 1.5; matched |= fn_hits
    fp = dict(fp)
    fp["matched_terms"] = sorted(matched)
    fp["score"] = score
    return fp


def search_local(fps: list, query: str, top_n: int = 100) -> list:
    scored = [score_local(fp, query) for fp in fps]
    scored = [fp for fp in scored if fp["score"] > 0]
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_n]


def search_claude(fps: list, query: str) -> list:
    candidates = search_local(fps, query, top_n=80) or fps[:80]
    lines = [
        f"[{i}] FILE: {fp['filename']}\n"
        f"  NODES: {', '.join(fp['nodes'][:35])}\n"
        f"  TITLES: {', '.join(fp['titles'][:12])}"
        for i, fp in enumerate(candidates)
    ]
    prompt = (
        f'You analyze ComfyUI workflow JSON files.\nQuery: "{query}"\n\n'
        "Candidates:\n" + "\n".join(lines) +
        '\n\nReturn ONLY a JSON array: [{"index":<int>,"score":<float>,"reason":"<phrase>"},...]. '
        "Sort desc. Return [] if none match. No markdown."
    )
    try:
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=1500,
            messages=[{"role": "user", "content": prompt}])
        raw = re.sub(r"```[a-z]*", "", msg.content[0].text.strip()).strip("`").strip()
        matches = json.loads(raw)
        results = []
        for m in matches:
            idx = m.get("index", -1)
            if 0 <= idx < len(candidates):
                fp = dict(candidates[idx])
                fp["score"] = float(m.get("score", 0))
                fp["matched_terms"] = [m.get("reason", "")]
                results.append(fp)
        return results
    except Exception:
        return candidates


# ─────────────────────────────────────────────────────────────────────────────
# Graph Canvas Widget
# ─────────────────────────────────────────────────────────────────────────────

class GraphCanvas(tk.Canvas):
    """
    Zoomable / pannable node-graph renderer.

    Controls:
      Scroll wheel  — zoom centred on cursor
      Left drag     — pan
      Right-click   — context menu (fit / 100%)
      F key         — fit to screen
    """

    _PAD          = 48
    _SLOT_SPACING = 22.0   # world-unit vertical spacing between slots
    _SLOT_R       = 4.0    # slot dot radius in world units (scaled)

    def __init__(self, parent, **kw):
        kw.setdefault("bg", "#080818")
        kw.setdefault("highlightthickness", 0)
        super().__init__(parent, **kw)

        self._scale  = 1.0
        self._off_x  = 0.0
        self._off_y  = 0.0
        self._drag   = None
        self._graph  = None
        self._tip    = None

        self.bind("<ButtonPress-1>",   self._press)
        self.bind("<B1-Motion>",       self._drag_cb)
        self.bind("<ButtonRelease-1>", self._release)
        self.bind("<MouseWheel>",      self._scroll)
        self.bind("<Button-4>",        self._scroll)
        self.bind("<Button-5>",        self._scroll)
        self.bind("<Configure>",       self._resize)
        self.bind("<Motion>",          self._motion)
        self.bind("<Leave>",           self._hide_tip)
        self.bind("<f>",               lambda _: self.fit())
        self.bind("<F>",               lambda _: self.fit())

        ctx = tk.Menu(self, tearoff=0, bg="#1a1a3e", fg="#d0d0ff",
                      activebackground="#3a3a7e", font=("Consolas", 9))
        ctx.add_command(label="Fit to screen  [F]", command=self.fit)
        ctx.add_command(label="Reset zoom (100%)",  command=self._zoom_reset)
        self.bind("<Button-3>", lambda e: ctx.tk_popup(e.x_root, e.y_root))

    # ── Public ──────────────────────────────────────────────────────────

    def clear(self):
        self.delete("all"); self._graph = None; self._hide_tip()

    def show_message(self, line1: str, line2: str = ""):
        self.delete("all"); self._graph = None
        w = max(self.winfo_width(), 400); h = max(self.winfo_height(), 200)
        self.create_text(w//2, h//2 - 12, text=line1, fill="#3a3a88",
                         font=("Consolas", 12), justify="center")
        if line2:
            self.create_text(w//2, h//2 + 14, text=line2, fill="#2a2a55",
                             font=("Consolas", 9), justify="center")

    def load_workflow(self, path: str):
        self.clear()
        g = parse_graph_data(path)
        if g is None:
            self.show_message("Could not read workflow file."); return
        err = g.get("error")
        if err == "api_format":
            self.show_message("Graph preview requires UI-exported format.",
                              "Save from ComfyUI UI (not API format) to include node positions.")
            return
        if err == "no_positions":
            self.show_message("No node positions found.",
                              "Open in ComfyUI and re-save the workflow.")
            return
        if not g.get("nodes"):
            self.show_message("No nodes found in workflow."); return
        self._graph = g
        self.update_idletasks()
        self.fit()

    def fit(self):
        if not self._graph: return
        nodes = self._graph["nodes"]
        if not nodes: return
        xs  = [n["x"]           for n in nodes.values()]
        ys  = [n["y"]           for n in nodes.values()]
        xr  = [n["x"] + n["w"] for n in nodes.values()]
        yr  = [n["y"] + n["h"] for n in nodes.values()]
        bbx, bby = min(xs), min(ys)
        bbw = max(xr) - bbx
        bbh = max(yr) - bby
        cw = max(self.winfo_width(),  400)
        ch = max(self.winfo_height(), 200)
        P  = self._PAD
        self._scale = min((cw - P*2) / max(bbw,1),
                          (ch - P*2) / max(bbh,1), 2.0)
        self._off_x = P - bbx * self._scale
        self._off_y = P - bby * self._scale
        self._draw()

    def _zoom_reset(self):
        self._scale = 1.0; self._off_x = 0.0; self._off_y = 0.0; self._draw()

    # ── Coordinate helpers ──────────────────────────────────────────────

    def _w2c(self, wx, wy):
        return wx * self._scale + self._off_x, wy * self._scale + self._off_y

    def _c2w(self, cx, cy):
        return (cx - self._off_x) / self._scale, (cy - self._off_y) / self._scale

    # ── Drawing ─────────────────────────────────────────────────────────

    def _draw(self):
        if not self._graph: return
        self.delete("all")
        s = self._scale
        nodes = self._graph["nodes"]
        links = self._graph["links"]

        # Wires (drawn behind nodes)
        for lk in links:
            src = nodes.get(lk["from_id"]); dst = nodes.get(lk["to_id"])
            if not src or not dst: continue

            sy_src = min(HEADER_H_WORLD + (lk["from_slot"] + 0.5) * self._SLOT_SPACING,
                         src["h"] - 5)
            sy_dst = min(HEADER_H_WORLD + (lk["to_slot"]  + 0.5) * self._SLOT_SPACING,
                         dst["h"] - 5)
            x1, y1 = self._w2c(src["x"] + src["w"], src["y"] + sy_src)
            x2, y2 = self._w2c(dst["x"],             dst["y"] + sy_dst)

            dx = max(abs(x2 - x1) * 0.5, 50 * s)
            wc = _link_color(lk["type"])
            lw = max(1.0, s * 1.2)

            self.create_line(x1, y1, x1+dx, y1, x2-dx, y2, x2, y2,
                             fill=wc, width=lw, smooth=True, splinesteps=20)
            if s > 0.25:
                r = max(2.0, self._SLOT_R * s * 0.55)
                for px, py in [(x1, y1), (x2, y2)]:
                    self.create_oval(px-r, py-r, px+r, py+r, fill=wc, outline="")

        # Nodes
        for n in nodes.values():
            cx, cy = self._w2c(n["x"], n["y"])
            cw = n["w"] * s; ch = n["h"] * s
            hh = min(HEADER_H_WORLD * s, ch * 0.38)

            bg  = _node_color(n["type"])
            hdr = _lighten(bg, 28)
            brd = _lighten(bg, 55)

            self.create_rectangle(cx, cy, cx+cw, cy+ch,
                                  fill=bg, outline=brd, width=1)
            self.create_rectangle(cx, cy, cx+cw, cy+hh,
                                  fill=hdr, outline="")

            if cw > 36 and ch > 16:
                fs_h = max(6, min(10, int(9*s)))
                fs_t = max(5, min(8,  int(7*s)))
                label = n["title"] or n["type"]
                self.create_text(cx+cw/2, cy+hh/2, text=label,
                                 fill="#e8e8ff", font=("Consolas", fs_h, "bold"),
                                 anchor="center", width=cw-4)
                if ch > hh + fs_t*2 + 6:
                    self.create_text(cx+cw/2, cy+hh+fs_t+5, text=n["type"],
                                     fill="#6868aa", font=("Consolas", fs_t),
                                     anchor="center", width=cw-4)

            if s > 0.22:
                r = max(2.0, 3.5 * s)
                for i in range(n["num_inputs"]):
                    sy = HEADER_H_WORLD + (i+0.5)*self._SLOT_SPACING
                    if sy > n["h"]-4: break
                    dx2, dy2 = self._w2c(n["x"],           n["y"]+sy)
                    self.create_oval(dx2-r, dy2-r, dx2+r, dy2+r, fill="#6888bb", outline="")
                for i in range(n["num_outputs"]):
                    sy = HEADER_H_WORLD + (i+0.5)*self._SLOT_SPACING
                    if sy > n["h"]-4: break
                    dx2, dy2 = self._w2c(n["x"]+n["w"],    n["y"]+sy)
                    self.create_oval(dx2-r, dy2-r, dx2+r, dy2+r, fill="#88aa66", outline="")

        self.create_text(8, 8, text="Scroll=zoom  Drag=pan  F=fit  Right-click=menu",
                         fill="#252550", font=("Consolas", 8), anchor="nw")

    # ── Tooltip ─────────────────────────────────────────────────────────

    def _hit(self, cx, cy) -> Optional[dict]:
        if not self._graph: return None
        wx, wy = self._c2w(cx, cy)
        for n in self._graph["nodes"].values():
            if n["x"] <= wx <= n["x"]+n["w"] and n["y"] <= wy <= n["y"]+n["h"]:
                return n
        return None

    def _motion(self, e):
        n = self._hit(e.x, e.y)
        if n: self._show_tip(e.x+14, e.y, n)
        else:  self._hide_tip()

    def _show_tip(self, x, y, n):
        lines = [f"  {n['type']}  "]
        if n["title"] and n["title"] != n["type"]:
            lines.insert(0, f"  {n['title']}  ")
        lines += [f"  in:{n['num_inputs']}  out:{n['num_outputs']}  id:{n['id']}  "]
        if self._tip: self._tip.destroy()
        tip = tk.Toplevel(self)
        tip.wm_overrideredirect(True)
        tip.wm_geometry(f"+{self.winfo_rootx()+x}+{self.winfo_rooty()+y}")
        tk.Label(tip, text="\n".join(lines), bg="#1a1a40", fg="#c8c8ff",
                 font=("Consolas", 9), justify="left", relief="flat", bd=1,
                 padx=4, pady=4).pack()
        self._tip = tip

    def _hide_tip(self, _=None):
        if self._tip: self._tip.destroy(); self._tip = None

    # ── Interaction ─────────────────────────────────────────────────────

    def _press(self, e):   self.focus_set(); self._drag = (e.x, e.y); self._hide_tip()
    def _release(self, _): self._drag = None

    def _drag_cb(self, e):
        if self._drag and self._graph:
            self._off_x += e.x - self._drag[0]
            self._off_y += e.y - self._drag[1]
            self._drag = (e.x, e.y)
            self._draw()

    def _scroll(self, e):
        if not self._graph: return
        f = 1.12 if (e.num == 4 or e.delta > 0) else (1/1.12)
        self._off_x = e.x - f*(e.x - self._off_x)
        self._off_y = e.y - f*(e.y - self._off_y)
        self._scale = max(0.04, min(self._scale*f, 14.0))
        self._draw()

    def _resize(self, _):
        if self._graph: self.after_idle(self.fit)


# ─────────────────────────────────────────────────────────────────────────────
# Main Application
# ─────────────────────────────────────────────────────────────────────────────

class WorkflowFinder(tk.Tk):

    # Default locations added on first run (only if config file doesn't exist yet)
    DEFAULT_DIRS = [
        r"H:\Workflow.Master",
        r"C:\Comfy\ComfyUI\user\default\workflows",
        r"H:\Comfy\ComfyUI\user\default\workflows",
        r"C:\ComfyUI_windows_portable\ComfyUI\user\default\workflows",
    ]

    CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "workflow_finder_config.json")

    def __init__(self):
        super().__init__()
        self.title("ComfyUI Workflow Finder  v2")
        self.geometry("1200x840")
        self.configure(bg="#111122")
        self.minsize(900, 640)

        # dir_entries: list of {"path": str, "enabled": bool}
        self.dir_entries      = self._load_config()
        self._dir_row_widgets = []
        self.fingerprints     = []
        self.results          = []
        self._fp_by_dir: dict = {}   # dir_path -> [fingerprints]  for incremental updates
        self._last_q          = ""   # last node-search query
        self._last_mode       = "local"
        self._pb              = None  # progress bar widget, set during _build_ui

        self._build_styles()
        self._build_ui()

        enabled = [e["path"] for e in self.dir_entries if e["enabled"]]
        if enabled:
            self.after(200, self._start_scan)
        else:
            # No enabled locations — likely a first run, show welcome
            self.after(400, self._show_welcome)

    # ── Config persistence ───────────────────────────────────────────────

    def _show_welcome(self):
        """First-run welcome dialog explaining how to get started."""
        win = tk.Toplevel(self)
        win.title("Welcome to ComfyUI Workflow Finder")
        win.configure(bg=BG)
        win.resizable(False, False)
        win.grab_set()

        # Centre on screen
        win.update_idletasks()
        w, h = 580, 420
        x = (win.winfo_screenwidth()  - w) // 2
        y = (win.winfo_screenheight() - h) // 2
        win.geometry(f"{w}x{h}+{x}+{y}")

        ACC = "#6c72ff"

        tk.Label(win, text="⚡  Welcome to ComfyUI Workflow Finder",
                 bg=BG, fg=ACC, font=("Consolas", 13, "bold")).pack(pady=(20, 4))
        tk.Label(win, text="Let's get you set up in 3 steps.",
                 bg=BG, fg=FG2, font=("Consolas", 10)).pack(pady=(0, 16))

        steps = tk.Frame(win, bg=PNL, padx=20, pady=16)
        steps.pack(fill="x", padx=24)

        for num, title, body in [
            ("1", "Add your workflow folders",
             "Click  ＋ Add Location  and browse to the folder where\n"
             "ComfyUI saves your workflows. It's usually here:\n\n"
             "   [ComfyUI install]\\user\\default\\workflows\n\n"
             "You can add as many locations as you have installs."),
            ("2", "Scan them",
             "Check the locations you want to include, then click\n"
             "Scan Enabled. The app indexes every workflow JSON file\n"
             "it finds so searches are instant."),
            ("3", "Search",
             "Type what you're looking for in plain English —\n"
             "\"generate video from an image\" or \"face swap with LoRA\"\n"
             "— and the app finds matching workflows by node type.\n"
             "No need to remember filenames."),
        ]:
            row = tk.Frame(steps, bg=PNL); row.pack(fill="x", pady=(0, 12))
            tk.Label(row, text=num, bg=ACC, fg="#0a0a1a",
                     font=("Consolas", 11, "bold"),
                     width=2, relief="flat").pack(side="left", anchor="n", padx=(0, 12))
            col = tk.Frame(row, bg=PNL); col.pack(side="left", fill="x", expand=True)
            tk.Label(col, text=title, bg=PNL, fg=FG,
                     font=("Consolas", 10, "bold"), anchor="w").pack(fill="x")
            tk.Label(col, text=body, bg=PNL, fg=FG2,
                     font=("Consolas", 9), anchor="w", justify="left").pack(fill="x")

        tk.Label(win,
                 text="💡  AI search mode and Find in the Wild require a free\n"
                      "    Anthropic API key — Fast mode works without one.",
                 bg=BG, fg="#4a4a7a", font=("Consolas", 9), justify="left").pack(pady=(14, 0))

        ttk.Button(win, text="Got it — let's go!",
                   style="Accent.TButton",
                   command=win.destroy).pack(pady=(14, 20))

        win.bind("<Return>", lambda _: win.destroy())
        win.focus_set()

    def _load_config(self) -> list:
        try:
            with open(self.CONFIG_FILE, "r") as f:
                data = json.load(f)
            entries = data.get("directories", [])
            if entries:
                return entries
        except Exception:
            pass
        # First run: seed from DEFAULT_DIRS, enable only those that exist
        return [{"path": d, "enabled": os.path.isdir(d)} for d in self.DEFAULT_DIRS]

    def _save_config(self):
        try:
            os.makedirs(os.path.dirname(self.CONFIG_FILE), exist_ok=True)
            with open(self.CONFIG_FILE, "w") as f:
                json.dump({"directories": self.dir_entries}, f, indent=2)
        except Exception:
            pass

    def _build_styles(self):
        BG, PNL, ACC, DIM = "#111122", "#0c0c1e", "#6c72ff", "#3a3a66"
        FG, FG2 = "#d4d4f0", "#8888bb"
        M, MB = ("Consolas", 10), ("Consolas", 10, "bold")
        s = ttk.Style(self); s.theme_use("clam")
        s.configure("TFrame",        background=BG)
        s.configure("TLabel",        background=BG,  foreground=FG,  font=M)
        s.configure("Dim.TLabel",    background=BG,  foreground=FG2, font=("Consolas",9))
        s.configure("Head.TLabel",   background=BG,  foreground=ACC, font=("Consolas",14,"bold"))
        s.configure("TButton",       background=DIM, foreground=FG,  font=M, borderwidth=0)
        s.map("TButton",             background=[("active","#5050aa")])
        s.configure("Accent.TButton",background=ACC, foreground="#0a0a1a", font=MB, borderwidth=0)
        s.map("Accent.TButton",      background=[("active","#8a90ff")])
        s.configure("Treeview",      background=PNL, foreground=FG, fieldbackground=PNL, font=M, rowheight=26)
        s.configure("Treeview.Heading", background="#1a1a3e", foreground=ACC, font=MB)
        s.map("Treeview",            background=[("selected","#282860")])
        s.configure("TNotebook",     background=BG, tabmargins=[0,0,0,0])
        s.configure("TNotebook.Tab", background=PNL, foreground=FG2, font=M, padding=[10,4])
        s.map("TNotebook.Tab",       background=[("selected","#1a1a3e")], foreground=[("selected",ACC)])
        s.configure("TPanedwindow",  background=BG)
        s.configure("TSeparator",    background=DIM)

    def _build_ui(self):
        ACC = "#6c72ff"

        # Status var must exist before anything else calls self._status.set()
        self._status = tk.StringVar(value="Ready — scan a directory to begin.")

        # Title bar
        hdr = ttk.Frame(self); hdr.pack(fill="x", padx=16, pady=(14,4))
        ttk.Label(hdr, text="⚡ COMFYUI WORKFLOW FINDER", style="Head.TLabel").pack(side="left")
        ttk.Label(hdr, text="v2.0", style="Dim.TLabel").pack(side="left", padx=(8,0), pady=(4,0))
        ttk.Button(hdr, text="🌐  Find in Wild",
                   command=self._open_wild_search).pack(side="right", padx=(8,0))
        ttk.Label(hdr, text="Semantic search + graph preview",
                  style="Dim.TLabel").pack(side="right", pady=(4,0))
        ttk.Separator(self).pack(fill="x", padx=16, pady=(0,8))

        # Scan locations panel
        sf = tk.Frame(self, bg="#0c0c1e", padx=10, pady=8); sf.pack(fill="x", padx=16)

        hrow = tk.Frame(sf, bg="#0c0c1e"); hrow.pack(fill="x")
        tk.Label(hrow, text="SCAN LOCATIONS", bg="#0c0c1e", fg=ACC,
                 font=("Consolas",9,"bold")).pack(side="left")
        tk.Label(hrow, text="(check/uncheck to include in scan)", bg="#0c0c1e", fg="#4040aa",
                 font=("Consolas",8)).pack(side="left", padx=(8,0), pady=(1,0))

        # Scrollable checkbox-row container
        rows_outer = tk.Frame(sf, bg="#080818", pady=2); rows_outer.pack(fill="x", pady=(4,0))
        self._rows_canvas = tk.Canvas(rows_outer, bg="#080818", height=110,
                                       highlightthickness=0, bd=0)
        rows_sb = ttk.Scrollbar(rows_outer, orient="vertical", command=self._rows_canvas.yview)
        self._rows_canvas.configure(yscrollcommand=rows_sb.set)
        self._rows_canvas.pack(side="left", fill="both", expand=True)
        rows_sb.pack(side="right", fill="y")

        self._rows_frame = tk.Frame(self._rows_canvas, bg="#080818")
        self._rows_canvas_win = self._rows_canvas.create_window((0,0), window=self._rows_frame, anchor="nw")
        self._rows_frame.bind("<Configure>", self._on_rows_configure)
        self._rows_canvas.bind("<Configure>", self._on_canvas_configure)

        # Bottom buttons
        br = tk.Frame(sf, bg="#0c0c1e"); br.pack(fill="x", pady=(6,0))
        ttk.Button(br, text="＋ Add Location", command=self._add_dir).pack(side="left", padx=(0,6))
        ttk.Button(br, text="☑ Enable All",   command=self._enable_all).pack(side="left", padx=(0,4))
        ttk.Button(br, text="☐ Disable All",  command=self._disable_all).pack(side="left")
        ttk.Button(br, text="🔍 Scan Enabled", style="Accent.TButton",
                   command=self._start_scan).pack(side="right")
        self._scan_sv = tk.StringVar(value="Not scanned yet")
        tk.Label(br, textvariable=self._scan_sv, bg="#0c0c1e", fg="#5050aa",
                 font=("Consolas",9)).pack(side="right", padx=(0,12))

        # Build initial rows
        self._rebuild_dir_rows()

        # Query bar
        qf = tk.Frame(self, bg="#111122"); qf.pack(fill="x", padx=16, pady=(12,4))

        ql = tk.Frame(qf, bg="#111122"); ql.pack(fill="x")
        tk.Label(ql, text="SEARCH QUERY", bg="#111122", fg=ACC,
                 font=("Consolas",9,"bold")).pack(side="left")
        tk.Label(ql, text="or pick a suggestion →", bg="#111122", fg="#4040aa",
                 font=("Consolas",8)).pack(side="left", padx=(10,6), pady=(1,0))
        self._sugg_var = tk.StringVar(value="")
        self._sugg_cb  = ttk.Combobox(ql, textvariable=self._sugg_var,
                                       state="readonly", width=52,
                                       font=("Consolas",9))
        self._sugg_cb.pack(side="left")
        self._sugg_cb.bind("<<ComboboxSelected>>", self._on_suggestion)
        self._load_suggestions()

        # Row 1: semantic / node-content search
        qr = tk.Frame(qf, bg="#111122"); qr.pack(fill="x", pady=(4,0))
        self._query = tk.StringVar()
        self._qentry = tk.Entry(qr, textvariable=self._query, bg="#080818", fg="#e0e0ff",
                                insertbackground=ACC, font=("Consolas",13), relief="flat",
                                highlightthickness=1, highlightcolor=ACC, highlightbackground="#2d2d5e")
        self._qentry.pack(side="left", fill="x", expand=True, ipady=7, padx=(0,10))
        self._qentry.bind("<Return>", lambda _: self._start_search())
        self._mode = tk.StringVar(value="local")
        for lbl, val in [("⚡ Fast","local"),("🤖 AI (Claude)","claude")]:
            tk.Radiobutton(qr, text=lbl, variable=self._mode, value=val,
                           bg="#111122", fg="#a0a0cc", selectcolor="#111122",
                           activebackground="#111122", activeforeground="#d0d0ff",
                           font=("Consolas",10)).pack(side="left", padx=(0,4))
        ttk.Button(qr, text="Search", style="Accent.TButton",
                   command=self._start_search).pack(side="left", padx=(8,0))

        # Row 2: name / filename filter (instant, no scan needed)
        nr = tk.Frame(qf, bg="#111122"); nr.pack(fill="x", pady=(6,0))
        tk.Label(nr, text="NAME FILTER", bg="#111122", fg=ACC,
                 font=("Consolas",9,"bold")).pack(side="left")
        tk.Label(nr, text="partial match, case-insensitive, instant",
                 bg="#111122", fg="#4040aa", font=("Consolas",8)).pack(side="left", padx=(8,0), pady=(1,0))

        nf = tk.Frame(qf, bg="#111122"); nf.pack(fill="x", pady=(3,0))
        self._name_filter = tk.StringVar()
        ne = tk.Entry(nf, textvariable=self._name_filter, bg="#080818", fg="#e0e0ff",
                      insertbackground=ACC, font=("Consolas",13), relief="flat",
                      highlightthickness=1, highlightcolor="#44aa66", highlightbackground="#2d2d5e")
        ne.pack(side="left", fill="x", expand=True, ipady=7, padx=(0,10))
        ne.bind("<Return>",  lambda _: self._name_search())
        ne.bind("<KeyRelease>", lambda _: self._name_search_live())

        # Quick prefix dropdown — loaded from JSON
        tk.Label(nf, text="Quick:", bg="#111122", fg="#4040aa",
                 font=("Consolas",9)).pack(side="left")
        self._prefix_var = tk.StringVar()
        self._prefix_cb  = ttk.Combobox(nf, textvariable=self._prefix_var,
                                         state="readonly", width=16,
                                         font=("Consolas",10))
        self._prefix_cb.pack(side="left", padx=(4,8))
        self._prefix_cb.bind("<<ComboboxSelected>>", self._on_prefix_select)
        self._load_prefixes()

        ttk.Button(nf, text="Clear", command=self._name_clear
                   ).pack(side="left", padx=(4,0))

        # Paned window
        paned = tk.PanedWindow(self, orient="vertical", bg="#111122",
                               sashwidth=6, sashpad=2, relief="flat")
        paned.pack(fill="both", expand=True, padx=16, pady=8)

        # Results tree
        tf = tk.Frame(paned, bg="#111122")
        cols = ("score","filename","nodes","created","modified","matched","path")
        self._tree = ttk.Treeview(tf, columns=cols, show="headings", selectmode="browse")
        self._sort_col = "score"
        self._sort_asc = False   # start descending (best score first)
        for col, head, w, anch in [
            ("score",    "Score",        70,  "center"),
            ("filename", "Workflow",     260, "w"),
            ("nodes",    "# Nodes",       72, "center"),
            ("created",  "Created",      132, "center"),
            ("modified", "Modified",     132, "center"),
            ("matched",  "Matched",      200, "w"),
            ("path",     "Path",         380, "w"),
        ]:
            self._tree.heading(col, text=head,
                               command=lambda c=col: self._sort_by(c))
            self._tree.column(col, width=w, anchor=anch, minwidth=40)
        vsb = ttk.Scrollbar(tf, orient="vertical",   command=self._tree.yview)
        hsb = ttk.Scrollbar(tf, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns"); hsb.grid(row=1, column=0, sticky="ew")
        tf.rowconfigure(0, weight=1); tf.columnconfigure(0, weight=1)
        self._tree.bind("<<TreeviewSelect>>", self._on_select)
        self._tree.bind("<Double-1>", self._open_folder)
        paned.add(tf, minsize=180)

        # Detail panel with notebook
        nb_outer = tk.Frame(paned, bg="#0c0c1e")
        nb_outer.rowconfigure(1, weight=1); nb_outer.columnconfigure(0, weight=1)

        nb_btn = tk.Frame(nb_outer, bg="#0c0c1e"); nb_btn.grid(row=0, column=0, sticky="ew", padx=8, pady=(6,2))
        tk.Label(nb_btn, text="WORKFLOW DETAILS", bg="#0c0c1e", fg=ACC,
                 font=("Consolas",9,"bold")).pack(side="left")
        ttk.Button(nb_btn, text="📁 Open Folder", command=self._open_folder).pack(side="right", padx=(4,0))
        ttk.Button(nb_btn, text="📋 Copy Path",   command=self._copy_path).pack(side="right")
        ttk.Button(nb_btn, text="⛶ Fullscreen",command=self._open_graph_fullscreen).pack(side="right", padx=(0,4))
        ttk.Button(nb_btn, text="⊞ Fit Graph [F]",command=self._fit_graph).pack(side="right", padx=(0,4))

        nb = ttk.Notebook(nb_outer); nb.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0,4))
        self._nb = nb

        # Tab 1: text
        tt = tk.Frame(nb, bg="#0c0c1e")
        self._detail = tk.Text(tt, bg="#0c0c1e", fg="#b8b8e0", font=("Consolas",9),
                               relief="flat", wrap="word", state="disabled", highlightthickness=0)
        tsb = ttk.Scrollbar(tt, command=self._detail.yview)
        self._detail.configure(yscrollcommand=tsb.set)
        self._detail.pack(side="left", fill="both", expand=True, padx=(8,0), pady=6)
        tsb.pack(side="right", fill="y", pady=6)
        nb.add(tt, text="  📄 Details  ")

        # Tab 2: graph
        tg = tk.Frame(nb, bg="#080818")
        tg.rowconfigure(0, weight=1); tg.columnconfigure(0, weight=1)
        self._gc = GraphCanvas(tg)
        self._gc.grid(row=0, column=0, sticky="nsew")
        self._gc.show_message("Select a workflow above to preview its graph.",
                              "Requires UI-exported format with node positions.")
        nb.add(tg, text="  🔗 Graph  ")

        paned.add(nb_outer, minsize=200)

        # Status bar
        tk.Label(self, textvariable=self._status, bg="#080818", fg="#404080",
                 font=("Consolas",9), anchor="w").pack(fill="x", side="bottom", padx=16, pady=(0,6))

    # ── Directory rows (scrollable toggleable list) ─────────────────────

    def _on_rows_configure(self, _event=None):
        self._rows_canvas.configure(scrollregion=self._rows_canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self._rows_canvas.itemconfig(self._rows_canvas_win, width=event.width)

    def _rebuild_dir_rows(self):
        """Destroy and recreate all directory checkbox rows."""
        for w in self._rows_frame.winfo_children():
            w.destroy()

        for idx, entry in enumerate(self.dir_entries):
            self._add_dir_row(idx, entry)

    def _add_dir_row(self, idx: int, entry: dict):
        row = tk.Frame(self._rows_frame, bg="#080818"); row.pack(fill="x", pady=1)

        enabled = entry["enabled"]
        exists  = os.path.isdir(entry["path"])

        # Visual toggle button — shows a real-looking checkbox using Unicode + color
        chk_btn = tk.Button(
            row,
            text=" ☑ " if enabled else " ☐ ",
            font=("Segoe UI", 11),
            fg="#66cc88" if enabled else "#505070",
            bg="#080818", activebackground="#0d0d22",
            activeforeground="#88ffaa" if enabled else "#7070aa",
            relief="flat", bd=0, padx=2, pady=0,
            cursor="hand2",
        )
        chk_btn.pack(side="left", padx=(4, 0))

        path_color = ("#9090cc" if enabled else "#404060") if exists else "#6a3a3a"
        lbl = tk.Label(row, text=entry["path"], bg="#080818", fg=path_color,
                       font=("Consolas", 9), anchor="w", cursor="hand2")
        lbl.pack(side="left", fill="x", expand=True, padx=(4, 8))

        if not exists:
            tk.Label(row, text="[not found]", bg="#080818", fg="#5a2a2a",
                     font=("Consolas", 8)).pack(side="left", padx=(0, 4))

        def on_toggle(i=idx, btn=chk_btn, label=lbl):
            new_val = not self.dir_entries[i]["enabled"]
            self.dir_entries[i]["enabled"] = new_val
            self._save_config()
            # Update button and label visuals immediately
            btn.configure(
                text=" ☑ " if new_val else " ☐ ",
                fg="#66cc88" if new_val else "#505070",
                activeforeground="#88ffaa" if new_val else "#7070aa",
            )
            ex = os.path.isdir(self.dir_entries[i]["path"])
            label.configure(fg=("#9090cc" if new_val else "#404060") if ex else "#6a3a3a")
            self._toggle_dir_dynamic(self.dir_entries[i]["path"], new_val)

        chk_btn.configure(command=on_toggle)
        lbl.bind("<Button-1>", lambda _: on_toggle())   # click label to toggle too

        def remove(i=idx):
            self.dir_entries.pop(i)
            self._save_config()
            self._rebuild_dir_rows()

        tk.Button(row, text="×", command=remove,
                  bg="#1a0808", fg="#884444", font=("Consolas", 9, "bold"),
                  relief="flat", bd=0, padx=6, pady=0,
                  activebackground="#2a1010", activeforeground="#ff8888",
                  cursor="hand2").pack(side="right", padx=(0, 4))

        # Store var reference to keep it alive

    def _update_row_color(self, idx: int):
        """Refresh the label color of a single row after toggle."""
        rows = [w for w in self._rows_frame.winfo_children()]
        if idx >= len(rows):
            return
        row = rows[idx]
        entry = self.dir_entries[idx]
        exists = os.path.isdir(entry["path"])
        color = "#9090cc" if entry["enabled"] else "#404060"
        if not exists: color = "#6a3a3a"
        for child in row.winfo_children():
            if isinstance(child, tk.Label) and entry["path"] in (child.cget("text") or ""):
                child.configure(fg=color)

    # ── Suggestions dropdown ─────────────────────────────────────────────

    QUERIES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "workflow_finder_queries.json")

    DEFAULT_QUERIES = {
        "Video Generation": [
            "generate video from a text prompt",
            "generate video from an image",
            "image to video with motion",
            "LTX video generation",
            "Wan video generation",
            "Hunyuan video generation",
            "extend or continue a video clip",
            "video generation with audio",
            "text to video with camera movement",
            "generate a short looping video",
        ],
        "Video Analysis": [
            "load a video and generate a caption or description",
            "extract frames from a video",
            "analyze video content with a vision model",
            "generate a prompt from a video frame",
            "describe what is happening in a video",
        ],
        "Image Generation": [
            "text to image with Flux",
            "text to image with SDXL",
            "text to image with SD 1.5",
            "high resolution image generation with upscale",
            "generate image with a reference style",
            "photorealistic portrait generation",
            "fantasy or concept art generation",
            "product photography on clean background",
        ],
        "Image Editing": [
            "image to image transformation",
            "inpainting to fill or replace an area",
            "outpainting to expand image borders",
            "background removal or replacement",
            "object removal from image",
            "image upscaling and enhancement",
            "color correction or style transfer",
            "sharpen or restore a blurry image",
        ],
        "ControlNet": [
            "image generation with pose control",
            "image generation with depth map control",
            "image generation with canny edge control",
            "image generation with lineart control",
            "tile upscale with ControlNet",
            "multi-controlnet combining pose and depth",
        ],
        "Face": [
            "face swap",
            "face identity consistency across images",
            "portrait with face reference using PuLID",
            "portrait with face reference using InstantID",
            "face restoration and enhancement",
            "multiple face swaps in one image",
        ],
        "Captioning and Vision LLM": [
            "caption an image with Florence2",
            "tag an image with WD14 tagger",
            "describe image contents with a vision model",
            "generate a prompt from an existing image",
            "reverse prompt engineering from image",
            "analyze image with QwenVL",
            "batch caption multiple images",
            "interrogate image with CLIP",
        ],
        "LoRA and Models": [
            "use a single LoRA for style",
            "stack multiple LoRAs together",
            "character consistency using a LoRA",
            "apply a concept LoRA",
            "combine checkpoint with multiple LoRAs",
            "use a detail or texture LoRA",
        ],
        "IP-Adapter and Reference": [
            "style transfer with IP-Adapter",
            "use a reference image for style",
            "face identity with IP-Adapter FaceID",
            "combine IP-Adapter with ControlNet",
            "character reference image consistency",
        ],
        "Segmentation and Masking": [
            "segment and mask an object with SAM",
            "detect and isolate object with GroundingDINO",
            "remove background with RMBG",
            "create mask from text description",
            "video object tracking and masking",
        ],
        "Upscaling": [
            "upscale image with ESRGAN",
            "ultimate tile upscale for large images",
            "upscale and enhance with detail",
            "4x upscale with face restoration",
            "video upscaling",
        ],
        "Batch and Automation": [
            "batch process multiple images from a folder",
            "batch generate with prompts from a text file",
            "automated caption and save workflow",
            "iterate through LoRAs on same prompt",
        ],
        "Audio": [
            "generate video with synchronized audio",
            "load audio and combine with video",
            "add music or sound to generated video",
        ],
        "Qwen Image Edit": [
            "edit an image using a text instruction",
            "change object color with Qwen image edit",
            "rotate or repose object in image",
            "add or remove element from image",
            "change background of product image",
            "multiple angle views of same object",
        ],
        "Flux Specific": [
            "Flux text to image",
            "Flux with LoRA",
            "Flux image to image",
            "Flux inpainting",
            "Flux with ControlNet",
            "Flux fill outpainting",
        ],
    }

    def _load_suggestions(self):
        """Load suggestions from JSON (auto-creates it from defaults if missing)."""
        # Try to load from file; create it from defaults if absent
        data = None
        try:
            with open(self.QUERIES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            # First run — write defaults to disk so user can edit them
            try:
                with open(self.QUERIES_FILE, "w", encoding="utf-8") as f:
                    json.dump({"_comment": "Edit freely. Restart app to reload.",
                               "categories": self.DEFAULT_QUERIES}, f, indent=2)
            except Exception:
                pass
        except Exception as e:
            self._status.set(f"Could not load suggestions: {e}")

        categories = (data or {}).get("categories", None) or self.DEFAULT_QUERIES

        entries = []
        for category, phrases in categories.items():
            for phrase in phrases:
                entries.append(f"[{category}]  {phrase}")

        if entries:
            self._sugg_cb["values"] = entries
            self._sugg_cb.set("— pick a suggested search —")

    PREFIXES_FILE    = os.path.join(os.path.dirname(os.path.abspath(__file__)), "workflow_finder_prefixes.json")
    DEFAULT_PREFIXES = ["Wow_", "Master_", "Test_", "WIP_"]

    def _load_prefixes(self):
        """Load name-filter quick picks from JSON, auto-creating it on first run."""
        prefixes = None
        try:
            with open(self.PREFIXES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            prefixes = data.get("prefixes", None)
        except FileNotFoundError:
            try:
                with open(self.PREFIXES_FILE, "w", encoding="utf-8") as f:
                    json.dump({
                        "_comment": "Quick-filter dropdown for the Name Filter bar. Edit freely, restart to reload.",
                        "prefixes": self.DEFAULT_PREFIXES
                    }, f, indent=2)
            except Exception:
                pass
        except Exception:
            pass

        values = prefixes or self.DEFAULT_PREFIXES
        self._prefix_cb["values"] = values
        self._prefix_cb.set("— pick —")

    def _on_prefix_select(self, _event=None):
        prefix = self._prefix_var.get()
        if prefix and prefix != "— pick —":
            self._name_filter.set(prefix)
            self._name_search()
        self.after(100, lambda: self._prefix_cb.set("— pick —"))

    def _on_suggestion(self, _event=None):
        """Fill the query box when a suggestion is selected."""
        raw = self._sugg_var.get()
        # Strip the [Category]  prefix
        if "]  " in raw:
            phrase = raw.split("]  ", 1)[1]
        else:
            phrase = raw
        self._query.set(phrase)
        self._qentry.focus_set()
        self._qentry.icursor("end")
        # Reset dropdown label so it's ready for next pick
        self.after(100, lambda: self._sugg_cb.set("— pick a suggested search —"))

    def _add_dir(self):
        d = filedialog.askdirectory(title="Add Workflow Location")
        if not d: return
        # Normalise to backslashes on Windows
        d = os.path.normpath(d)
        if any(e["path"] == d for e in self.dir_entries):
            self._status.set(f"Already in the list: {d}  2190 scroll the location list to find it")
            return
        self.dir_entries.append({"path": d, "enabled": True})
        self._save_config()
        self._rebuild_dir_rows()
        # Scroll to bottom
        self._rows_canvas.update_idletasks()
        self._rows_canvas.yview_moveto(1.0)

    def _enable_all(self):
        for e in self.dir_entries: e["enabled"] = True
        self._save_config(); self._rebuild_dir_rows()

    def _disable_all(self):
        for e in self.dir_entries: e["enabled"] = False
        self._save_config(); self._rebuild_dir_rows()

    # ── Scanning ────────────────────────────────────────────────────────

    def _start_scan(self):
        enabled = [e["path"] for e in self.dir_entries if e["enabled"]]
        if not enabled:
            messagebox.showwarning("Nothing enabled",
                                   "Check at least one location before scanning."); return
        self.fingerprints = []
        self._fp_by_dir   = {}   # clear stale entries from disabled locations
        self._scan_sv.set("Scanning…"); self._status.set("Scanning workflow locations…")
        threading.Thread(target=self._scan_worker, args=(enabled,), daemon=True).start()

    def _scan_worker(self, dirs: list):
        total = 0
        for root_dir in dirs:
            if not os.path.isdir(root_dir): continue
            dir_fps = []
            for dp, _, files in os.walk(root_dir):
                for fn in files:
                    if not fn.endswith(".json"): continue
                    total += 1
                    fp = extract_workflow_fingerprint(os.path.join(dp, fn))
                    if fp:
                        fp["source_dir"] = root_dir
                        dir_fps.append(fp)
                    if total % 25 == 0:
                        self.after(0, self._scan_sv.set, f"Scanning… {total} files")
            self._fp_by_dir[root_dir] = dir_fps
        self._rebuild_fingerprints()
        fps = self.fingerprints
        msg = f"✓ {len(fps):,} workflows  ({total:,} files)"
        self.after(0, lambda: (
            self._scan_sv.set(msg),
            self._status.set(f"Scan complete — {len(fps):,} workflows from {len(dirs)} location(s).")
        ))

    def _scan_one_dir(self, dir_path: str):
        """Scan a single newly-enabled directory and merge into fingerprints."""
        fps, total = [], 0
        if os.path.isdir(dir_path):
            for dp, _, files in os.walk(dir_path):
                for fn in files:
                    if not fn.endswith(".json"): continue
                    total += 1
                    fp = extract_workflow_fingerprint(os.path.join(dp, fn))
                    if fp:
                        fp["source_dir"] = dir_path
                        fps.append(fp)
                    if total % 25 == 0:
                        self.after(0, self._scan_sv.set, f"Scanning… {total} files")
        self._fp_by_dir[dir_path] = fps
        self._rebuild_fingerprints()
        count = len(self.fingerprints)
        if self._pb: self.after(0, self._pb.stop)
        if self._pb: self.after(0, self._pb.pack_forget)
        self.after(0, self._scan_sv.set,
                   f"✓ {count:,} workflows  (+{len(fps)} from new location)")
        self.after(0, self._rerun_last_search)

    def _rebuild_fingerprints(self):
        """Flatten _fp_by_dir into self.fingerprints, deduplicating by path."""
        seen, fps = set(), []
        for dir_fps in self._fp_by_dir.values():
            for fp in dir_fps:
                if fp["path"] not in seen:
                    seen.add(fp["path"])
                    fps.append(fp)
        self.fingerprints = fps

    def _toggle_dir_dynamic(self, dir_path: str, enabled: bool):
        """Called when a checkbox is toggled — add or remove that dir live."""
        if not enabled:
            self._fp_by_dir.pop(dir_path, None)
            self._rebuild_fingerprints()
            count = len(self.fingerprints)
            self._scan_sv.set(f"✓ {count:,} workflows  (location unchecked)")
            self._rerun_last_search()
        else:
            if not os.path.isdir(dir_path):
                self._status.set(f"Directory not found: {dir_path}")
                return
            if self._pb:
                self._pb.pack(fill="x", padx=16, pady=(4,0))
                self._pb.start(12)
            self._scan_sv.set("Scanning new location…")
            threading.Thread(target=self._scan_one_dir,
                             args=(dir_path,), daemon=True).start()

    def _rerun_last_search(self):
        """Re-run the last search query against the current fingerprint pool."""
        name_pat = self._name_filter.get().strip() if hasattr(self, "_name_filter") else ""
        if name_pat:
            self.after(0, self._name_search)
        elif self._last_q:
            self._status.set(f"Re-running search…")
            threading.Thread(target=self._search_worker,
                             args=(self._last_q, self._last_mode),
                             daemon=True).start()
        else:
            for i in self._tree.get_children():
                self._tree.delete(i)

    # ── Search ───────────────────────────────────────────────────────────

    # ── Name filter search ──────────────────────────────────────────────

    def _name_search_live(self):
        """Trigger name search after a short debounce delay."""
        if hasattr(self, "_name_after"):
            self.after_cancel(self._name_after)
        self._name_after = self.after(180, self._name_search)

    def _name_search(self):
        """Filter results tree instantly by filename substring."""
        pattern = self._name_filter.get().strip().lower()
        if not pattern:
            # If name filter cleared and there's a pending node search result, restore it
            if self.results:
                self._populate(self.results,
                               self._query.get().strip(),
                               self._mode.get())
            else:
                for i in self._tree.get_children():
                    self._tree.delete(i)
                self._status.set("Name filter cleared.")
            return

        if not self.fingerprints:
            messagebox.showinfo("Not Scanned", "Please scan directories first.")
            return

        # Match against filename (no node scoring needed)
        matches = [fp for fp in self.fingerprints
                   if pattern in fp["filename"].lower()]
        matches.sort(key=lambda fp: fp["filename"].lower())

        for i in self._tree.get_children():
            self._tree.delete(i)
        for fp in matches:
            self._tree.insert("", "end", values=(
                "—",
                fp["filename"],
                fp["node_count"],
                self._fmt_ts(fp.get("created",  0)),
                self._fmt_ts(fp.get("modified", 0)),
                "",
                fp["path"],
            ))
        self._status.set(
            f"[name]  {len(matches):,} workflow(s) matching '{pattern}'")

    def _name_clear(self):
        self._name_filter.set("")
        self._name_search()

    def _start_search(self):
        q = self._query.get().strip()
        if not q: return
        if not self.fingerprints:
            messagebox.showinfo("Not Scanned", "Please scan directories first."); return
        for i in self._tree.get_children(): self._tree.delete(i)
        self._status.set(f"Searching: \"{q}\"…")
        mode = self._mode.get()
        if mode == "claude" and not ANTHROPIC_AVAILABLE:
            self._status.set("anthropic package not found on this Python — falling back to Fast mode. Run: pip install anthropic")
            mode = "local"
        self._last_q    = q
        self._last_mode = mode
        threading.Thread(target=self._search_worker, args=(q, mode), daemon=True).start()

    def _search_worker(self, q, mode):
        res = search_claude(self.fingerprints, q) if mode=="claude" \
              else search_local(self.fingerprints, q)
        self.results = res
        self.after(0, self._populate, res, q, mode)

    @staticmethod
    def _fmt_ts(ts: float) -> str:
        """Format a Unix timestamp as MM/DD/YY HH:MM, or blank if zero."""
        if not ts:
            return ""
        import datetime
        return datetime.datetime.fromtimestamp(ts).strftime("%m/%d/%y  %H:%M")

    def _populate(self, res, q, mode):
        for i in self._tree.get_children(): self._tree.delete(i)
        for fp in res:
            self._tree.insert("", "end", values=(
                f"{fp.get('score',0):.1f}",
                fp["filename"],
                fp["node_count"],
                self._fmt_ts(fp.get("created",  0)),
                self._fmt_ts(fp.get("modified", 0)),
                ", ".join(fp.get("matched_terms",[])),
                fp["path"],
            ))
        m = "AI" if mode=="claude" else "fast"
        self._status.set(f"[{m}]  {len(res):,} result(s) for: \"{q}\"")

    # ── Selection ────────────────────────────────────────────────────────

    # ── Column sorting ───────────────────────────────────────────────────

    # Column index map for extracting the right value
    _COL_IDX = {"score":0,"filename":1,"nodes":2,"created":3,"modified":4,"matched":5,"path":6}
    # Columns that should sort numerically
    _NUMERIC_COLS = {"score", "nodes"}

    def _sort_by(self, col: str):
        """Sort tree by column; clicking the same column reverses direction."""
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True

        idx = self._COL_IDX.get(col, 0)
        rows = [(self._tree.set(k, col), k) for k in self._tree.get_children("")]

        if col in self._NUMERIC_COLS:
            def key(x):
                try: return float(x[0].replace(",","").replace("—","0") or 0)
                except ValueError: return 0.0
        else:
            def key(x): return x[0].lower()

        rows.sort(key=key, reverse=not self._sort_asc)
        for i, (_, k) in enumerate(rows):
            self._tree.move(k, "", i)

        # Update header labels to show sort direction arrow
        arrows = {"score":"Score","filename":"Workflow","nodes":"# Nodes",
                  "created":"Created","modified":"Modified","matched":"Matched","path":"Path"}
        for c, base in arrows.items():
            if c == col:
                arrow = " ▲" if self._sort_asc else " ▼"
                self._tree.heading(c, text=base + arrow)
            else:
                self._tree.heading(c, text=base)

    def _get_sel(self) -> Optional[dict]:
        sel = self._tree.selection()
        if not sel: return None
        vals = self._tree.item(sel[0])["values"]
        if not vals: return None
        path = str(vals[6])
        for fp in self.results:
            if fp["path"] == path: return fp
        return None

    def _on_select(self, _=None):
        fp = self._get_sel()
        if not fp: return
        # Fill details tab
        lines = [
            f"FILE   : {fp['filename']}",
            f"PATH   : {fp['path']}",
            f"NODES  : {fp['node_count']} total", "",
            "NODE TYPES  (→ capability)", "─"*72,
        ]
        for nt in fp["nodes"]:
            cap = NODE_CAPS.get(nt,"")
            if cap:
                d = cap[:55]+"…" if len(cap)>55 else cap
                lines.append(f"  {nt:<44} →  {d}")
            else:
                lines.append(f"  {nt}")
        if fp.get("titles"):
            lines += ["","CUSTOM TITLES","─"*72] + [f"  {t}" for t in fp["titles"]]
        if fp.get("text_snippets"):
            lines += ["","TEXT SNIPPETS","─"*72] + [f"  {s[:120]}" for s in fp["text_snippets"]]
        self._detail.configure(state="normal")
        self._detail.delete("1.0","end")
        self._detail.insert("end","\n".join(lines))
        self._detail.configure(state="disabled")
        # Load graph (switches to graph tab automatically on first selection)
        self._gc.load_workflow(fp["path"])

    # ── Actions ──────────────────────────────────────────────────────────

    def _open_folder(self, _=None):
        fp = self._get_sel()
        if fp: subprocess.Popen(f'explorer /select,"{fp["path"]}"')

    def _copy_path(self):
        fp = self._get_sel()
        if fp:
            self.clipboard_clear(); self.clipboard_append(fp["path"])
            self._status.set(f"Copied: {fp['path']}")

    def _fit_graph(self):
        self._gc.fit()
        self._nb.select(1)

    def _open_graph_fullscreen(self):
        fp = self._get_sel()
        if not fp:
            self._status.set("Select a workflow first.")
            return

        # ── Build the popup ──────────────────────────────────────────────
        popup = tk.Toplevel(self)
        popup.title(f"Graph — {fp['filename']}")
        popup.configure(bg="#080818")
        popup.state("zoomed")   # maximized on Windows

        ACC = "#6c72ff"

        # Header bar
        hdr = tk.Frame(popup, bg="#0c0c1e"); hdr.pack(fill="x")

        tk.Label(hdr, text=fp["filename"], bg="#0c0c1e", fg=ACC,
                 font=("Consolas", 12, "bold")).pack(side="left", padx=(12, 0), pady=6)
        tk.Label(hdr, text=fp["path"], bg="#0c0c1e", fg="#4040aa",
                 font=("Consolas", 9)).pack(side="left", padx=(10, 0), pady=(8, 0))

        # Buttons (right side)
        btn_f = tk.Frame(hdr, bg="#0c0c1e"); btn_f.pack(side="right", padx=8, pady=4)

        def fit(): gc.fit()
        def close(): popup.destroy()

        ttk.Button(btn_f, text="⊞ Fit [F]", command=fit).pack(side="left", padx=(0, 6))
        ttk.Button(btn_f, text="✕ Close",   command=close,
                   style="Accent.TButton").pack(side="left")

        # Colour-coded legend
        legend_items = [
            ("#0b3d36", "Video I/O"),
            ("#2d0d55", "Models"),
            ("#5c2800", "Samplers"),
            ("#0d3d0d", "CLIP/Text"),
            ("#3d2e00", "Caption/LLM"),
            ("#003344", "VAE"),
            ("#3d003d", "ControlNet"),
            ("#3d1500", "SAM/Seg"),
            ("#1a1a35", "Utility"),
        ]
        leg = tk.Frame(hdr, bg="#0c0c1e"); leg.pack(side="right", padx=(0, 16), pady=4)
        for color, label in legend_items:
            item = tk.Frame(leg, bg="#0c0c1e"); item.pack(side="left", padx=4)
            tk.Label(item, text="  ", bg=color, width=2,
                     relief="flat").pack(side="left")
            tk.Label(item, text=label, bg="#0c0c1e", fg="#6060aa",
                     font=("Consolas", 8)).pack(side="left", padx=(2, 0))

        ttk.Separator(popup, orient="horizontal").pack(fill="x")

        # Full-size graph canvas
        gc = GraphCanvas(popup)
        gc.pack(fill="both", expand=True)
        gc.load_workflow(fp["path"])

        # Keyboard shortcuts
        popup.bind("<f>",      lambda _: gc.fit())
        popup.bind("<F>",      lambda _: gc.fit())
        popup.bind("<Escape>", lambda _: popup.destroy())
        popup.focus_set()


    def _open_wild_search(self):
        # Try a fresh import in case module-level check ran under wrong Python
        global ANTHROPIC_AVAILABLE, anthropic
        if not ANTHROPIC_AVAILABLE:
            try:
                import anthropic as _a
                anthropic = _a
                ANTHROPIC_AVAILABLE = True
            except ImportError:
                pass

        if not ANTHROPIC_AVAILABLE:
            import sys
            messagebox.showwarning(
                "anthropic not found",
                f"Wild Search needs the anthropic package, but it is not\n"
                f"installed for the Python this app is running under.\n\n"
                f"Python:   {sys.executable}\n"
                f"Version:  {sys.version[:6]}\n\n"
                f"Fix — run this exact command in PowerShell:\n\n"
                f'  & "{sys.executable}" -m pip install anthropic\n\n'
                f"Then restart the app.")
            return
        try:
            WildSearchWindow(self)
        except Exception as e:
            messagebox.showerror("Wild Search Error", str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Wild Search Window
# ─────────────────────────────────────────────────────────────────────────────

class WildSearchWindow(tk.Toplevel):
    """
    Standalone window that uses the Claude API + web_search tool to find
    ComfyUI workflows across YouTube, CivitAI, GitHub, Reddit, etc.
    """

    SOURCES_FILE = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "workflow_finder_sources.json")

    DEFAULT_SOURCES = [
        {"name": "YouTube",              "enabled": True},
        {"name": "CivitAI",              "enabled": True},
        {"name": "GitHub",               "enabled": True},
        {"name": "Reddit (r/comfyui)",   "enabled": True},
        {"name": "ComfyHub",             "enabled": True},
        {"name": "Hugging Face",         "enabled": False},
        {"name": "ComfyUI Forums",       "enabled": False},
        {"name": "OpenArt",              "enabled": False},
    ]

    def __init__(self, parent):
        super().__init__(parent)
        self.title("🌐  Find Workflows in the Wild")
        self.configure(bg=BG)
        self.state("zoomed")
        self.minsize(900, 600)

        self._sources   = self._load_sources()
        self._src_vars  = []   # BooleanVar per source row
        self._results   = []
        self._searching = False

        self._build_ui()
        self.focus_set()
        self.bind("<Escape>", lambda _: self.destroy())

    # ── Config ───────────────────────────────────────────────────────────

    def _load_sources(self) -> list[dict]:
        try:
            with open(self.SOURCES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("sources"):
                return data["sources"]
        except FileNotFoundError:
            pass
        except Exception:
            pass
        # Write defaults on first run
        try:
            with open(self.SOURCES_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "_comment": "Wild Search sources. Edit freely, restart to reload.",
                    "sources": self.DEFAULT_SOURCES
                }, f, indent=2)
        except Exception:
            pass
        return list(self.DEFAULT_SOURCES)

    def _save_sources(self):
        for i, var in enumerate(self._src_vars):
            self._sources[i]["enabled"] = var.get()
        try:
            with open(self.SOURCES_FILE, "w", encoding="utf-8") as f:
                json.dump({"_comment": "Wild Search sources.",
                           "sources": self._sources}, f, indent=2)
        except Exception:
            pass

    # ── UI ───────────────────────────────────────────────────────────────

    def _build_ui(self):
        ACC = "#6c72ff"

        # Title
        hdr = ttk.Frame(self); hdr.pack(fill="x", padx=16, pady=(14,4))
        ttk.Label(hdr, text="🌐  FIND WORKFLOWS IN THE WILD",
                  style="Head.TLabel").pack(side="left")
        ttk.Label(hdr, text="Claude searches the internet — results include download links where found",
                  style="Dim.TLabel").pack(side="left", padx=(12,0), pady=(4,0))
        ttk.Button(hdr, text="✕ Close", style="Accent.TButton",
                   command=self.destroy).pack(side="right")
        ttk.Separator(self).pack(fill="x", padx=16, pady=(0,8))

        # Sources panel
        sp = tk.Frame(self, bg=PNL, padx=10, pady=8); sp.pack(fill="x", padx=16)
        tk.Label(sp, text="SEARCH SOURCES", bg=PNL, fg=ACC,
                 font=("Consolas",9,"bold")).pack(anchor="w")
        src_row = tk.Frame(sp, bg=PNL); src_row.pack(fill="x", pady=(4,0))

        self._src_vars = []
        for src in self._sources:
            var = tk.BooleanVar(value=src["enabled"])
            self._src_vars.append(var)
            cb = tk.Checkbutton(src_row, text=src["name"], variable=var,
                                bg=PNL, fg=FG, selectcolor=PNL,
                                activebackground=PNL, activeforeground=ACC,
                                font=("Consolas",10),
                                command=self._save_sources)
            cb.pack(side="left", padx=(0,16))

        # Query bar
        qf = tk.Frame(self, bg=BG); qf.pack(fill="x", padx=16, pady=(10,4))
        tk.Label(qf, text="QUERY", bg=BG, fg=ACC,
                 font=("Consolas",9,"bold")).pack(anchor="w")
        qr = tk.Frame(qf, bg=BG); qr.pack(fill="x")
        self._query = tk.StringVar()
        qe = tk.Entry(qr, textvariable=self._query, bg=PNL2, fg="#e0e0ff",
                      insertbackground=ACC, font=("Consolas",13), relief="flat",
                      highlightthickness=1, highlightcolor=ACC,
                      highlightbackground=DIM)
        qe.pack(side="left", fill="x", expand=True, ipady=7, padx=(0,10))
        qe.bind("<Return>", lambda _: self._start_search())
        qe.focus_set()

        self._search_btn = ttk.Button(qr, text="🌐  Search Wild",
                                       style="Accent.TButton",
                                       command=self._start_search)
        self._search_btn.pack(side="left")

        # ── Searching indicator (hidden until search starts) ─────────────
        self._search_indicator = tk.Frame(self, bg="#0a0a20")
        # Don't pack yet — shown only during search

        ind_inner = tk.Frame(self._search_indicator, bg="#0a0a20")
        ind_inner.pack(fill="x", padx=16, pady=(6,4))

        self._srch_icon = tk.Label(ind_inner, text="🔍", bg="#0a0a20",
                                   font=("Segoe UI", 14))
        self._srch_icon.pack(side="left", padx=(0,10))

        srch_text_col = tk.Frame(ind_inner, bg="#0a0a20")
        srch_text_col.pack(side="left", fill="x", expand=True)

        self._srch_main = tk.StringVar(value="Searching…")
        tk.Label(srch_text_col, textvariable=self._srch_main,
                 bg="#0a0a20", fg=ACC, font=("Consolas",10,"bold"),
                 anchor="w").pack(fill="x")

        self._srch_sub = tk.StringVar(value="")
        tk.Label(srch_text_col, textvariable=self._srch_sub,
                 bg="#0a0a20", fg=FG2, font=("Consolas",9),
                 anchor="w").pack(fill="x")

        self._srch_count = tk.StringVar(value="")
        tk.Label(ind_inner, textvariable=self._srch_count,
                 bg="#0a0a20", fg="#4a4a8a", font=("Consolas",9)).pack(side="right")

        self._pb = ttk.Progressbar(self._search_indicator, mode="indeterminate",
                                   style="Horizontal.TProgressbar", length=100)
        self._pb.pack(fill="x", padx=16, pady=(0,6))

        self._anim_after = None   # handle for dot animation

        # Paned: results tree (top) + detail panel (bottom)
        self._paned = tk.PanedWindow(self, orient="vertical", bg=BG,
                               sashwidth=6, relief="flat")
        self._paned.pack(fill="both", expand=True, padx=16, pady=8)
        paned = self._paned

        # Results treeview
        tf = tk.Frame(paned, bg=BG)
        cols = ("source","title","description","download","url")
        self._tv = ttk.Treeview(tf, columns=cols, show="headings",
                                  selectmode="browse")
        for col, head, w, anch in [
            ("source",      "Source",        100, "w"),
            ("title",       "Title",         280, "w"),
            ("description", "Description",   380, "w"),
            ("download",    "Download Link", 180, "w"),
            ("url",         "URL",           300, "w"),
        ]:
            self._tv.heading(col, text=head)
            self._tv.column(col, width=w, anchor=anch, minwidth=40)

        vsb = ttk.Scrollbar(tf, orient="vertical",   command=self._tv.yview)
        hsb = ttk.Scrollbar(tf, orient="horizontal", command=self._tv.xview)
        self._tv.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self._tv.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tf.rowconfigure(0, weight=1); tf.columnconfigure(0, weight=1)

        self._tv.tag_configure("youtube",  foreground="#ff6060")
        self._tv.tag_configure("civitai",  foreground="#66aaff")
        self._tv.tag_configure("github",   foreground="#88cc66")
        self._tv.tag_configure("reddit",   foreground="#ff8844")
        self._tv.tag_configure("comfyhub", foreground="#cc88ff")
        self._tv.tag_configure("other",    foreground=FG2)

        self._tv.bind("<<TreeviewSelect>>", self._on_select)
        self._tv.bind("<Double-1>",          self._open_url)

        # Right-click menu
        ctx = tk.Menu(self, tearoff=0, bg="#1a1a3e", fg=FG,
                      activebackground="#3a3a7e", font=("Consolas",9))
        ctx.add_command(label="🌐  Open URL in browser",      command=self._open_url)
        ctx.add_command(label="⬇  Open Download Link",        command=self._open_download)
        ctx.add_separator()
        ctx.add_command(label="📋  Copy URL",                  command=self._copy_url)
        ctx.add_command(label="📋  Copy Download Link",        command=self._copy_dl)
        self._tv.bind("<Button-3>", lambda e: ctx.tk_popup(e.x_root, e.y_root))

        paned.add(tf, minsize=320)

        # Detail panel
        dp = tk.Frame(paned, bg=PNL2)
        dp_hdr = tk.Frame(dp, bg=PNL2); dp_hdr.pack(fill="x", padx=8, pady=(6,2))
        tk.Label(dp_hdr, text="RESULT DETAILS", bg=PNL2, fg=ACC,
                 font=("Consolas",9,"bold")).pack(side="left")
        ttk.Button(dp_hdr, text="🌐 Open URL",      command=self._open_url    ).pack(side="right", padx=(4,0))
        ttk.Button(dp_hdr, text="⬇ Open Download",  command=self._open_download).pack(side="right", padx=(4,0))
        ttk.Button(dp_hdr, text="📋 Copy URL",       command=self._copy_url    ).pack(side="right")

        self._detail = tk.Text(dp, bg=PNL2, fg="#b8b8e0", font=("Consolas",10),
                               relief="flat", wrap="word", state="disabled",
                               highlightthickness=0)
        self._detail.pack(fill="both", expand=True, padx=8, pady=(0,6))
        paned.add(dp, minsize=160)

        # Set sash leaving 200px for details panel
        self.after(200, lambda: paned.sash_place(
            0, 0, max(300, paned.winfo_height() - 200)))

        # Status bar
        self._status = tk.StringVar(value="Enter a query and click Search Wild.")
        tk.Label(self, textvariable=self._status, bg="#080818", fg="#404080",
                 font=("Consolas",9), anchor="w").pack(
                 fill="x", side="bottom", padx=16, pady=(0,4))

    # ── Search ───────────────────────────────────────────────────────────

    def _start_search(self):
        q = self._query.get().strip()
        if not q:
            return
        enabled = [s["name"] for s, v in zip(self._sources, self._src_vars)
                   if v.get()]
        if not enabled:
            self._status.set("Select at least one source.")
            return
        if self._searching:
            return

        self._searching = True
        self._tv.delete(*self._tv.get_children())
        self._detail.configure(state="normal")
        self._detail.delete("1.0","end")
        self._detail.configure(state="disabled")
        self._search_btn.configure(state="disabled", text="Searching…")
        self._srch_main.set(f"Searching {len(enabled)} source(s) for: \"{q}\"")
        self._srch_sub.set("Claude is browsing the web in real time…")
        self._srch_count.set("")
        self._search_indicator.pack(fill="x", pady=(4,0), before=self._paned)
        self._pb.start(10)
        self._start_dot_anim()
        self._status.set(f"Claude is searching {', '.join(enabled)} for: \"{q}\"\u2026")

        threading.Thread(target=self._search_worker,
                         args=(q, enabled), daemon=True).start()

    def _search_worker(self, query: str, sources: list[str]):
        try:
            client = anthropic.Anthropic()
            sources_str = ", ".join(sources)

            system_prompt = """You are a ComfyUI workflow discovery assistant with web search access.

Search for ComfyUI workflows matching the user's query across the specified platforms.

For EACH result, extract:
- source: platform (YouTube / CivitAI / GitHub / Reddit / ComfyHub / etc.)
- title: name of the video/workflow/post
- url: direct URL to the resource
- description: what the workflow does (2-3 sentences max)
- download_url: direct download link if discoverable (CivitAI model page, HuggingFace, GitHub raw JSON, Google Drive, etc.) — null if not found
- author: creator / channel name

Search guidelines:
- YouTube: search "ComfyUI [query] workflow" — look for tutorial videos, check if description mentions download links
- CivitAI: search civitai.com for workflows — use /models?type=Other or search the workflows section
- GitHub: search for ComfyUI workflow JSON repos matching the query
- Reddit: search r/comfyui and r/StableDiffusion for relevant posts
- ComfyHub: search comfyhub.com for matching workflows

Return ONLY a valid JSON array, no markdown fences, no explanation.
Format: [{"source":"...","title":"...","url":"...","description":"...","download_url":"...or null","author":"..."}]"""

            user_msg = (
                f'Find ComfyUI workflows for: "{query}"\n\n'
                f'Search these sources: {sources_str}\n\n'
                f'Find at least 3-5 results per source where possible. '
                f'Prioritise results with actual downloadable workflows. '
                f'Return JSON array only.'
            )

            result_text  = ""
            search_count = 0
            partial_input = ""

            with client.messages.stream(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                tools=[{"type": "web_search_20250305", "name": "web_search"}],
                system=system_prompt,
                messages=[{"role": "user", "content": user_msg}]
            ) as stream:
                for event in stream:
                    etype = getattr(event, "type", "")

                    # New content block starting
                    if etype == "content_block_start":
                        block = getattr(event, "content_block", None)
                        if block and getattr(block, "type", "") == "tool_use":
                            search_count += 1
                            partial_input = ""
                            self.after(0, self._srch_count.set,
                                       f"web search #{search_count}")
                            self.after(0, self._srch_sub.set,
                                       "Firing web search…")

                    # Delta arriving
                    elif etype == "content_block_delta":
                        delta = getattr(event, "delta", None)
                        if delta:
                            dtype = getattr(delta, "type", "")
                            if dtype == "input_json_delta":
                                partial_input += getattr(delta, "partial_json", "")
                                m = re.search(r'"query"\s*:\s*"([^"]{6,})"', partial_input)
                                if m:
                                    q_preview = m.group(1)[:65]
                                    self.after(0, self._srch_sub.set,
                                               f"🔍 \"{q_preview}\"")
                                    self.after(0, self._status.set,
                                               f"Search #{search_count}: \"{q_preview}\"")
                            elif dtype == "text_delta":
                                result_text += getattr(delta, "text", "")

                # Collect any remaining text from the final message
                final = stream.get_final_message()
                result_text = ""
                for block in final.content:
                    if hasattr(block, "text"):
                        result_text += block.text

            self.after(0, self._status.set,
                       f"✓ {search_count} searches completed — parsing results…")

            # Strip any accidental markdown fences
            result_text = re.sub(r"```[a-z]*", "", result_text).strip("`").strip()

            # Find JSON array in response
            start = result_text.find("[")
            end   = result_text.rfind("]") + 1
            if start >= 0 and end > start:
                result_text = result_text[start:end]

            results = json.loads(result_text)
            self.after(0, self._search_done, results, query)

        except json.JSONDecodeError as e:
            self.after(0, self._search_error,
                       f"Could not parse Claude's response as JSON: {e}")
        except Exception as e:
            self.after(0, self._search_error, str(e))

    def _start_dot_anim(self):
        """Animate the search icon to show life."""
        icons = ["🔍", "🌐", "⚡", "🔎"]
        self._dot_frame = 0

        def tick():
            if not self._searching:
                return
            self._srch_icon.configure(text=icons[self._dot_frame % len(icons)])
            self._dot_frame += 1
            self._anim_after = self.after(400, tick)

        tick()

    def _stop_dot_anim(self):
        if self._anim_after:
            self.after_cancel(self._anim_after)
            self._anim_after = None
        self._srch_icon.configure(text="✓")

    def _search_done(self, results: list[dict], query: str):
        self._searching = False
        self._pb.stop()
        self._search_indicator.pack_forget()
        self._stop_dot_anim()
        self._search_btn.configure(state="normal", text="🌐  Search Wild")
        self._results = results

        self._tv.delete(*self._tv.get_children())
        for r in results:
            source = r.get("source", "")
            dl     = r.get("download_url") or ""
            tag    = self._source_tag(source)
            self._tv.insert("", "end", tags=(tag,), values=(
                source,
                r.get("title", ""),
                r.get("description", ""),
                dl if dl and dl != "null" else "—",
                r.get("url", ""),
            ))

        self._status.set(
            f"Found {len(results)} result(s) for \"{query}\" — "
            f"double-click to open in browser")

    def _search_error(self, msg: str):
        self._searching = False
        self._pb.stop()
        self._search_indicator.pack_forget()
        self._stop_dot_anim()
        self._search_btn.configure(state="normal", text="🌐  Search Wild")
        self._status.set(f"Error: {msg}")
        messagebox.showerror("Wild Search Error", msg, parent=self)

    # ── Selection / actions ──────────────────────────────────────────────

    def _source_tag(self, source: str) -> str:
        sl = source.lower()
        if "youtube"  in sl: return "youtube"
        if "civitai"  in sl: return "civitai"
        if "github"   in sl: return "github"
        if "reddit"   in sl: return "reddit"
        if "comfyhub" in sl: return "comfyhub"
        return "other"

    def _get_selected(self) -> Optional[dict]:
        sel = self._tv.selection()
        if not sel: return None
        vals = self._tv.item(sel[0])["values"]
        if not vals: return None
        url = str(vals[4])
        for r in self._results:
            if r.get("url","") == url:
                return r
        return None

    def _on_select(self, _=None):
        r = self._get_selected()
        if not r: return
        dl  = r.get("download_url") or "—"
        lines = [
            f"SOURCE   : {r.get('source','')}",
            f"AUTHOR   : {r.get('author','')}",
            f"TITLE    : {r.get('title','')}",
            "",
            f"URL      : {r.get('url','')}",
            f"DOWNLOAD : {dl if dl and dl != 'null' else '(not found)'}",
            "",
            "DESCRIPTION",
            "─" * 60,
            r.get("description",""),
        ]
        self._detail.configure(state="normal")
        self._detail.delete("1.0","end")
        self._detail.insert("end", "\n".join(lines))
        self._detail.configure(state="disabled")

    def _open_url(self, _=None):
        import webbrowser
        r = self._get_selected()
        if r and r.get("url"):
            webbrowser.open(r["url"])

    def _open_download(self, _=None):
        import webbrowser
        r = self._get_selected()
        if r:
            dl = r.get("download_url")
            if dl and dl != "null":
                webbrowser.open(dl)
            else:
                self._status.set("No download link found for this result.")

    def _copy_url(self):
        r = self._get_selected()
        if r and r.get("url"):
            self.clipboard_clear(); self.clipboard_append(r["url"])
            self._status.set(f"Copied: {r['url']}")

    def _copy_dl(self):
        r = self._get_selected()
        if r:
            dl = r.get("download_url")
            if dl and dl != "null":
                self.clipboard_clear(); self.clipboard_append(dl)
                self._status.set(f"Copied: {dl}")
            else:
                self._status.set("No download link to copy.")


if __name__ == "__main__":
    app = WorkflowFinder()
    app.mainloop()
