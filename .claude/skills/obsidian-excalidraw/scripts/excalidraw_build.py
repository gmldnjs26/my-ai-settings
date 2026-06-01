#!/usr/bin/env python3
"""
excalidraw_build.py — build and write Excalidraw drawings into an Obsidian vault.

Import as a library from another script, or run directly for a smoke test:

    python3 excalidraw_build.py            # builds a 2-node demo to /tmp/_excalidraw_demo.excalidraw.md

Core helpers:
    make_text / make_rect / make_arrow / make_line   -> element factories
    instantiate(lib_elements, cx, cy, ...)           -> place a .excalidrawlib item
    load_library(path) / library_items(path)         -> read a .excalidrawlib
    gate_newlines(obj)                               -> strip \\n / \\r from ALL strings
    scene(elements)                                  -> wrap elements with required keys
    write_parsed_file(path, scene_dict)             -> write a valid .excalidraw.md

Read references/format.md for the WHY behind every rule enforced here.
"""

import copy
import json
import os
import re

# --- a shared counter so every element gets unique id / seed / versionNonce ---
_CTR = [1000]


def _next():
    _CTR[0] += 1
    return _CTR[0]


def nid(prefix="el"):
    return f"{prefix}{_next()}"


# Common palette (matches references/format.md).
COLORS = {
    "black": "#1e1e1e", "blue": "#1971c2", "blue_bg": "#a5d8ff",
    "orange": "#e8590c", "orange_bg": "#ffd8a8", "green": "#2f9e44",
    "green_bg": "#b2f2bb", "red": "#e03131", "gray": "#868e96",
    "gray_light": "#ced4da", "gray_bg": "#f1f3f5",
}


# ---------------------------------------------------------------------------
# Element factories  (all required fields pre-filled)
# ---------------------------------------------------------------------------
def _base(eltype, x, y, w, h, **over):
    n = _next()
    el = {
        "type": eltype, "id": over.pop("id", nid("e")),
        "x": x, "y": y, "width": w, "height": h, "angle": 0,
        "strokeColor": COLORS["black"], "backgroundColor": "transparent",
        "fillStyle": "solid", "strokeWidth": 2, "strokeStyle": "solid",
        "roughness": 1, "opacity": 100, "groupIds": [], "frameId": None,
        "roundness": None, "seed": n, "version": 1, "versionNonce": n,
        "isDeleted": False, "boundElements": [], "updated": 1,
        "link": None, "locked": False,
    }
    el.update(over)
    return el


def make_rect(x, y, w, h, stroke=None, bg=None, rounded=True, **over):
    return _base("rectangle", x, y, w, h,
                 strokeColor=stroke or COLORS["black"],
                 backgroundColor=bg or "transparent",
                 roundness={"type": 3} if rounded else None, **over)


def make_text(x, y, text, color=None, size=16, width=None, align="center", **over):
    # NOTE: text MUST be a single line. Newlines are stripped at write time, but
    # build single-line strings here and stack multiple text elements for multi-line labels.
    text = text.replace("\n", " ").replace("\r", " ")
    if width is None:
        width = int(len(text) * size * 0.62) + 8
    return _base("text", x, y, width, int(size * 1.25),
                 strokeColor=color or COLORS["black"],
                 fontSize=size, fontFamily=2,  # 2 = normal font (supports Korean; 1=Virgil does NOT)
                 text=text, textAlign=align, verticalAlign="top",
                 containerId=None, originalText=text, lineHeight=1.25,
                 baseline=int(size * 0.85), **over)


def make_text_centered(cx, y, text, **kw):
    """Make a text element horizontally centered on cx."""
    t = make_text(0, y, text, **kw)
    t["x"] = cx - t["width"] / 2
    return t


def make_arrow(x, y, dx, dy=0, color=None, width=2, dashed=False,
               start_head=None, end_head="arrow", **over):
    return _base("arrow", x, y, abs(dx), abs(dy),
                 strokeColor=color or COLORS["black"],
                 strokeWidth=width,
                 strokeStyle="dashed" if dashed else "solid",
                 roundness={"type": 2},
                 points=[[0, 0], [dx, dy]], lastCommittedPoint=None,
                 startBinding=None, endBinding=None,
                 startArrowhead=start_head, endArrowhead=end_head, **over)


def make_line(x, y, dx, dy=0, color=None, width=1, dashed=False, **over):
    return _base("line", x, y, abs(dx), abs(dy),
                 strokeColor=color or COLORS["gray_light"],
                 strokeWidth=width,
                 strokeStyle="dashed" if dashed else "solid",
                 points=[[0, 0], [dx, dy]], lastCommittedPoint=None,
                 startBinding=None, endBinding=None,
                 startArrowhead=None, endArrowhead=None, **over)


# ---------------------------------------------------------------------------
# Library (.excalidrawlib) handling
# ---------------------------------------------------------------------------
def load_library(path):
    return json.load(open(path, encoding="utf-8"))


def library_items(path):
    """Return the list of items. v1 files use key 'library' (each item = bare element
    array); newer files use 'libraryItems' (each item = {name, elements})."""
    d = load_library(path)
    return d.get("libraryItems") or d.get("library") or []


def item_elements(item):
    """Normalize an item to its element list, regardless of v1/v2 shape."""
    if isinstance(item, list):
        return [e for e in item if isinstance(e, dict)]
    return [e for e in item.get("elements", []) if isinstance(e, dict)]


def _bbox(els):
    xs = [e.get("x", 0) for e in els]
    ys = [e.get("y", 0) for e in els]
    xe = [e.get("x", 0) + e.get("width", 0) for e in els]
    ye = [e.get("y", 0) + e.get("height", 0) for e in els]
    return min(xs), min(ys), max(xe), max(ye)


def instantiate(lib_elements, cx, cy, scale=1.0, opacity=None, drop_text=True):
    """Deep-copy a library item and place it centered on (cx, cy).

    Returns (elements, bbox) where bbox = (minx, miny, maxx, maxy) of the placed item.
    Regenerates every id / groupId / seed; fixes containerId, boundElements,
    startBinding, endBinding so internal references stay consistent. Library items
    cannot be referenced by id in a scene — they must be copied like this.
    """
    src = [copy.deepcopy(e) for e in lib_elements if isinstance(e, dict)]
    dropped = set()
    if drop_text:
        dropped = {e["id"] for e in src if e.get("type") == "text"}
        src = [e for e in src if e.get("type") != "text"]
    if not src:
        return [], (cx, cy, cx, cy)

    minx, miny, maxx, maxy = _bbox(src)
    w, h = (maxx - minx) * scale, (maxy - miny) * scale
    tx, ty = cx - w / 2, cy - h / 2
    group = nid("grp")
    idmap = {e["id"]: nid("e") for e in src}

    out = []
    for e in src:
        e["id"] = idmap[e["id"]]
        e["x"] = tx + (e["x"] - minx) * scale
        e["y"] = ty + (e["y"] - miny) * scale
        if "width" in e:
            e["width"] *= scale
        if "height" in e:
            e["height"] *= scale
        if e.get("points"):
            e["points"] = [[px * scale, py * scale] for px, py in e["points"]]
        e["groupIds"] = [group]
        n = _next()
        e["seed"] = n
        e["version"] = 1
        e["versionNonce"] = n
        e["frameId"] = None
        if opacity is not None:
            e["opacity"] = opacity
        # fix references
        be = []
        for b in (e.get("boundElements") or []):
            bid = b.get("id")
            if bid in dropped:
                continue
            if bid in idmap:
                b["id"] = idmap[bid]
            be.append(b)
        e["boundElements"] = be
        cid = e.get("containerId")
        if cid in dropped:
            e["containerId"] = None
        elif cid in idmap:
            e["containerId"] = idmap[cid]
        for bk in ("startBinding", "endBinding"):
            bd = e.get(bk)
            if not bd:
                continue
            eid = bd.get("elementId")
            if eid in dropped:
                e[bk] = None
            elif eid in idmap:
                bd["elementId"] = idmap[eid]
        out.append(e)
    return out, (tx, ty, tx + w, ty + h)


# ---------------------------------------------------------------------------
# Scene assembly + safe write
# ---------------------------------------------------------------------------
def gate_newlines(obj):
    """Recursively replace \\n / \\r in EVERY string value with a space.

    This is the single most important safety step: the Obsidian Excalidraw plugin
    expands escaped newlines inside JSON string values into real newlines on file
    open, which corrupts the inline JSON and yields a blank canvas. Gate the whole
    object, not just `text`/`originalText`.
    """
    if isinstance(obj, dict):
        return {k: gate_newlines(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [gate_newlines(v) for v in obj]
    if isinstance(obj, str):
        return obj.replace("\n", " ").replace("\r", " ")
    return obj


def scene(elements, background="#ffffff"):
    return {
        "type": "excalidraw", "version": 2,
        "source": "https://github.com/zsviczian/obsidian-excalidraw-plugin",
        "elements": elements,
        "appState": {"gridSize": None, "viewBackgroundColor": background},
        "files": {},
    }


_DEFAULT_HEAD = (
    "---\n\nexcalidraw-plugin: parsed\ntags: [excalidraw]\n\n---\n"
    "==⚠  Switch to EXCALIDRAW VIEW in the MORE OPTIONS menu of this document. ⚠== "
    "You can decompress Drawing data with the command palette: "
    "'Decompress current Excalidraw file'. For more info check in plugin settings "
    "under 'Saving'\n\n"
)


def _extract_head(path):
    """If a file already exists, preserve its frontmatter + warning head (everything
    before '# Excalidraw Data'). Otherwise return a sensible default head."""
    if not os.path.exists(path):
        return _DEFAULT_HEAD
    s = open(path, encoding="utf-8").read()
    idx = s.find("# Excalidraw Data")
    if idx == -1:
        # Existing non-excalidraw or minimal file: keep frontmatter if any, else default.
        return _DEFAULT_HEAD
    head = s[:idx]
    return head if head.strip() else _DEFAULT_HEAD


def write_parsed_file(path, scene_dict):
    """Write scene_dict to `path` in the plugin's parsed format (uncompressed json).
    Gates newlines, asserts the JSON is valid, and preserves an existing file head.

    IMPORTANT: before editing an EXISTING drawing, read it first — the plugin may have
    re-serialized it to ```compressed-json``` with a populated ## Text Elements section.
    This writer always replaces the whole body, so reading first is about understanding
    intent / not clobbering unrelated content, not about format parsing.
    """
    scene_dict = gate_newlines(scene_dict)
    # fail loudly if anything still smells wrong
    assert json.dumps(scene_dict)  # serializable
    for e in scene_dict["elements"]:
        for k, v in e.items():
            if isinstance(v, str):
                assert "\n" not in v and "\r" not in v, f"newline left in {e.get('id')}.{k}"

    head = _extract_head(path)
    if not head.endswith("\n"):
        head += "\n"

    text_lines = [f'{e["text"]} ^{e["id"]}'
                  for e in scene_dict["elements"] if e.get("type") == "text"]
    text_block = "\n\n".join(text_lines)
    drawing = json.dumps(scene_dict, ensure_ascii=False, indent="\t")

    doc = (
        head
        + "# Excalidraw Data\n\n"
        + "## Text Elements\n" + text_block + "\n%%\n"
        + "## Drawing\n```json\n" + drawing + "\n```\n%%"
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(doc)

    # round-trip validation
    s = open(path, encoding="utf-8").read()
    m = re.search(r"```json\n(.*?)\n```", s, flags=re.DOTALL)
    assert m, "json block not found after write"
    json.loads(m.group(1))  # raises if invalid
    return path


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    els = []
    els.append(make_text(40, 30, "Demo: Client → Server", color=COLORS["black"], size=22, align="left"))
    a = make_rect(40, 90, 140, 70, stroke=COLORS["blue"], bg=COLORS["blue_bg"])
    b = make_rect(320, 90, 140, 70, stroke=COLORS["green"], bg=COLORS["green_bg"])
    els += [a, b]
    els.append(make_text_centered(110, 113, "Client", color=COLORS["black"], size=18))
    els.append(make_text_centered(390, 113, "Server", color=COLORS["black"], size=18))
    els.append(make_arrow(185, 125, 130, color=COLORS["black"]))
    els.append(make_text_centered(250, 100, "request", color=COLORS["blue"]))
    out = write_parsed_file("/tmp/_excalidraw_demo.excalidraw.md", scene(els))
    print("wrote", out, "with", len(els), "elements — open it in Obsidian Excalidraw view to confirm.")
