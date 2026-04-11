#!/usr/bin/env python3
"""
py_to_snippet.py — Convert .py files to a widget-ready JSON snippet.

Usage (single file):
    python py_to_snippet.py myscript.py

Usage (multi-file project):
    python py_to_snippet.py main.py helper.py data.csv

Usage (with explicit title/description):
    python py_to_snippet.py main.py -t "My Title" -d "What it does"

Output:
    A .json file named after the first file (e.g. myscript.json),
    or use -o to set the output path.

Tip: add metadata as comments at the top of your main .py file and
they will be picked up automatically:

    # title: Hello World
    # description: A simple greeting program
"""

import argparse
import json
import os
import re
import sys


# ── File types the widget understands ─────────────────────────────────────────
TEXT_EXTENSIONS = {
    '.py', '.txt', '.csv', '.json', '.md', '.html', '.css', '.js',
    '.tsv', '.xml', '.yaml', '.yml', '.ini', '.cfg', '.toml',
}

def read_file(path: str) -> str:
    """Read a file as UTF-8 text (with fallback to latin-1)."""
    try:
        with open(path, encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        with open(path, encoding='latin-1') as f:
            return f.read()


def parse_metadata(content: str) -> dict:
    """
    Extract optional metadata from leading comments in a .py file.

    Recognised comment keys (case-insensitive):
        # title: My Title
        # description: What this does
    """
    meta = {}
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped.startswith('#'):
            break   # stop at first non-comment line
        m = re.match(r'#\s*(title|description)\s*:\s*(.+)', stripped, re.IGNORECASE)
        if m:
            meta[m.group(1).lower()] = m.group(2).strip()
    return meta


def build_snippet(files: list[tuple[str, str]], title: str, description: str) -> dict:
    """Build the snippet dict from (name, content) pairs."""
    snippet = {}
    if title:
        snippet['title'] = title
    if description:
        snippet['description'] = description

    snippet['files'] = [
        {'name': name, 'content': content}
        for name, content in files
    ]
    return snippet


def main():
    parser = argparse.ArgumentParser(
        description='Convert .py (and other text) files to a widget JSON snippet.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        'files', nargs='+', metavar='FILE',
        help='One or more files to include. The first .py file becomes main.py.',
    )
    parser.add_argument('-t', '--title',       help='Snippet title (overrides # title: comment)')
    parser.add_argument('-d', '--description', help='Snippet description (overrides # description: comment)')
    parser.add_argument('-o', '--output',      help='Output JSON file path (default: <first_file_stem>.json)')
    parser.add_argument('--indent', type=int, default=2, help='JSON indentation (default: 2)')

    args = parser.parse_args()

    # ── Validate and read input files ─────────────────────────────────────────
    file_pairs = []   # (name_in_snippet, content)

    for path in args.files:
        if not os.path.isfile(path):
            print(f'Error: file not found: {path}', file=sys.stderr)
            sys.exit(1)

        ext = os.path.splitext(path)[1].lower()
        if ext not in TEXT_EXTENSIONS:
            print(f'Warning: skipping binary/unsupported file: {path}', file=sys.stderr)
            continue

        name    = os.path.basename(path)
        content = read_file(path)
        file_pairs.append((name, content))

    if not file_pairs:
        print('Error: no readable files found.', file=sys.stderr)
        sys.exit(1)

    # ── Auto-promote the first .py to main.py if it isn't already ─────────────
    py_indices = [i for i, (n, _) in enumerate(file_pairs) if n.endswith('.py')]
    if py_indices and file_pairs[py_indices[0]][0] != 'main.py':
        idx  = py_indices[0]
        name, content = file_pairs[idx]
        # Only rename if there's no existing main.py in the list
        if not any(n == 'main.py' for n, _ in file_pairs):
            print(f'Info: renaming "{name}" → "main.py" in snippet.')
            file_pairs[idx] = ('main.py', content)

    # ── Extract metadata from the first .py file ───────────────────────────────
    first_py_content = next((c for n, c in file_pairs if n.endswith('.py')), '')
    meta = parse_metadata(first_py_content)

    title       = args.title       or meta.get('title', '')
    description = args.description or meta.get('description', '')

    # ── If still no title, use the original filename ───────────────────────────
    if not title:
        stem  = os.path.splitext(os.path.basename(args.files[0]))[0]
        title = stem.replace('_', ' ').replace('-', ' ').title()

    # ── Build snippet ──────────────────────────────────────────────────────────
    snippet = build_snippet(file_pairs, title, description)

    # ── Determine output path ──────────────────────────────────────────────────
    if args.output:
        out_path = args.output
    else:
        stem     = os.path.splitext(os.path.basename(args.files[0]))[0]
        out_path = stem + '.json'

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(snippet, f, indent=args.indent, ensure_ascii=False)

    # ── Summary ────────────────────────────────────────────────────────────────
    print(f'✓ Written: {out_path}')
    print(f'  Title:       {snippet.get("title", "(none)")}')
    if snippet.get('description'):
        print(f'  Description: {snippet["description"]}')
    print(f'  Files ({len(snippet["files"])}):', ', '.join(f["name"] for f in snippet["files"]))
    print()
    print('Embed it with:')
    print(f'  <div class="py-snippet" data-src="snippets/{os.path.basename(out_path)}"></div>')


if __name__ == '__main__':
    main()
