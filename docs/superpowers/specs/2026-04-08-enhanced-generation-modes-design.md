# Enhanced Generation Modes Design

## Goal
Implement two new high-fidelity, structured generation modes to increase the artistic diversity and quality of the Perlin-Infinite engine. These modes focus on clean, geometric aesthetics ("Digital Mosaic" and "Circuitry") to provide a professional, designed look suitable for Pebble watchfaces.

## Mode 1: Rectilinear Cellular Grid (`grid`)
This mode generates a discrete mosaic of blocks influenced by the Perlin noise field.

### Architecture
- **Grid Logic**: Divide the 2048x2048 canvas into a grid of `grid_res` x `grid_res` cells (default 64x64).
- **Visibility Logic**: Sample the `noise_field` at each cell's center. A cell is only rendered if `noise_value > grid_threshold` (default 0.4).
- **Aesthetics**:
    - `cell_padding`: Float [0, 1] controlling the gap between cells.
    - `cell_stroke`: Width in pixels for a dark outline around each block to provide high-definition "blueprint" styling.
- **Coloring**:
    - Supports all standard palettes.
    - Color is mapped to each cell based on its `(i, j)` coordinate for global gradients or `noise_value` for localized clusters.

## Mode 2: Geometric L-System with Terminals (`lsystem_geom`)
This mode creates a structured "Circuit" or "Molecular" look by connecting discrete nodes with clean paths.

### Architecture
- **Vertex Logic**: Use the L-System path generator. Apply noise-driven distortion *only* to the vertices.
- **Path Logic**: Draw straight-line segments between distorted vertices to maintain geometric clarity.
- **Terminals (Nodes)**:
    - At every vertex, draw a geometric shape (Circle, Square, or Diamond).
    - **Size Modulation**: Terminal size is scaled by the local `noise_value`.
    - **Clutter Filtering**: Segments compressed by distortion to < 5px are skipped to prevent "messy" overdraw.
- **Color Harmony**:
    - **Synchronized Progress**: Segments and their attached nodes share the same color mapping index to prevent discontinuity.
    - **Accent Coloring**: Nodes are rendered using a luminance-offset version of the line color (lighter or darker) to highlight them as "hubs" without breaking the palette's coherence.

## Design Goals: Quality & Artistic Value
- **Clarity**: Both modes use rigid geometric primitives (Rectangles, Circles) to ensure the output looks intentional and clean even at high distortion settings.
- **Diversity**: By parameterizing `grid_res`, `cell_padding`, and `terminal_shape`, we can generate everything from sparse "circuit boards" to dense "mosaics."
- **High Contrast**: White background is enforced, with `cell_stroke` providing sharp definition for color blocks.

## Implementation Strategy
- Refactor `Engine.generate_universe` to branch based on a `mode` parameter.
- Add `_render_grid_mode` and `_render_lsystem_geom_mode` helper methods to `Engine`.
- Update the CLI in `scripts/generate.py` to support these new modes and their specific parameters.
