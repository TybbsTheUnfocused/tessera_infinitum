# Enhanced Generation Modes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement `grid` and `lsystem_geom` generation modes to provide clean, structured, and visually striking artwork.

**Architecture:** Refactor the `Engine` to branch rendering logic based on a `mode` parameter. Use rigid geometric primitives (Rectangles, Circles) to maintain artistic quality and prevent "messy" overlaps.

**Tech Stack:** Python, NumPy, PIL (Pillow), vnoise.

---

### Task 1: Refactor Engine for Mode Support

**Files:**
- Modify: `generator/engine.py`
- Test: `tests/test_engine.py`

- [ ] **Step 1: Add `mode` parameter to `generate_universe`**
- [ ] **Step 2: Create empty stubs for `_render_grid_mode` and `_render_lsystem_geom_mode`**
- [ ] **Step 3: Update `generate_universe` to branch into these stubs**
- [ ] **Step 4: Commit**

### Task 2: Implement Rectilinear Grid Mode (`grid`)

**Files:**
- Modify: `generator/engine.py`
- Test: `tests/test_engine.py`

- [ ] **Step 1: Implement `_render_grid_mode` logic**
    - Iterate through grid coordinates.
    - Sample noise at cell centers.
    - Respect `grid_threshold`, `cell_padding`, and `cell_stroke`.
- [ ] **Step 2: Add color mapping logic (Coordinate-based vs Noise-based)**
- [ ] **Step 3: Write test case for `grid` mode**
- [ ] **Step 4: Commit**

### Task 3: Implement Geometric L-System Mode (`lsystem_geom`)

**Files:**
- Modify: `generator/engine.py`
- Test: `tests/test_engine.py`

- [ ] **Step 1: Implement `_render_lsystem_geom_mode` logic**
    - Draw straight segments between distorted vertices.
    - Implement clutter filtering (skip < 5px segments).
- [ ] **Step 2: Add Node/Terminal rendering**
    - Support Circle and Square shapes.
    - Implement noise-driven size modulation and thresholding.
- [ ] **Step 3: Implement Synchronized Color Harmony and Accent Offset**
- [ ] **Step 4: Write test case for `lsystem_geom` mode**
- [ ] **Step 5: Commit**

### Task 4: CLI Update and Batch Generation

**Files:**
- Modify: `scripts/generate.py`

- [ ] **Step 1: Add new CLI arguments**
    - `--mode`, `--grid-res`, `--grid-threshold`, `--cell-padding`, `--cell-stroke`, `--terminal-shape`, `--node-threshold`.
- [ ] **Step 2: Generate 15 unique images**
    - 5x `grid` mode (varying resolutions/paddings).
    - 5x `lsystem_geom` mode (Circle terminals).
    - 5x `lsystem_geom` mode (Square terminals).
- [ ] **Step 3: Verify uniqueness and clean output**
- [ ] **Step 4: Commit**
