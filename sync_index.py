#!/usr/bin/env python3
"""
sync_index.py

Reads the title from every snippet JSON file listed in snippets/index.json
and writes the title back into the index entry so the page labels match
the snippet files exactly.

Run from the py-snippet-widget directory:
    python3 sync_index.py
"""

import json
import os

INDEX_PATH   = os.path.join(os.path.dirname(__file__), 'snippets', 'index.json')
SNIPPET_ROOT = os.path.join(os.path.dirname(__file__), 'snippets')


def main():
    """Read each snippet file and sync its title into index.json."""
    with open(INDEX_PATH, encoding='utf-8') as f:
        index = json.load(f)

    updated = 0
    missing = 0

    for cat in index['categories']:
        for entry in cat['snippets']:
            snippet_path = os.path.join(SNIPPET_ROOT, entry['file'])
            if not os.path.isfile(snippet_path):
                print('  MISSING: ' + entry['file'])
                missing += 1
                continue

            with open(snippet_path, encoding='utf-8') as f:
                snippet = json.load(f)

            new_title = snippet.get('title', '').strip()
            if new_title and new_title != entry.get('title'):
                print('  Updated: ' + entry['file'])
                print('    old: ' + entry.get('title', ''))
                print('    new: ' + new_title)
                entry['title'] = new_title
                updated += 1

    with open(INDEX_PATH, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    print()
    print(str(updated) + ' titles updated, ' + str(missing) + ' files missing.')
    print('index.json saved.')


if __name__ == '__main__':
    main()
