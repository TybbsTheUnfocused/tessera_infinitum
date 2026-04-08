# Artistic Generation V2: Advanced Generative Art Architecture

## Goal
Implement a high-fidelity generative engine capable of creating clean, non-intersecting L-systems, composite grid/fractal layers, and pure geometric fractals (Box and Quadratic Koch). The focus is on "Structured Complexity"—avoiding visual "messes" through collision detection and rigid geometric constraints.

## 1. Collision-Aware Growth Engine (`lsystem_growth`)
To solve the "V-shape" and "messy soup" issues, we will move from static paths to a growth-based model.

### Logic
- **Multiple Seed Points**: Generate `N` (default 5-10) random starting points on the 2048x2048 canvas.
- **Collision Mask**: Maintain a 1-bit NumPy `collision_mask`.
- **Step-by-Step Growth**: For each L-system agent:
    - Before drawing a segment, check the `collision_mask`.
    - If a collision is detected (or image boundary reached), the agent stops or attempts a random 90/45 degree turn.
    - Successfully drawn segments are marked in the `collision_mask` with a buffer (e.g., `line_width * 2`) to ensure paths don't touch.
- **Rule Diversity**: Replace hardcoded rules with a library of high-quality L-system definitions (Gosper, Dragon, Sierpinski, Plant).

## 2. Refined Square/Node Rendering
Fixes for "too large" and "low artistic value" terminals.

### Logic
- **Scaling**: Reduce base `node_size` scale (e.g., 2-8px instead of 10-20px).
- **Layered Rendering**:
    - **Outline**: 1-2px border using the standard palette color.
    - **Fill**: A luminance-shifted version (lighten or darken) of the outline color.
- **Node Sync**: Nodes only appear at vertices where a segment was successfully drawn (post-collision check).

## 3. Composite Rendering (Layered Passes)
Allows mixing "Grid" and "Fractal" modes.

### Logic
- **Background Pass**: Optional `grid` pass (Rectilinear Mosaic).
- **Foreground Pass**: `lsystem_growth` or `fractal_pure` pass.
- **Masking Option**: A parameter `mask_fractal_to_grid` will allow fractals to *only* grow inside existing grid cells, creating a highly integrated, architectural look.

## 4. Pure Geometric Fractals (`fractal_pure`)
Deterministic but randomized geometric structures.

### Box Fractal
- Recursive squares within squares. 
- **Randomness**: Random exit points for the recursion and randomized "nesting" depths per quadrant.

### Quadratic Koch Island
- Straight-line segments with 90-degree "bumps."
- **Randomness**: Randomly flip the direction of the "bump" (inward vs. outward) at each segment to create unique, non-uniform islands.

## 5. Artistic Constraints & Quality Control
- **White Background**: Mandatory for high contrast.
- **Clutter Filtering**: Segments < 3px are ignored.
- **Vectorized Color**: All coloring remains Pebble-safe and uses the `periodic` mapping for fluid transitions.
