# Python Snippet Widget

A lightweight, static, embeddable Python code runner styled after IDLE. Visitors can edit and run Python directly in the browser — no server required. Python executes via [Skulpt](https://skulpt.org) (Python compiled to JavaScript) and the editor is powered by [CodeMirror 6](https://codemirror.net).

---

## How embedding works

The easiest way to embed a snippet on any page is with a single `<iframe>`:

```html
<iframe
  src="https://USERNAME.github.io/REPO/viewer.html?src=https://USERNAME.github.io/REPO/snippets/hello.json"
  width="100%"
  height="540"
  style="border:none;border-radius:8px;"
  loading="lazy"
></iframe>
```

- Replace `USERNAME` with your GitHub username and `REPO` with your repository name
- Use the **</> Embed** button in any widget on the demo page to get a ready-to-paste iframe for that specific snippet

### Alternative: script tag (multiple widgets on one page)

If you want several widgets on the same page and prefer not to use iframes, add two lines instead:

```html
<script src="https://USERNAME.github.io/REPO/embed.js"></script>
<div class="py-snippet" data-src="https://USERNAME.github.io/REPO/snippets/hello.json"></div>
```

You can place as many `<div class="py-snippet">` elements as you like — Skulpt loads only once and is shared across all widgets.

---

## Snippet JSON format

Each snippet is a JSON file in the `snippets/` folder. It supports single-file and multi-file projects.

### Single file (simple)

```json
{
  "title": "Hello World",
  "description": "Optional subtitle shown below the title.",
  "code": "print('Hello, world!')"
}
```

### Multi-file project

```json
{
  "title": "My Project",
  "description": "A project with multiple files.",
  "files": [
    { "name": "main.py",   "content": "from helper import greet\ngreet()" },
    { "name": "helper.py", "content": "def greet():\n    print('Hello!')" },
    { "name": "data.txt",  "content": "" }
  ]
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `title` | No | Displayed as the widget heading |
| `description` | No | Displayed as a subtitle |
| `code` | Yes (single-file) | Python code for single-file snippets |
| `files` | Yes (multi-file) | Array of `{ name, content }` objects |

The first file named `main.py` is always the entry point that gets executed when ▶ Run is clicked.

---

## Converting .py files to snippets

Use the included `py_to_snippet.py` script to convert existing Python files to the JSON format:

```bash
# Single file — title/description read from # comments at the top
python3 py_to_snippet.py myscript.py

# Multi-file project
python3 py_to_snippet.py main.py helper.py data.csv

# Override title/description and set output path
python3 py_to_snippet.py main.py -t "My Title" -d "What it does" -o snippets/basic-examples/my_snippet.json
```

Add metadata comments at the top of your `.py` file and they are picked up automatically:

```python
# title: Hello World
# description: A simple greeting program

print("Hello!")
```

---

## Adding a new snippet

1. Place the JSON file in the appropriate subfolder:
   - `snippets/basic-examples/` — standalone demos
   - `snippets/lecture-examples/` — numbered lecture files (`01.json` … `17.json`)
   - `snippets/mobius-material/` — numbered Möbius files (`01.json` … `06.json`)

2. Add an entry to `snippets/index.json` under the matching category.

3. Commit and push:

```bash
git add snippets/
git commit -m "Add new snippet"
git push
```

4. Get the iframe embed code by clicking **</> Embed** on the demo page, or construct it manually:

```html
<iframe
  src="https://USERNAME.github.io/REPO/viewer.html?src=https://USERNAME.github.io/REPO/snippets/basic-examples/my_example.json"
  width="100%"
  height="540"
  style="border:none;border-radius:8px;"
  loading="lazy"
></iframe>
```

---

## Deploying to GitHub Pages

### First-time setup

1. Create a new public repository on GitHub

2. Push this project to it:

```bash
cd py-snippet-widget
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/USERNAME/REPO.git
git branch -M main
git push -u origin main
```

3. Enable GitHub Pages:
   - Go to your repo on GitHub → **Settings** → **Pages**
   - Under **Source**, select **Deploy from a branch**
   - Set branch to `main`, folder to `/ (root)`
   - Click **Save**

4. Wait ~60 seconds, then visit:
   `https://USERNAME.github.io/REPO/`

The `.nojekyll` file in the repo root tells GitHub Pages to serve files as-is without Jekyll processing.

### Updating

Any `git push` to `main` automatically redeploys within 30–60 seconds.

---

## File structure

```
/
├── index.html              ← demo page (GitHub Pages homepage)
├── viewer.html             ← single-snippet iframe host (used for embedding)
├── embed.js                ← the widget script
├── embed.css               ← optional host-page spacing overrides
├── py_to_snippet.py        ← CLI tool to convert .py files to JSON snippets
├── snippets/
│   ├── index.json          ← master list of all snippets by category
│   ├── basic-examples/
│   │   ├── hello.json
│   │   ├── greet.json
│   │   ├── fibonacci.json
│   │   └── list_example.json
│   ├── lecture-examples/
│   │   ├── 01.json … 17.json
│   └── mobius-material/
│       ├── 01.json … 06.json
├── .nojekyll               ← disables Jekyll on GitHub Pages
└── README.md
```

---

## Widget features

| Feature | Details |
|---------|---------|
| **Editor** | CodeMirror 6 with IDLE-style syntax highlighting and Menlo font |
| **Syntax colours** | Keywords orange, strings green, comments red, built-ins purple, def/class names blue — matching IDLE exactly |
| **▶ Run** | Executes `main.py` via Skulpt; also triggered by **Ctrl+Enter** / **Cmd+Enter** |
| **↺ Reset** | Restores all files to their original state and clears output |
| **↓ Download** | Saves the currently active file as-is |
| **`input()`** | Rendered inline in the output panel — type and press Enter, just like a shell |
| **File I/O** | Virtual filesystem: `open()`, `read()`, `write()`, `readline()`, `for line in file` all work |
| **Multi-file** | Import across files; file panel on the left to switch between them |
| **Output panel** | White background, monospace font; errors in red |

---

## Browser support

Works in all modern browsers: Chrome, Firefox, Safari, Edge.
Requires ES modules support (universally available since 2019).

---

## Limitations

- Only standard Python built-ins and a subset of the standard library are available (no `numpy`, `pandas`, etc.) — see [Skulpt's supported modules](https://skulpt.org/docs/index.html)
- `input()` is synchronous-style but implemented asynchronously — code pauses and waits for the user to type
- Only one snippet can run at a time per page (Skulpt is single-threaded)
- Network access from Python code is not available

---

## Open-source dependencies and licences

This project depends on the following open-source libraries, all of which are loaded from CDN at runtime with no build step required.

### Skulpt
- **What it is**: A full Python 3 interpreter compiled to JavaScript, enabling Python to run directly in the browser without a server or WebAssembly.
- **Version used**: 1.2.0
- **CDN**: `https://cdn.jsdelivr.net/npm/skulpt@1.2.0/`
- **Licence**: [MIT License](https://opensource.org/licenses/MIT) (runtime) / [Python Software Foundation License v2](https://opensource.org/licenses/Python-2.0) (for compatibility with CPython)
- **Authors**: Originally created by Scott Graham. Key contributors include Brad Miller, Scott Rixner, Albert-Jan Nijburg, Marie Chatfield, and others.
- **Source**: https://github.com/skulpt/skulpt

### CodeMirror 6
- **What it is**: A highly extensible code editor component for the browser, used here to provide the Python editor with syntax highlighting, line numbers, bracket matching, and auto-indent.
- **Version used**: 6.0.1 (core) plus `@codemirror/state`, `@codemirror/language`, `@codemirror/lang-python`, `@lezer/highlight`
- **CDN**: `https://esm.sh/codemirror@6.0.1`
- **Licence**: [MIT License](https://opensource.org/licenses/MIT)
- **Author/Maintainer**: Marijn Haverbeke
- **Source**: https://github.com/codemirror/codemirror.next

### esm.sh
- **What it is**: A CDN that serves npm packages as ES modules, used to load CodeMirror 6 directly in the browser without a bundler.
- **Licence**: [MIT License](https://github.com/esm-dev/esm.sh/blob/main/LICENSE)
- **Source**: https://github.com/esm-dev/esm.sh

### jsDelivr
- **What it is**: A free, open-source CDN used to load Skulpt.
- **Licence**: [MIT License](https://github.com/jsdelivr/jsdelivr/blob/master/LICENSE)
- **Source**: https://github.com/jsdelivr/jsdelivr

---

## Licence

This project (the widget code, demo page, and converter script) is released under the [MIT License](https://opensource.org/licenses/MIT). You are free to use, modify, and distribute it in personal and commercial projects.
