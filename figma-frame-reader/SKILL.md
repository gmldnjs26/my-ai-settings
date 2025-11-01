---
name: figma-frame-reader
description: Automatically read large Figma pages frame-by-frame when the page is too large to read at once. This skill should be used when (1) get_design_context or get_figjam fails due to page size being too large, (2) the user provides a Figma page URL or nodeId and requests code generation, or (3) the user explicitly asks to read an entire Figma page or all frames.
---

# Figma Frame Reader

## Overview

This skill enables reading large Figma pages by automatically splitting them into individual frames when the page is too large to read at once. It uses the Figma MCP tools to first extract metadata, then reads each frame individually, allowing Claude to understand the complete design structure and generate code accurately.

## When to Use

Use this skill when:
1. **get_design_context or get_figjam returns an error** indicating the output is too large
2. **User provides a Figma page URL or nodeId** and requests code generation or design implementation
3. **User explicitly asks to read an entire Figma page** or all frames
4. **Automatic fallback**: When initial design read fails due to size constraints

## Workflow

### Step 1: Attempt Direct Read First

Before using the frame-by-frame approach, always attempt to read the design directly using the standard MCP tools:

- For design files: Use `mcp__figma-mcp__get_design_context` with the provided nodeId
- For FigJam files: Use `mcp__figma-mcp__get_figjam` with the provided nodeId

If the read succeeds, proceed directly with code generation or analysis. Only continue to Step 2 if the direct read fails due to size constraints.

### Step 2: Extract Page Metadata

When the direct read fails, use `mcp__figma-mcp__get_metadata` to get the page structure in XML format:

```
mcp__figma-mcp__get_metadata with nodeId (page-level ID like "0:1" or specific node)
```

This returns:
- All frame node IDs within the page
- Frame names and positions
- Overall page structure

**Important**: Extract all FRAME-type node IDs from the metadata. These are the top-level frames that should be read individually.

### Step 3: Read Each Frame

For each frame node ID extracted from the metadata:

1. Call `mcp__figma-mcp__get_design_context` with each frame's nodeId
2. Store the design context for each frame
3. Note any Code Connect mappings for component integration

**Optimization**: When there are many frames (>5), consider:
- Reading frames in parallel using multiple tool calls in a single message
- Prioritizing frames by name (e.g., read "Desktop" before "Mobile variants")
- Asking the user which frames to focus on if there are many unrelated frames

### Step 4: Synthesize Understanding

After reading all frames:

1. **Analyze the complete design system** across all frames:
   - Identify reusable components
   - Extract color schemes, typography, spacing patterns
   - Understand layout structures and responsive patterns

2. **Build a mental model** of the design:
   - How frames relate to each other (e.g., different pages, variants, states)
   - Component hierarchy and relationships
   - Design patterns and conventions used

3. **Do NOT show raw data to the user** - they only want the generated code, not the frame data itself

### Step 5: Generate Code

Based on the complete understanding from all frames:

1. **Generate cohesive code** that implements the entire design:
   - Create reusable components for repeated patterns
   - Implement proper styling with extracted design tokens
   - Structure code logically based on the frame relationships

2. **Use Code Connect mappings** when available to match existing codebase components

3. **Follow the project's conventions**:
   - Check for framework type (React, Vue, etc.) from context
   - Match existing code style and patterns
   - Use appropriate CSS methodology (CSS modules, Tailwind, styled-components, etc.)

## Error Handling

If errors occur during the frame-by-frame reading:

1. **Individual frame read failures**: Skip problematic frames and continue with others, noting what was skipped
2. **Metadata read failures**: Fall back to asking the user to provide specific frame URLs or nodeIds
3. **Too many frames**: Ask the user which frames are most important to focus on

## Example Usage

**User request**: "Generate code from this Figma page: https://figma.com/design/abc123/Project?node-id=0-1"

**Workflow execution**:
1. Extract nodeId "0:1" from URL
2. Attempt `get_design_context` with nodeId "0:1"
3. If size error occurs, call `get_metadata` with nodeId "0:1"
4. Extract frame nodeIds from metadata (e.g., "1:2", "1:5", "1:8")
5. Read each frame using `get_design_context`:
   - Call for nodeId "1:2" (e.g., "Homepage")
   - Call for nodeId "1:5" (e.g., "Product Page")
   - Call for nodeId "1:8" (e.g., "Checkout")
6. Synthesize understanding of the complete multi-page application
7. Generate cohesive code implementing all pages with shared components

## Best Practices

1. **Be selective**: If there are many frames, ask the user which ones to focus on
2. **Extract design tokens**: Look for consistent colors, spacing, typography across frames
3. **Identify component patterns**: Reuse component code across frames when patterns are similar
4. **Preserve relationships**: Maintain the logical connection between related frames (e.g., page states)
5. **Silent processing**: Don't show frame data to users - they only want the final generated code

## Notes

- This skill works with both regular Figma design files and FigJam files
- For FigJam files, use `get_figjam` instead of `get_design_context` in the workflow
- Variable definitions can be retrieved separately using `get_variable_defs` for design tokens
- Code Connect mappings from `get_code_connect_map` help align with existing codebases
