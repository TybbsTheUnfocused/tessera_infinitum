# Adaptive Density & Segmentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ensure all generated canvases have <= 50% white space via an adaptive void-filling loop, and introduce an optional `segmented` generation mode. Existing modes must be perfectly preserved as the base layer.

**Architecture:** 
1. `Engine.generate_universe` will render the requested base mode (e.g., `fractal_pure`, `lsystem_growth`, or `segmented`).
2. A `while` loop checks the white pixel ratio. If > 0.50, `scipy.ndimage.label` identifies the largest empty bounding box.
3. A random pattern is generated within that bounding box on a transparent layer and pasted over the void.
4. The `segmented` mode explicitly divides the canvas into regions, populates them independently, and weaves them together.

**Tech Stack:** Python, NumPy, SciPy (`scipy.ndimage`), PIL.

---

### Task 1: Whitespace Evaluation & Void Detection

**Files:**
- Modify: `generator/engine.py`

- [ ] **Step 1: Implement `_get_whitespace_ratio` helper**
    - Convert PIL Image to NumPy array.
    - Calculate ratio of exactly `[255, 255, 255]` pixels.
- [ ] **Step 2: Implement `_get_largest_void` helper**
    - Convert image to boolean mask (True if white).
    - Use `scipy.ndimage.label` and `scipy.ndimage.find_objects`.
    - Return the bounding box `(x1, y1, x2, y2)` of the largest contiguous void.
- [ ] **Step 3: Commit**

### Task 2: Implement Adaptive Void Filling

**Files:**
- Modify: `generator/engine.py`

- [ ] **Step 1: Refactor `generate_universe` into a density loop**
    - Generate the base layer as requested by `params`.
    - `while _get_whitespace_ratio(img) > 0.50 and iterations < 5:`
- [ ] **Step 2: Implement sub-canvas rendering in the loop**
    - Get largest void bounding box.
    - Randomly select a mode (`fractal_pure` or `lsystem_growth`) and style parameters.
    - Create a transparent PIL Image matching the void size.
    - Render the pattern onto the transparent image.
    - Paste onto the main master canvas.
- [ ] **Step 3: Commit**

### Task 3: Implement Optional Segmented Mode

**Files:**
- Modify: `generator/engine.py`

- [ ] **Step 1: Implement `_render_segmented_mode`**
    - Subdivide the 2048x2048 canvas into a 2x2 or 3x3 grid of sub-regions.
    - For each region, create a transparent sub-canvas.
    - Generate a random pattern (Box, Koch, Dragon, etc.) scaled to the sub-canvas.
    - Paste all sub-canvases onto the master.
- [ ] **Step 2: Add Connector Pass to Segmented Mode**
    - Generate a large, sparse `lsystem_growth` or `hilbert_koch` across the full master canvas to weave the segments together.
- [ ] **Step 3: Commit**

### Task 4: CLI Updates and Verification

**Files:**
- Modify: `scripts/generate.py`
- Modify: `tests/test_engine.py`

- [ ] **Step 1: Add `segmented` to the choices for `--mode`**
- [ ] **Step 2: Add a test asserting that generated universes always have <= 50% whitespace**
- [ ] **Step 3: Run the export script (`scripts/export_all.py`) to verify the new segmented mode and adaptive density kicks in on sparse generations**
- [ ] **Step 4: Commit**
