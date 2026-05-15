# Contributing to ComfyUI Workflow Finder

Thanks for your interest in contributing! This is a community tool built for ComfyUI users by a ComfyUI user, and contributions that make it more useful for everyone are welcome.

---

## Bug Reports

Open a [GitHub Issue](https://github.com/gregowahoo/comfyui-workflow-finder/issues) and include:

- What you did
- What you expected to happen
- What actually happened
- Your Python version (`python --version`)
- Your OS (Windows 10 / 11)
- Any error message from the terminal

---

## Feature Requests

Open a [GitHub Issue](https://github.com/gregowahoo/comfyui-workflow-finder/issues) describing what you want and why it would be useful. No guarantees, but good ideas get built.

---

## Pull Requests

PRs are welcome for:

### ✅ Great PR targets
- **Adding node types to `NODE_CAPS`** — this is the easiest and most valuable contribution. If you use a custom node that isn't recognized by the search, add it. The dict is at the top of `workflow_finder.py`:
  ```python
  "YourNodeClassName": "keywords describing what it does",
  ```
- **Bug fixes** — if you found it and fixed it, send the PR
- **New search suggestions** — additions to `DEFAULT_QUERIES` in new or existing categories
- **New wild search sources** — additions to `DEFAULT_SOURCES`
- **Performance improvements** — faster scanning, smarter caching, etc.

### ⚠️ Open an Issue first
For anything bigger — new UI panels, major workflow changes, new dependencies — open an Issue and describe what you're thinking before writing code. Saves everyone time if the direction doesn't fit.

### ❌ Out of scope
- Changing the dark colour scheme
- Adding file deletion or modification features (intentionally report-only)
- Dependencies that require a complex install

---

## Adding Node Types (most wanted)

The `NODE_CAPS` dictionary is what powers the Fast search mode. If your favourite custom node isn't returning results, this is why and the fix is one line.

Find the dict near the top of `workflow_finder.py` and add your node:

```python
# Format: "NodeClassName": "space separated keywords describing capabilities",

"MyCustomNode":        "what it does keyword1 keyword2 keyword3",
"AnotherCustomLoader": "load something model specific thing",
```

**Tips for good keywords:**
- Use lowercase
- Think about what a user would *search for*, not just the node name
- Include synonyms (`caption describe tag` not just `caption`)
- Look at nearby entries for style guidance

---

## Code Style

- Python 3.10+
- No external dependencies beyond `anthropic` (optional) and standard library
- Keep tkinter UI code consistent with the existing dark theme
- No type annotations required but welcome
- Comments on anything non-obvious

---

## Questions

Open an Issue tagged `question` — happy to help.
