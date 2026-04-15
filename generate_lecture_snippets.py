#!/usr/bin/env python3
"""
generate_lecture_snippets.py

Batch-converts all examples in Lecturer_examples_DD1310 into widget JSON
snippets and writes them to snippets/lecture-examples/lecture{N}/.

Run from the py-snippet-widget directory:
    python3 generate_lecture_snippets.py

Each example becomes:
    snippets/lecture-examples/lecture01/01.json   (code 1.1)
    snippets/lecture-examples/lecture01/02.json   (code 1.2)
    ...

The script also rewrites snippets/index.json to include all lecture categories.
"""

import json
import os
import re
import sys


# ── Paths ──────────────────────────────────────────────────────────────────────
SOURCE_ROOT  = os.path.join(os.path.dirname(__file__), '..', 'Lecturer_examples_DD1310')
SNIPPET_ROOT = os.path.join(os.path.dirname(__file__), 'snippets', 'lecture-examples')
INDEX_PATH   = os.path.join(os.path.dirname(__file__), 'snippets', 'index.json')

TEXT_EXTENSIONS = {
    '.py', '.txt', '.csv', '.json', '.md', '.html', '.css', '.js',
    '.tsv', '.xml', '.yaml', '.yml', '.ini', '.cfg', '.toml',
}


# ── Title generation ───────────────────────────────────────────────────────────

def read_file_safe(path):
    """
    Read a text file, trying UTF-8 then latin-1.

    Parameters:
        path (str): File path to read.

    Returns:
        str: File contents, or empty string on failure.
    """
    for enc in ('utf-8', 'latin-1'):
        try:
            with open(path, encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, OSError):
            continue
    return ''


def extract_title_comment(code):
    """
    Return the value of a '# title:' comment at the top of the code.

    Parameters:
        code (str): Python source code.

    Returns:
        str or None: The title string, or None if not found.
    """
    for line in code.splitlines():
        stripped = line.strip()
        if not stripped.startswith('#'):
            break
        match = re.match(r'#\s*title\s*:\s*(.+)', stripped, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def analyse_code(code):
    """
    Analyse Python source and return a dict of detected features.

    Parameters:
        code (str): Python source code.

    Returns:
        dict: Keys: imports, classes, functions, has_main, has_try,
              has_while, has_for, has_input, has_file, has_recursion,
              has_inheritance, first_comment.
    """
    imports      = re.findall(r'^\s*import\s+(\w+)', code, re.MULTILINE)
    imports     += re.findall(r'^\s*from\s+(\w+)\s+import', code, re.MULTILINE)
    classes      = re.findall(r'^\s*class\s+(\w+)', code, re.MULTILINE)
    functions    = re.findall(r'^\s*def\s+(\w+)', code, re.MULTILINE)
    first_comment = ''
    for line in code.splitlines():
        s = line.strip()
        if s.startswith('#'):
            text = s.lstrip('#').strip()
            if text and 'coding' not in text.lower():
                first_comment = text
                break
        elif s:
            break

    return {
        'imports':       imports,
        'classes':       classes,
        'functions':     functions,
        'has_main':      'main' in functions,
        'has_try':       bool(re.search(r'^\s*try\s*:', code, re.MULTILINE)),
        'has_while':     bool(re.search(r'^\s*while\s+', code, re.MULTILINE)),
        'has_for':       bool(re.search(r'^\s*for\s+', code, re.MULTILINE)),
        'has_input':     'input(' in code,
        'has_file':      bool(re.search(r'\bopen\s*\(', code)),
        'has_recursion': any(
            f in code.replace('def ' + f, '', 1)
            for f in functions
        ),
        'has_inheritance': bool(re.search(r'class\s+\w+\s*\(', code)),
        'has_super':     'super()' in code,
        'first_comment': first_comment,
    }


def generate_title(code_files, lecture_num, example_num):
    """
    Generate a descriptive title for an example based on its code content.

    Parameters:
        code_files (list of tuple): Each tuple is (filename, code_string).
        lecture_num (int):  Lecture number (1–15).
        example_num (int):  Example position within the lecture.

    Returns:
        str: A descriptive title like "1.2 – While Loop with Break".
    """
    prefix = str(lecture_num) + '.' + str(example_num)

    # Combine all code for analysis
    all_code = '\n'.join(code for _, code in code_files)
    main_code = next(
        (code for name, code in code_files if name == 'main.py'),
        code_files[0][1] if code_files else ''
    )

    # Check for explicit title comment first
    for name, code in code_files:
        if name.endswith('.py'):
            t = extract_title_comment(code)
            if t:
                return prefix + ' \u2013 ' + t

    info = analyse_code(all_code)
    non_main_modules = [f for f, _ in code_files if f not in ('main.py',) and f.endswith('.py')]

    # Use first meaningful comment if it's descriptive enough
    if info['first_comment'] and len(info['first_comment']) > 8:
        title = info['first_comment'].rstrip('.')
        # Capitalise first letter
        title = title[0].upper() + title[1:]
        return prefix + ' \u2013 ' + title

    # Multi-module project
    if len(code_files) > 1 and non_main_modules:
        mod_names = ', '.join(os.path.splitext(m)[0].capitalize() for m in non_main_modules)
        classes = info['classes']
        if classes:
            return prefix + ' \u2013 ' + classes[0] + ' Class (multi-file)'
        return prefix + ' \u2013 Module Import: ' + mod_names

    # Class-based examples
    classes  = info['classes']
    has_inh  = info['has_inheritance']
    has_sup  = info['has_super']

    if classes:
        name = classes[0]
        if has_sup:
            return prefix + ' \u2013 ' + name + ': Inheritance with super()'
        if has_inh:
            parent = re.search(r'class\s+' + name + r'\s*\((\w+)\)', all_code)
            parent_name = parent.group(1) if parent else ''
            return prefix + ' \u2013 ' + name + (' extends ' + parent_name if parent_name else ': Inheritance')
        if info['has_main']:
            return prefix + ' \u2013 ' + name + ' Class with Menu'
        return prefix + ' \u2013 ' + name + ' Class'

    # File I/O
    if info['has_file']:
        if info['has_try']:
            return prefix + ' \u2013 File I/O with Exception Handling'
        return prefix + ' \u2013 Reading and Writing Files'

    # Exception handling
    if info['has_try']:
        exc = re.findall(r'except\s+(\w+)', all_code)
        if exc:
            return prefix + ' \u2013 Exception Handling: ' + exc[0]
        return prefix + ' \u2013 Try/Except: Exception Handling'

    # Specific imports
    imports = [i.lower() for i in info['imports']]
    if 'random' in imports:
        return prefix + ' \u2013 Random Numbers'
    if 'math' in imports:
        return prefix + ' \u2013 Math Module'
    if 'copy' in imports:
        return prefix + ' \u2013 Copying Objects'

    # Recursion
    if info['has_recursion']:
        fns = [f for f in info['functions'] if f != 'main']
        fn  = fns[0] if fns else 'function'
        return prefix + ' \u2013 Recursion: ' + fn + '()'

    # Functions
    user_fns = [f for f in info['functions'] if f != 'main']
    if user_fns:
        fn = user_fns[0]
        if info['has_main']:
            return prefix + ' \u2013 Functions and main()'
        return prefix + ' \u2013 Function: ' + fn + '()'

    # Loops
    if info['has_while'] and info['has_for']:
        return prefix + ' \u2013 While and For Loops'
    if info['has_while']:
        if 'break' in all_code:
            return prefix + ' \u2013 While Loop with Break'
        if info['has_input']:
            return prefix + ' \u2013 While Loop with User Input'
        return prefix + ' \u2013 While Loop'
    if info['has_for']:
        if 'range(' in all_code:
            return prefix + ' \u2013 For Loop with range()'
        return prefix + ' \u2013 For Loop'

    # Collections
    if re.search(r'\{[^}]*:[^}]*\}', all_code) or '.items()' in all_code or '.keys()' in all_code:
        return prefix + ' \u2013 Dictionary'
    if re.search(r'\bset\s*\(', all_code) or ('union' in all_code or 'intersection' in all_code):
        return prefix + ' \u2013 Set Operations'
    if '[' in all_code and ('.append(' in all_code or '.insert(' in all_code):
        return prefix + ' \u2013 List Operations'
    if '[' in all_code:
        return prefix + ' \u2013 Lists'

    # if/elif
    if re.search(r'^\s*elif\s', all_code, re.MULTILINE):
        return prefix + ' \u2013 if / elif / else'
    if re.search(r'^\s*if\s', all_code, re.MULTILINE):
        return prefix + ' \u2013 if / else'

    # Input/output
    if info['has_input']:
        return prefix + ' \u2013 User Input and Output'

    return prefix + ' \u2013 Example ' + str(example_num)


# ── Snippet builder ────────────────────────────────────────────────────────────

def build_snippet(file_pairs, title, description=''):
    """
    Build the snippet dictionary that will be saved as JSON.

    Parameters:
        file_pairs  (list of tuple): (name, content) pairs for each file.
        title       (str): Snippet title.
        description (str): Optional subtitle.

    Returns:
        dict: Snippet ready for json.dump().
    """
    snippet = {'title': title}
    if description:
        snippet['description'] = description
    snippet['files'] = [{'name': n, 'content': c} for n, c in file_pairs]
    return snippet


def collect_example(path):
    """
    Collect all files for a single example.

    A single .py file → [(basename, code)].
    A subfolder       → all text files sorted with main.py first.

    Parameters:
        path (str): Path to the .py file or subfolder.

    Returns:
        list of tuple: (filename, content) pairs, or empty list on failure.
    """
    if os.path.isfile(path):
        code = read_file_safe(path)
        return [('main.py', code)]

    if os.path.isdir(path):
        pairs = []
        entries = sorted(os.listdir(path))
        # main.py first
        if 'main.py' in entries:
            entries.remove('main.py')
            entries = ['main.py'] + entries
        for entry in entries:
            full = os.path.join(path, entry)
            ext  = os.path.splitext(entry)[1].lower()
            if os.path.isfile(full) and ext in TEXT_EXTENSIONS:
                content = read_file_safe(full)
                pairs.append((entry, content))
        return pairs

    return []


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    """
    Process all lecture examples and write JSON snippets plus updated index.json.
    """
    # Load existing index.json to preserve basic-examples and mobius-material
    with open(INDEX_PATH, encoding='utf-8') as f:
        index = json.load(f)

    # Remove any existing lecture categories so we rebuild them cleanly
    non_lecture = [c for c in index['categories'] if not c['folder'].startswith('lecture-examples/lecture')]
    index['categories'] = non_lecture

    lecture_dirs = sorted(
        d for d in os.listdir(SOURCE_ROOT)
        if os.path.isdir(os.path.join(SOURCE_ROOT, d))
        and re.match(r'Lecture\d+$', d, re.IGNORECASE)
    )
    # Sort numerically
    lecture_dirs.sort(key=lambda d: int(re.search(r'\d+', d).group()))

    total_snippets = 0

    for lecture_dir in lecture_dirs:
        lecture_num = int(re.search(r'\d+', lecture_dir).group())
        src_path    = os.path.join(SOURCE_ROOT, lecture_dir)
        dest_folder = 'lecture{:02d}'.format(lecture_num)
        dest_path   = os.path.join(SNIPPET_ROOT, dest_folder)
        os.makedirs(dest_path, exist_ok=True)

        # Collect all examples: direct .py files + subfolders
        entries = sorted(os.listdir(src_path))
        examples = []

        for entry in entries:
            full = os.path.join(src_path, entry)
            if os.path.isfile(full) and entry.endswith('.py'):
                examples.append(full)
            elif os.path.isdir(full):
                # Only include if subfolder contains at least one .py file
                has_py = any(f.endswith('.py') for f in os.listdir(full))
                if has_py:
                    examples.append(full)

        category_snippets = []

        for idx, example_path in enumerate(examples, start=1):
            file_pairs = collect_example(example_path)
            if not file_pairs:
                continue

            title       = generate_title(file_pairs, lecture_num, idx)
            snippet     = build_snippet(file_pairs, title)
            out_name    = '{:02d}.json'.format(idx)
            out_path    = os.path.join(dest_path, out_name)
            rel_file    = 'lecture-examples/' + dest_folder + '/' + out_name

            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(snippet, f, indent=2, ensure_ascii=False)

            category_snippets.append({
                'id':    'lecture{:02d}-{:02d}'.format(lecture_num, idx),
                'file':  rel_file,
                'title': title,
            })
            total_snippets += 1

        # Add this lecture as a category in index.json
        index['categories'].append({
            'name':     'Lecture ' + str(lecture_num),
            'folder':   'lecture-examples/' + dest_folder,
            'snippets': category_snippets,
        })

        print('Lecture {:2d}: {:2d} snippets written to snippets/lecture-examples/{}/'.format(
            lecture_num, len(category_snippets), dest_folder))

    # Write updated index.json
    with open(INDEX_PATH, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    print()
    print('Done. ' + str(total_snippets) + ' snippets total.')
    print('index.json updated.')


if __name__ == '__main__':
    main()
