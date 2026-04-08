# Hilbert Fill and Generation Enhancements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement overlapping Hilbert curves with region filling and fix deterministic seeding.

**Architecture:** Use `scipy.ndimage.binary_fill_holes` on a rasterized mask of two distorted Hilbert paths to identify enclosed regions. Fill these regions with lighter shades of the path colors. Ensure all noise generation is seeded.

**Tech Stack:** Python, NumPy, SciPy, Pillow, vnoise.

---

### Task 1: Fix Seeding in Noise Generation (Verification)

**Files:**
- Modify: `generator/noise.py` (Already done, verify)
- Modify: `generator/engine.py` (Already done, verify)
- Test: `tests/test_noise.py`

- [ ] **Step 1: Update noise tests to verify determinism**
- [ ] **Step 2: Run tests**
- [ ] **Step 3: Commit**

### Task 2: Implement Region Filling Logic

**Files:**
- Modify: `generator/engine.py`
- Test: `tests/test_engine.py`

- [ ] **Step 1: Add `scipy.ndimage` import to `engine.py`**
- [ ] **Step 2: Implement `_generate_filled_mask` helper in `Engine`**
- [ ] **Step 3: Update `generate_universe` to handle `hilbert_fill` mode**
    - Generate two paths with different seeds.
    - Create binary mask and fill holes.
    - Draw filled regions with lightened colors.
    - Draw outlines on top.
- [ ] **Step 4: Write test for filled generation**
- [ ] **Step 5: Commit**

### Task 3: Enhance Color Palettes & UI

**Files:**
- Modify: `generator/palette.py`
- Modify: `scripts/generate.py`

- [ ] **Step 1: Add `lighten_color` utility to `palette.py`**
- [ ] **Step 2: Add `--hilbert-fill` argument to `generate.py`**
- [ ] **Step 3: Commit**

### Task 4: Final Validation and Batch Generation

**Files:**
- Create: `generations/` (Already exists, but will populate with new batch)

- [ ] **Step 1: Generate 15 unique images with new parameters**
    - 5x Rainbow with Fill
    - 5x Sunset with Fill
    - 5x Forest with Fill
- [ ] **Step 2: Verify all 15 images are unique**
- [ ] **Step 3: Commit**
