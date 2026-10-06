#!/usr/bin/env python3
"""Inventory and link-audit a markdown corpus.

Usage:
  corpus_scan.py inventory <path> [--json]
  corpus_scan.py links <path> [--json] [--strict]

inventory reports file counts, markdown coverage, frontmatter presence,
duplicate titles and the largest notes.
links reports broken wikilinks, ambiguous targets and orphan notes.
--strict makes links exit 1 when broken links are found.
"""
import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict

IGNORE_DIRS = {
    ".git", ".obsidian", ".trash", "node_modules", "__pycache__",
    ".venv", "venv", ".pytest_cache", ".mypy_cache", ".ruff_cache",
}
WIKILINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]*))?\]\]")
H1 = re.compile(r"^#\s+(.+?)\s*$", re.M)
FM_KEY = re.compile(r"^([A-Za-z_][\w-]*):\s*(.*)$")
LIST_ITEM = re.compile(r"^\s*-\s+")

MD_SUFFIXES = (".md", ".markdown")


def read_text(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def iter_markdown(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in IGNORE_DIRS)
        for name in sorted(filenames):
            if name.lower().endswith(MD_SUFFIXES):
                yield os.path.join(dirpath, name)


def parse_frontmatter(text):
    if not text.startswith("---"):
        return {}, 0
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, 0
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() in ("---", "..."):
            end = i
            break
    if end is None:
        return {}, 0
    fm = {}
    i = 1
    while i < end:
        m = FM_KEY.match(lines[i])
        if m:
            key = m.group(1).lower()
            val = m.group(2).strip()
            if val == "" and i + 1 < end and LIST_ITEM.match(lines[i + 1]):
                items = []
                i += 1
                while i < end and LIST_ITEM.match(lines[i]):
                    items.append(LIST_ITEM.sub("", lines[i]).strip().strip("'\""))
                    i += 1
                fm[key] = items
                continue
            fm[key] = val.strip("'\"")
        i += 1
    return fm, end + 1


def split_list(val):
    if isinstance(val, list):
        return [str(v).strip() for v in val if str(v).strip()]
    if not val:
        return []
    s = str(val).strip()
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1]
    return [p.strip().strip("'\"") for p in s.split(",") if p.strip()]


def note_title(path, fm, text):
    t = fm.get("title")
    if t:
        return str(t).strip().strip("'\"")
    m = H1.search(text)
    if m:
        return m.group(1).strip()
    return os.path.splitext(os.path.basename(path))[0]


def norm(s):
    s = str(s).strip().split("/")[-1]
    s = re.sub(r"\.(md|markdown)$", "", s, flags=re.I)
    s = re.sub(r"\s+", " ", s)
    return s.casefold()


def parse_links(text, body_start):
    lines = text.splitlines()
    body = "\n".join(lines[body_start:])
    out = []
    for m in WIKILINK.finditer(body):
        target = m.group(1).strip()
        if target:
            line = body.count("\n", 0, m.start()) + body_start + 1
            out.append((target, line))
    return out


def collect_notes(root):
    notes = []
    for path in iter_markdown(root):
        text = read_text(path)
        fm, body_start = parse_frontmatter(text)
        aliases = split_list(fm.get("aliases"))
        handle = fm.get("handle")
        if handle:
            aliases.append(str(handle))
        notes.append({
            "path": path,
            "title": note_title(path, fm, text),
            "aliases": aliases,
            "links": parse_links(text, body_start),
            "has_frontmatter": bool(fm),
        })
    return notes


def inventory(root, as_json):
    total = 0
    by_ext = Counter()
    by_top = Counter()
    md_paths = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in IGNORE_DIRS)
        for name in filenames:
            total += 1
            by_ext[os.path.splitext(name)[1].lower() or "(none)"] += 1
            rel = os.path.relpath(dirpath, root)
            top = "(root)" if rel == "." else rel.split(os.sep)[0]
            by_top[top] += 1
            if name.lower().endswith(MD_SUFFIXES):
                md_paths.append(os.path.join(dirpath, name))

    with_fm = 0
    titles = defaultdict(list)
    for path in md_paths:
        text = read_text(path)
        fm, _ = parse_frontmatter(text)
        if fm:
            with_fm += 1
        titles[norm(note_title(path, fm, text))].append(path)

    duplicates = {k: sorted(v) for k, v in titles.items() if len(v) > 1}
    largest = sorted(((os.path.getsize(p), p) for p in md_paths), reverse=True)[:5]

    result = {
        "root": os.path.abspath(root),
        "files_total": total,
        "markdown_notes": len(md_paths),
        "with_frontmatter": with_fm,
        "by_extension": dict(by_ext.most_common()),
        "by_top_folder": dict(by_top.most_common()),
        "duplicate_titles": duplicates,
        "largest_notes": [{"bytes": s, "path": p} for s, p in largest],
    }
    if as_json:
        print(json.dumps(result, indent=2))
        return
    print(f"corpus: {result['root']}")
    print(f"files: {total} total · {len(md_paths)} markdown · {with_fm} with frontmatter")
    ext_line = " · ".join(f"{e} {c}" for e, c in by_ext.most_common(8))
    print(f"by extension: {ext_line}")
    top_line = " · ".join(f"{d} {c}" for d, c in by_top.most_common(8))
    print(f"top folders: {top_line}")
    if duplicates:
        print(f"duplicate titles: {len(duplicates)} group(s)")
        for key, paths in list(duplicates.items())[:5]:
            print(f"  - \"{key}\" → {', '.join(os.path.relpath(p, root) for p in paths)}")
    else:
        print("duplicate titles: none")
    if largest:
        print("largest notes:")
        for size, path in largest:
            print(f"  - {os.path.relpath(path, root)} ({size} bytes)")
    print("next: register the folder as a project, then enrich in batches of 10–20 "
          "(see references/seed-playbook.md)")


def links(root, as_json, strict):
    notes = collect_notes(root)
    index = defaultdict(set)
    for n in notes:
        keys = {norm(n["title"])}
        keys |= {norm(a) for a in n["aliases"]}
        keys.add(norm(os.path.splitext(os.path.basename(n["path"]))[0]))
        for key in keys:
            index[key].add(n["path"])

    broken = []
    inbound = defaultdict(set)
    for n in notes:
        for target, line in n["links"]:
            key = norm(target)
            if key in index:
                for p in index[key]:
                    if p != n["path"]:
                        inbound[p].add(n["path"])
            else:
                broken.append({"file": n["path"], "line": line, "target": target})

    orphans = [n["path"] for n in notes
               if not n["links"] and not inbound.get(n["path"])]
    ambiguous = {k: sorted(v) for k, v in index.items() if len(v) > 1}

    result = {
        "root": os.path.abspath(root),
        "notes": len(notes),
        "links": sum(len(n["links"]) for n in notes),
        "broken": broken,
        "ambiguous_targets": ambiguous,
        "orphans": orphans,
    }
    if as_json:
        print(json.dumps(result, indent=2))
    else:
        print(f"notes: {result['notes']} · links: {result['links']} · "
              f"broken: {len(broken)} · orphans: {len(orphans)}")
        if broken:
            print("broken links:")
            for b in broken[:20]:
                print(f"  - {os.path.relpath(b['file'], root)}:{b['line']} → [[{b['target']}]]")
        if ambiguous:
            print(f"ambiguous targets: {len(ambiguous)}")
            for key, paths in list(ambiguous.items())[:10]:
                print(f"  - \"{key}\" → {', '.join(os.path.relpath(p, root) for p in paths)}")
        if orphans:
            print(f"orphans (no links in or out): {len(orphans)}")
            for p in orphans[:20]:
                print(f"  - {os.path.relpath(p, root)}")
    if strict and broken:
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser(description="Inventory and link-audit a markdown corpus.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    inv = sub.add_parser("inventory", help="catalog files, duplicates and frontmatter")
    inv.add_argument("path")
    inv.add_argument("--json", action="store_true")
    lnk = sub.add_parser("links", help="report broken links, ambiguous targets and orphans")
    lnk.add_argument("path")
    lnk.add_argument("--json", action="store_true")
    lnk.add_argument("--strict", action="store_true", help="exit 1 when broken links exist")
    args = ap.parse_args()
    if not os.path.isdir(args.path):
        print(f"not a directory: {args.path}", file=sys.stderr)
        sys.exit(2)
    if args.cmd == "inventory":
        inventory(args.path, args.json)
    else:
        links(args.path, args.json, args.strict)


if __name__ == "__main__":
    main()
