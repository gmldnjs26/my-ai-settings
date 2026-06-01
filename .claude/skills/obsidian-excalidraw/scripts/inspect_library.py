#!/usr/bin/env python3
"""
inspect_library.py — list the items inside an Excalidraw library (.excalidrawlib).

Usage:
    python3 inspect_library.py <file.excalidrawlib> [--index N]

Without --index: prints one line per item (index, the text labels it contains so you
can identify icons like "CDN", element type counts, and bounding-box size).
With --index N: dumps the raw element list of item N (useful before instancing it).

Handles both formats:
    v1: top-level key "library"      -> each item is a bare array of elements
    v2: top-level key "libraryItems" -> each item is {name, elements}
"""

import json
import sys


def items(path):
    d = json.load(open(path, encoding="utf-8"))
    return d.get("libraryItems") or d.get("library") or []


def elements(item):
    if isinstance(item, list):
        return [e for e in item if isinstance(e, dict)]
    return [e for e in item.get("elements", []) if isinstance(e, dict)]


def name(item):
    return "" if isinstance(item, list) else item.get("name", "")


def bbox(els):
    if not els:
        return (0, 0, 0, 0)
    xs = [e.get("x", 0) for e in els]
    ys = [e.get("y", 0) for e in els]
    xe = [e.get("x", 0) + e.get("width", 0) for e in els]
    ye = [e.get("y", 0) + e.get("height", 0) for e in els]
    return min(xs), min(ys), max(xe), max(ye)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    path = sys.argv[1]
    its = items(path)

    if "--index" in sys.argv:
        i = int(sys.argv[sys.argv.index("--index") + 1])
        print(json.dumps(elements(its[i]), ensure_ascii=False, indent=2))
        return

    print(f"{len(its)} item(s) in {path}\n")
    for i, it in enumerate(its):
        els = elements(it)
        texts = [e.get("text", "") for e in els if e.get("type") == "text"]
        types = {}
        for e in els:
            types[e["type"]] = types.get(e["type"], 0) + 1
        x0, y0, x1, y1 = bbox(els)
        label = name(it) or (texts[0] if texts else "")
        print(f"[{i:>2}] {label!r:<24} w={x1 - x0:>4.0f} h={y1 - y0:>4.0f} "
              f"n={len(els):>2}  texts={texts}  types={types}")


if __name__ == "__main__":
    main()
