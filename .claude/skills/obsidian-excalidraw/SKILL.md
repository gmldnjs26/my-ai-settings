---
name: obsidian-excalidraw
description: Create and edit Excalidraw drawings (.excalidraw.md) inside an Obsidian vault, including diagrams built from reusable .excalidrawlib library icons (e.g. CDN/server/architecture shapes). This skill should be used when drawing or editing an Excalidraw canvas in Obsidian, generating flow/architecture diagrams as Excalidraw, or reusing icons from an Excalidraw library. Also covers the common failure where a drawing opens to a blank canvas.
---

# Obsidian Excalidraw

## Overview

Authoring Excalidraw drawings inside Obsidian is full of non-obvious pitfalls (a newline
bug that blanks the canvas, a file format the plugin silently rewrites, and library icons
that can only be used by copying). This skill provides a tested Python helper, a library
inspector, and a deep-format reference so a drawing is produced correctly on the first try.

## CRITICAL rules (do not skip)

1. **Never put `\n` or `\r` in any string value.** The plugin expands escaped newlines
   inside JSON strings into real newlines on open, which corrupts the inline JSON and
   produces a blank canvas. Build single-line text strings; for multi-line labels, stack
   multiple text elements. Always run `gate_newlines()` over the whole scene before writing
   (the helper's `write_parsed_file()` does this automatically).

2. **Re-read the file immediately before editing an existing drawing.** After the user
   opens a drawing in Excalidraw view, the plugin re-serializes it to ` ```compressed-json `
   and adds a populated `## Text Elements` section. Do not assume it is still the
   ` ```json ` you last wrote — read it, understand it, then replace the body.

3. **Validate, then ask the user to reopen.** After writing, the helper validates the JSON.
   But inline validation is NOT render-proof (the newline bug passes write-time validation
   and still breaks on open). Always end by telling the user to open/reopen the file in
   Excalidraw view (More options `•••` → "Open as Excalidraw") to confirm it renders.

4. The `==⚠ Switch to EXCALIDRAW VIEW ...==` line in the file is **not an error** — it is
   the normal Markdown-mode placeholder present in every drawing.

## Workflow

1. **Orient.** If editing, read the target `.excalidraw.md` to see its current on-disk
   format and content. New drawings live under `Atlas/Visuals/`.

2. **(If using library icons) inspect the library.** List items and find the icon by its
   text label:
   ```bash
   python3 scripts/inspect_library.py system-design.excalidrawlib
   python3 scripts/inspect_library.py system-design.excalidrawlib --index 20   # dump item 20 (CDN)
   ```
   Libraries are at the vault root (`system-design.excalidrawlib`,
   `software-architecture.excalidrawlib`).

3. **Build the scene** with `scripts/excalidraw_build.py` (import it). Use the element
   factories and `instantiate()` for library icons:
   ```python
   import sys; sys.path.insert(0, "scripts")
   from excalidraw_build import (make_rect, make_arrow, make_text_centered, COLORS,
                                 library_items, item_elements, instantiate,
                                 scene, write_parsed_file)

   lib = library_items("system-design.excalidrawlib")
   cdn_els, cdn_bbox = instantiate(item_elements(lib[20]), cx=500, cy=200, scale=1.4)

   els = [*cdn_els,
          make_text_centered(500, cdn_bbox[3] + 8, "CDN 서버", color=COLORS["orange"]),
          make_arrow(190, 200, 130, color=COLORS["black"])]

   write_parsed_file("Atlas/Visuals/My Diagram.excalidraw.md", scene(els))
   ```
   - `instantiate(elements, cx, cy, scale=, opacity=, drop_text=True)` copies a library item,
     centers it on `(cx,cy)`, regenerates ids/groupIds, fixes bindings, and returns
     `(elements, bbox)`. It drops the icon's built-in text by default — add your own caption.
   - Compute arrow endpoints from the returned bboxes; keep arrow/text bindings null.

4. **Write** with `write_parsed_file(path, scene(els))` — it gates newlines, writes the
   parsed format (`# Excalidraw Data` / `## Text Elements` / `## Drawing` + ` ```json `),
   and round-trip-validates the JSON. A fallback manual check: `python3 -m json.tool`.

5. **Confirm.** Tell the user to open/reopen in Excalidraw view; offer to adjust layout
   (icon size, spacing, caption positions) since the render cannot be previewed here.

## Resources

- `scripts/excalidraw_build.py` — element factories (`make_rect/make_text/make_arrow/
  make_line`, `make_text_centered`), `instantiate()` for library icons, `gate_newlines()`,
  `scene()`, and `write_parsed_file()`. Run it directly for a smoke-test demo.
- `scripts/inspect_library.py` — list/dump items in a `.excalidrawlib` file.
- `references/format.md` — deep reference: file anatomy, the `\n` bug, scene/element
  required-field schemas, color palette, library format, and the instancing algorithm.
  Grep it for a section (e.g. `## Element schemas`) rather than reading it whole.

### Shell note
Avoid `cd` into the iCloud vault path — it can trigger a noisy shell profile
(`GVM_ROOT not set`) that aborts compound commands. Use absolute paths instead.
