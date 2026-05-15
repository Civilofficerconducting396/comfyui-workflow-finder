# ⚡ ComfyUI Workflow Finder

A desktop search and preview tool for your local ComfyUI workflow library — plus a live web search to find workflows in the wild across YouTube, CivitAI, GitHub, and more.

![Workflow Finder](docs/screenshot.png)

---

## Features

### Local Search
- **Semantic search** — describe what you want (*"load a video and generate a caption"*) and find matching workflows instantly by node type
- **AI-powered search** — optional Claude API mode for natural language queries that go beyond keyword matching
- **Name filter** — partial match, case-insensitive, live-as-you-type with custom quick-pick dropdown
- **Suggestions dropdown** — 80+ pre-built search phrases across 15 categories, loaded from an editable JSON file
- **Sortable columns** — click any column header to sort ascending/descending with arrow indicator
- **Created / Modified dates** — find your most recently worked-on workflows instantly
- **Multiple scan locations** — add as many workflow folders as you have, toggle each on/off with real checkboxes
- **Dynamic location toggling** — check or uncheck a location and results update automatically without a full rescan
- **Config persistence** — scan locations, enabled states, and preferences survive restarts

### Graph Preview
- **Node graph preview** — see the actual node layout of any workflow, colour-coded by node type
- **Fullscreen graph popup** — open any workflow graph maximized with a colour legend
- **Zoomable / pannable canvas** — scroll to zoom, drag to pan, F to fit, right-click for menu
- **Bezier wire colouring** — wires coloured by data type (IMAGE, LATENT, MODEL, VIDEO, MASK, etc.)
- **Hover tooltips** — hover any node to see type, title, and slot counts

### Find in the Wild 🌐
- **Live web search** — Claude searches YouTube, CivitAI, GitHub, Reddit, ComfyHub in real time
- **Download link detection** — automatically finds direct download links where available
- **Live search indicator** — animated progress panel shows each web search query as Claude fires it
- **Configurable sources** — edit `workflow_finder_sources.json` to add or remove sources

---

## Requirements

- Python 3.10+
- `tkinter` — included with standard Python on Windows
- `anthropic` — needed for AI search mode and Find in the Wild

```powershell
python -m pip install anthropic
```

---

## Installation

1. Download all files into a folder (e.g. `C:\py\Workflow Finder\`)
2. Run:

```powershell
python workflow_finder.py
```

No installer, no virtual environment needed.

---

## Files

| File | Purpose |
|---|---|
| `workflow_finder.py` | Main application |
| `workflow_finder_queries.json` | Suggested search phrases (auto-created, editable) |
| `workflow_finder_prefixes.json` | Quick name-filter prefixes (auto-created, editable) |
| `workflow_finder_sources.json` | Wild Search sources (auto-created, editable) |
| `workflow_finder_config.json` | Your scan locations — auto-created, **not in repo** |

---

## Search Modes

**⚡ Fast** — local keyword matching against a built-in node capability map (~100 node types). Instant, no internet required.

**🤖 AI (Claude)** — sends workflow fingerprints to the Claude API for true semantic matching. Requires an Anthropic API key set in Windows Environment Variables as `ANTHROPIC_API_KEY`.

---

## Find in the Wild

Click **🌐 Find in Wild** in the toolbar. Claude browses real websites in real time and returns:

- Source, Title, Description, Download Link, URL
- Double-click any row to open in your browser
- Right-click for copy options

Edit `workflow_finder_sources.json` to customise which sites are searched.

---

## Graph Preview Controls

| Control | Action |
|---|---|
| Scroll wheel | Zoom in / out |
| Left drag | Pan |
| `F` key | Fit to screen |
| Right-click | Context menu |
| Hover | Node tooltip |

---

## Customisation

All JSON files are auto-created on first run. Edit freely, restart to reload.

Add your own search suggestions to `workflow_finder_queries.json`, name filter prefixes to `workflow_finder_prefixes.json`, and wild search sources to `workflow_finder_sources.json`.

---

## Related

- [ComfyUI Model Scanner](https://github.com/gregowahoo/comfyui-model-scanner)

---

## License

MIT
