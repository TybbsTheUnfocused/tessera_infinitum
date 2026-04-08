# Adaptive Density & Segmentation Design

## Goal
Ensure that all generated 2048x2048 canvases contain a maximum of 50% pure white pixels. This will be achieved through a deterministic, iterative rendering pipeline that uses canvas segmentation and targeted sub-canvas generation to intelligently fill voids while maintaining color cohesion and structural beauty.

## 1. The Iterative Rendering Pipeline
The `Engine.generate_universe` method will be refactored from a single-pass function into a `while` loop:
- **Condition**: `while whitespace_percentage > 0.50 and iterations < MAX_PASSES`
- **Evaluation**: After each pass, the master canvas is converted to a NumPy array to calculate the exact ratio of `[255, 255, 255]` pixels.

## 2. Canvas Segmentation & Branching (The Base Passes)
Instead of starting with a single massive fractal, the engine will build the image in structured layers.
- **Regional Fills**: The canvas is logically split into regions (e.g., a 2x2 or 3x3 grid). Within each region, a randomly selected generative pattern (Box, Koch, or L-System) is rendered into a transparent sub-canvas bounded precisely by that region's dimensions, then pasted onto the master.
- **The Connector Pass**: Once the regions are filled, a "connecting pattern" (e.g., a large, sparse `lsystem_growth` or `hilbert_koch`) is generated across the full 2048x2048 canvas. This weaves the disparate regional blocks together into a cohesive whole.

## 3. Target-Aware Placement (The Refinement Passes)
If the Segmentation and Connector passes leave the canvas with > 50% white space, the engine enters the Targeted Placement phase.
- **Void Detection**: Use `scipy.ndimage.label` on the binary whitespace mask to find the largest contiguous blocks of empty pixels.
- **Bounding Box Extraction**: Calculate the exact bounding box `(min_x, min_y, max_x, max_y)` of the largest void.
- **Sub-Canvas Generation**: A new generative pattern is selected. It is given a `size` matching the void's bounding box and is rendered onto a transparent (`RGBA`) sub-canvas.
- **Overlay**: The sub-canvas is pasted onto the master canvas exactly over the void.
- **Iteration**: This process repeats, targeting the *next* largest void, until the 50% density threshold is met.

## 4. Artistic Constraints
- **Strict Color Cohesion**: Every iterative pass, whether a regional block, a connector, or a void-filler, MUST use the exact same `palette` (e.g., `deep_sea`) selected at the start of the generation.
- **Transparency**: All sub-canvases must use a transparent background (`(0, 0, 0, 0)`) so that when they are pasted, they only add their drawn lines and filled shapes, preserving any existing background grids or lines beneath them.
- **Diversity**: The choice of algorithm for each region/void is randomized (weighted to ensure a mix of L-systems and pure fractals).
