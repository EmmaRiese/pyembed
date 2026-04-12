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


def read_file(path):
    """
    Read a file and return its contents as a string.

    Tries UTF-8 first, falls back to latin-1 for files with special characters.

    Parameters:
        path (str): Path to the file to read.

    Returns:
        str: The full contents of the file.
    """
    try:
        with open(path, encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        with open(path, encoding='latin-1') as f:
            return f.read()


def parse_metadata(content):
    """
    Extract optional title and description from leading comment lines in a Python file.

    Scans lines from the top of the file until the first non-comment line.
    Recognised keys (case-insensitive):
        # title: My Title
        # description: What this does

    Parameters:
        content (str): The full source code of a Python file.

    Returns:
        dict: A dictionary with zero or more of the keys 'title' and 'description',
              each mapping to a string value.
    """
    meta = {}
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped.startswith('#'):
            break
        match = re.match(r'#\s*(title|description)\s*:\s*(.+)', stripped, re.IGNORECASE)
        if match:
            key   = match.group(1).lower()
            value = match.group(2).strip()
            meta[key] = value
    return meta


def build_snippet(file_pairs, title, description):
    """
    Build the snippet dictionary that will be saved as JSON.

    Parameters:
        file_pairs  (list of tuple): Each tuple contains (name, content) where
                                     name is the filename shown in the widget
                                     and content is the file's text.
        title       (str): The snippet title shown in the widget toolbar.
        description (str): The subtitle shown below the title. May be empty.

    Returns:
        dict: A snippet dictionary with optional 'title', optional 'description',
              and a 'files' list of {'name': str, 'content': str} entries.
    """
    snippet = {}

    if title:
        snippet['title'] = title

    if description:
        snippet['description'] = description

    file_list = []
    for name, content in file_pairs:
        file_list.append({'name': name, 'content': content})
    snippet['files'] = file_list

    return snippet


def find_first_py_index(file_pairs):
    """
    Find the index of the first Python file in a list of (name, content) pairs.

    Parameters:
        file_pairs (list of tuple): Each tuple contains (name, content).

    Returns:
        int or None: The index of the first .py file, or None if there are none.
    """
    for index, (name, _) in enumerate(file_pairs):
        if name.endswith('.py'):
            return index
    return None


def has_main_py(file_pairs):
    """
    Check whether any file in the list is named 'main.py'.

    Parameters:
        file_pairs (list of tuple): Each tuple contains (name, content).

    Returns:
        bool: True if 'main.py' is present, False otherwise.
    """
    for name, _ in file_pairs:
        if name == 'main.py':
            return True
    return False


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
    file_pairs = []

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

    # ── Auto-promote the first .py to main.py if needed ───────────────────────
    first_py = find_first_py_index(file_pairs)

    if first_py is not None:
        name, content = file_pairs[first_py]
        if name != 'main.py' and not has_main_py(file_pairs):
            print(f'Info: renaming "{name}" → "main.py" in snippet.')
            file_pairs[first_py] = ('main.py', content)

    # ── Extract metadata from the first .py file ───────────────────────────────
    first_py_content = ''
    for name, content in file_pairs:
        if name.endswith('.py'):
            first_py_content = content
            break

    meta = parse_metadata(first_py_content)

    title       = args.title       or meta.get('title', '')
    description = args.description or meta.get('description', '')

    # ── If still no title, derive one from the filename ───────────────────────
    if not title:
        stem  = os.path.splitext(os.path.basename(args.files[0]))[0]
        title = stem.replace('_', ' ').replace('-', ' ').title()

    # ── Build and write the snippet ────────────────────────────────────────────
    snippet = build_snippet(file_pairs, title, description)

    if args.output:
        out_path = args.output
    else:
        stem     = os.path.splitext(os.path.basename(args.files[0]))[0]
        out_path = stem + '.json'

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(snippet, f, indent=args.indent, ensure_ascii=False)

    # ── Summary ────────────────────────────────────────────────────────────────
    file_names = ', '.join(entry['name'] for entry in snippet['files'])

    print(f'✓ Written: {out_path}')
    print(f'  Title:       {snippet.get("title", "(none)")}')
    if snippet.get('description'):
        print(f'  Description: {snippet["description"]}')
    print(f'  Files ({len(snippet["files"])}): {file_names}')
    print()
    print('Embed it with:')
    print(f'  <div class="py-snippet" data-src="snippets/{os.path.basename(out_path)}"></div>')


if __name__ == '__main__':
    main()
