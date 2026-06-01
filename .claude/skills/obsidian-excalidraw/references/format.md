# Obsidian Excalidraw file & library format reference

Deep reference for authoring `.excalidraw.md` drawings in an Obsidian vault. Grep this
file for a section (e.g. `## Element schemas`) rather than reading it whole.

## `.excalidraw.md` parsed-file anatomy

An Obsidian Excalidraw drawing is a Markdown file. In `parsed` mode the structure is:

```
---
excalidraw-plugin: parsed
tags: [excalidraw]
---
==⚠  Switch to EXCALIDRAW VIEW ... ⚠==      <- always-present warning (NOT an error)

# Excalidraw Data

## Text Elements
<text of element> ^<elementId>
<text of element> ^<elementId>
%%
## Drawing
```compressed-json        (or ```json — both are accepted)
{ ...scene JSON... }
```
%%
```

- The `==⚠ Switch to EXCALIDRAW VIEW ...==` line is shown in Markdown mode for EVERY
  drawing. It is not an error. The user just needs the Excalidraw view (More options
  `•••` → "Open as Excalidraw", or toggle Markdown/Excalidraw view).
- `## Text Elements` lists each text element's content followed by ` ^<id>`. Keep it in
  sync with the text elements in the scene JSON (same ids, same text).
- `%%` lines are Obsidian comment/fold markers wrapping the data block.

### compressed-json vs json
- The plugin reads BOTH ` ```compressed-json ` and ` ```json ` fenced blocks.
- It is fine to WRITE uncompressed ` ```json ` — the plugin re-compresses to
  `compressed-json` the next time the user opens the file in Excalidraw view.
- Therefore: a freshly hand-written minimal file changes shape after first open. Always
  re-read the file right before editing an existing drawing.

## CRITICAL: the `\n` corruption bug

The plugin expands escaped `\n` inside JSON string values into REAL newlines when the
file is opened. A real newline inside a JSON string is invalid JSON → the whole drawing
fails to parse → blank canvas.

- Symptom: file opens but the canvas is empty (only the warning text shows in Markdown).
- Diagnostic tell: the on-disk JSON is a few bytes SHORTER than what you wrote (each
  `\n` (2 chars) collapses to one newline char), and `python3 -m json.tool` reports
  "Invalid control character".
- It affects every string field, and `text` + `originalText` are duplicated, so a single
  2-line label corrupts in (at least) 2 places.
- FIX / PREVENTION: never emit `\n` or `\r` in any string value. For multi-line labels,
  use several single-line text elements stacked vertically. `gate_newlines()` in
  `excalidraw_build.py` enforces this across the entire object — always run it.

Note: inline JSON validation is necessary but NOT sufficient. A file can pass
`json.tool` at write time and still break on the next plugin open (that is exactly the
`\n` bug). The only complete check is the user reopening it in Excalidraw view.

## Scene-level required keys

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "https://github.com/zsviczian/obsidian-excalidraw-plugin",
  "elements": [ ... ],
  "appState": { "gridSize": null, "viewBackgroundColor": "#ffffff" },
  "files": {}
}
```
Missing `appState` or `files` can cause a parse/no-render failure.

## Element schemas (required fields)

All elements share this base set — omitting fields tends to crash/no-render rather than
degrade gracefully:

`type, id, x, y, width, height, angle, strokeColor, backgroundColor, fillStyle,
strokeWidth, strokeStyle, roughness, opacity, groupIds, frameId, roundness, seed,
version, versionNonce, isDeleted, boundElements, updated, link, locked`

Per-type extras:
- **rectangle / ellipse / diamond**: `roundness: {"type":3}` for rounded corners (or null).
- **text**: `fontSize, fontFamily, text, textAlign, verticalAlign, containerId,
  originalText, lineHeight, baseline`.
  - `fontFamily`: **2 = normal** (supports Korean). 1 = Virgil/hand-drawn (does NOT render
    Korean). 3 = code.
  - Keep `text` and `originalText` identical and single-line.
  - For unbound static labels set `containerId: null` (recommended — bound text is the #1
    cause of disappearing labels).
- **arrow / line**: `points: [[0,0],[dx,dy]], lastCommittedPoint, startBinding,
  endBinding, startArrowhead, endArrowhead`. The element's `x,y` is the start point;
  `points` are relative. For a leftward/return arrow use a negative `dx`.
  - Keep `startBinding`/`endBinding` null and compute endpoints from the actual placed
    bounding boxes — bindings are fragile and you cannot preview the render.
  - `roundness: {"type":2}` for arrows.

## Color palette (used by the helper)

| name | hex | name | hex |
|------|-----|------|-----|
| black | #1e1e1e | red | #e03131 |
| blue | #1971c2 | blue_bg | #a5d8ff |
| orange | #e8590c | orange_bg | #ffd8a8 |
| green | #2f9e44 | green_bg | #b2f2bb |
| gray | #868e96 | gray_light | #ced4da |

## `.excalidrawlib` library format

```json
{ "type": "excalidrawlib", "version": 1, "library": [ [ ...elements... ], ... ] }
```
- v1 uses key `library`; each item is a bare ARRAY of elements (no name).
- v2 uses key `libraryItems`; each item is `{ "name": ..., "elements": [...] }`.
- Items often bundle a graphic plus a built-in text label (e.g. the "CDN" item is a
  cloud/nodes graphic + a "CDN" text element).
- Use `inspect_library.py` to list items and identify them by their text labels.

### Instancing a library item (the only way to use it)
A scene cannot reference a library item by id; copy its elements in. For each instance:
1. Deep-copy the item's elements.
2. (Usually) drop the built-in text element and add your own caption — keeps labels
   consistent (e.g. Korean) and avoids the item's English text.
3. Build an `oldId -> newId` map and remap every reference:
   - `id`
   - `containerId`
   - each entry in `boundElements` (`{id,type}`)
   - `startBinding.elementId`, `endBinding.elementId`
   - drop references that point to removed (text) elements; set to null / filter out.
4. Regenerate `seed` and `versionNonce` per element.
5. Assign a single fresh `groupIds: [groupId]` so the instance moves as a unit.
6. Offset (and optionally scale) coordinates and `points` so the item's bounding box is
   centered on the target `(cx, cy)`.

`instantiate()` in `excalidraw_build.py` does all of this and returns `(elements, bbox)`.

## Default vault locations (this user)

- Drawings: `Atlas/Visuals/*.excalidraw.md`
- Libraries (vault root): `system-design.excalidrawlib`, `software-architecture.excalidrawlib`
  - In `system-design.excalidrawlib`, item **[20]** is the **CDN** icon. Others include
    server, Application server, Cache, DNS, Load Balancer, Message Q, cloud, Web Application.
- Plugin data: `.obsidian/plugins/obsidian-excalidraw-plugin/`

## Shell note
`cd` into the iCloud vault path can trigger a noisy shell profile (`GVM_ROOT not set`)
that may abort a compound command. Prefer absolute paths in commands and avoid `cd`.
