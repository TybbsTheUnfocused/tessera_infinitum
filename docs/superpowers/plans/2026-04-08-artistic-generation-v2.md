# Artistic Generation V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a high-fidelity generative engine with non-intersecting growth, layered composite rendering, and pure geometric fractals.

**Architecture:** Refactor `Engine` to use a 1-bit `collision_mask` for path growth. Implement a layered rendering pipeline that supports background (Grid) and foreground (Fractal) passes. Add Box and Quadratic Koch fractal generators.

**Tech Stack:** Python, NumPy, PIL (Pillow), vnoise.

---

### Task 1: Pure Geometric Fractals & Rule Library

**Files:**
- Modify: `generator/fractals.py`
- Test: `tests/test_fractals.py`

- [ ] **Step 1: Implement `get_box_fractal`**
    - Recursive squares with randomized exit points.
- [ ] **Step 2: Implement `get_quadratic_koch_island`**
    - 90-degree bumps with randomized directions (inward/outward).
- [ ] **Step 3: Add L-System Rule Library**
    - Dictionary containing `GOSPER`, `DRAGON`, `PLANT`, `SIERPINSKI` axioms/rules.
- [ ] **Step 4: Write tests for new fractals**
- [ ] **Step 5: Commit**

### Task 2: Collision-Aware Growth Logic

**Files:**
- Modify: `generator/engine.py`
- Test: `tests/test_engine.py`

- [ ] **Step 1: Add `collision_mask` initialization to `Engine`**
    - `np.zeros(self.size, dtype=bool)`
- [ ] **Step 2: Implement `_is_collision_free` helper**
    - Check if a segment path intersects `True` values in the mask.
- [ ] **Step 3: Implement `_render_lsystem_growth_mode`**
    - Multiple start points, step-by-step collision checks, and mask updates.
- [ ] **Step 4: Commit**

### Task 3: Refined Node Rendering (Outline & Fill)

**Files:**
- Modify: `generator/engine.py`
- Modify: `generator/palette.py`

- [ ] **Step 1: Add `darken_color` utility to `palette.py`**
- [ ] **Step 2: Refactor terminal rendering in `engine.py`**
    - Draw 1px black outline.
    - Draw 1-2px color border.
    - Draw lightened/darkened interior fill.
- [ ] **Step 3: Update node scaling parameters**
- [ ] **Step 4: Commit**

### Task 4: Composite Layering & CLI

**Files:**
- Modify: `generator/engine.py`
- Modify: `scripts/generate.py`

- [ ] **Step 1: Refactor `generate_universe` for multi-pass rendering**
    - Background (Grid) -> Foreground (Fractal).
    - Implement `mask_fractal_to_grid` logic.
- [ ] **Step 2: Update CLI arguments in `generate.py`**
    - `--lsystem-rule`, `--composite`, `--mask-to-grid`, `--node-fill-factor`.
- [ ] **Step 3: Generate 15 unique images for audit**
    - 5x Composite (Grid + Koch).
    - 5x L-System Growth (Dragon/Gosper).
    - 5x Box Fractals.
- [ ] **Step 4: Commit**
