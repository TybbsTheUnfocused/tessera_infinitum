# Orchestrator Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the three-script pipeline (orchestrate → slice → upload) and GitHub Actions workflow that generates, crops, and deploys hourly generative art to Cloudflare R2.

**Architecture:** Three independent scripts communicate only through files in a shared `--output-dir`. `orchestrate.py` renders a master canvas from a seeded recipe. `slice.py` converts it to an indexed PNG and pre-crops platform-sized byte-array slices. `upload.py` pushes everything to R2. A GitHub Actions cron workflow chains them.

**Tech Stack:** Python 3.13, uv, NumPy, Pillow, boto3, GitHub Actions

**Spec:** `docs/superpowers/specs/2026-04-09-orchestrator-pipeline-design.md`

---

## File Map

| Action | Path | Responsibility |
|--------|------|---------------|
| Create | `scripts/orchestrate.py` | Seed derivation, recipe selection, rendering, metadata output |
| Create | `scripts/slice.py` | Indexed-PNG conversion, platform cropping, byte-array encoding |
| Create | `scripts/upload.py` | R2 upload via boto3 S3-compatible API |
| Create | `tests/test_orchestrate.py` | Tests for seed derivation, recipe selection, metadata output |
| Create | `tests/test_slice.py` | Tests for indexed-PNG conversion, cropping, byte-array encoding |
| Create | `tests/test_upload.py` | Tests for upload path construction and dry-run |
| Create | `.github/workflows/generate.yml` | Hourly cron + manual dispatch workflow |
| Modify | `pyproject.toml` | Add `boto3` dependency |
| Modify | `.gitignore` | Add `output/` directory |

---

### Task 1: Recipe Data Module

Extract the recipe deck into a testable data structure before building the orchestrator script.

**Files:**
- Create: `scripts/recipes.py`
- Create: `tests/test_recipes.py`

- [ ] **Step 1: Write failing tests for recipe data**

```python
# tests/test_recipes.py
import numpy as np
from scripts.recipes import RECIPES, STYLES, get_recipe_by_name, select_recipe


def test_recipe_count():
    assert len(RECIPES) == 19


def test_all_recipes_have_required_keys():
    required = {'name', 'mode', 'params', 'weight'}
    for recipe in RECIPES:
        missing = required - set(recipe.keys())
        assert not missing, f"Recipe {recipe.get('name', '?')} missing keys: {missing}"


def test_all_modes_are_valid():
    valid_modes = {'grid', 'lsystem_growth', 'fractal_pure', 'segmented'}
    for recipe in RECIPES:
        assert recipe['mode'] in valid_modes, f"Invalid mode: {recipe['mode']}"


def test_weights_are_positive():
    for recipe in RECIPES:
        assert recipe['weight'] > 0, f"Recipe {recipe['name']} has non-positive weight"


def test_get_recipe_by_name():
    recipe = get_recipe_by_name('grid_rect')
    assert recipe is not None
    assert recipe['mode'] == 'grid'


def test_get_recipe_by_name_missing():
    assert get_recipe_by_name('nonexistent') is None


def test_select_recipe_deterministic():
    rng = np.random.RandomState(42)
    r1 = select_recipe(rng)
    rng = np.random.RandomState(42)
    r2 = select_recipe(rng)
    assert r1['name'] == r2['name']


def test_select_recipe_respects_weights():
    # With enough samples, high-weight recipes should appear more often
    counts = {}
    for i in range(10000):
        rng = np.random.RandomState(i)
        r = select_recipe(rng)
        counts[r['name']] = counts.get(r['name'], 0) + 1
    # segmented has weight 3.0, grid_rect has weight 1.0
    assert counts.get('segmented', 0) > counts.get('grid_rect', 0)


def test_styles_list():
    assert len(STYLES) == 8
    assert 'deep_sea' in STYLES
    assert 'pebble' in STYLES
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=. uv run pytest tests/test_recipes.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.recipes'`

- [ ] **Step 3: Implement recipes.py**

```python
# scripts/recipes.py
"""
Recipe deck for the Tessera ad Infinitum orchestrator.

Each recipe is a frozen param dict for Engine.generate_universe().
Palette and terminal_shape are NOT included — they are randomized per run.
"""
import numpy as np

STYLES = [
    'deep_sea', 'solar', 'rainbow', 'forest',
    'sunset', 'cobalt', 'crimson', 'pebble',
]

# L-system growth base params per rule (from export_all.py proven combos)
_LSYSTEM_PARAMS = {
    'dragon':     {'lsystem_rule': 'dragon',     'iterations': 10, 'step_size': 25, 'num_seeds': 40, 'node_size': 8, 'line_width': 5},
    'gosper':     {'lsystem_rule': 'gosper',     'iterations': 4,  'step_size': 30, 'num_seeds': 30, 'node_size': 8, 'line_width': 5},
    'sierpinski': {'lsystem_rule': 'sierpinski', 'iterations': 6,  'step_size': 35, 'num_seeds': 25, 'node_size': 8, 'line_width': 5},
    'plant':      {'lsystem_rule': 'plant',      'iterations': 5,  'step_size': 25, 'num_seeds': 30, 'node_size': 8, 'line_width': 5},
}

RECIPES = [
    # Grid modes (1-3)
    {'name': 'grid_rect', 'mode': 'grid', 'weight': 1.0,
     'params': {'grid_res': 48, 'cell_padding': 0.2, 'grid_style': 'rect'}},
    {'name': 'grid_dots', 'mode': 'grid', 'weight': 1.0,
     'params': {'grid_res': 48, 'cell_padding': 0.2, 'grid_style': 'dots'}},
    {'name': 'grid_maze', 'mode': 'grid', 'weight': 1.0,
     'params': {'grid_res': 48, 'cell_padding': 0.2, 'grid_style': 'maze'}},

    # Pure L-system growth (4-7)
    {'name': 'growth_dragon',     'mode': 'lsystem_growth', 'weight': 1.0, 'params': {**_LSYSTEM_PARAMS['dragon']}},
    {'name': 'growth_gosper',     'mode': 'lsystem_growth', 'weight': 0.5, 'params': {**_LSYSTEM_PARAMS['gosper']}},
    {'name': 'growth_sierpinski', 'mode': 'lsystem_growth', 'weight': 1.0, 'params': {**_LSYSTEM_PARAMS['sierpinski']}},
    {'name': 'growth_plant',      'mode': 'lsystem_growth', 'weight': 0.5, 'params': {**_LSYSTEM_PARAMS['plant']}},

    # Hybrid L-system growth + composite grid (8-11)
    {'name': 'hybrid_growth_dragon',     'mode': 'lsystem_growth', 'weight': 3.0, 'params': {**_LSYSTEM_PARAMS['dragon'],     'composite': True}},
    {'name': 'hybrid_growth_gosper',     'mode': 'lsystem_growth', 'weight': 3.0, 'params': {**_LSYSTEM_PARAMS['gosper'],     'composite': True}},
    {'name': 'hybrid_growth_sierpinski', 'mode': 'lsystem_growth', 'weight': 3.0, 'params': {**_LSYSTEM_PARAMS['sierpinski'], 'composite': True}},
    {'name': 'hybrid_growth_plant',      'mode': 'lsystem_growth', 'weight': 3.0, 'params': {**_LSYSTEM_PARAMS['plant'],      'composite': True}},

    # Pure fractals (12-14)
    {'name': 'pure_box',          'mode': 'fractal_pure', 'weight': 1.0, 'params': {'fractal_type': 'box',          'order': 7, 'size': 2048.0}},
    {'name': 'pure_koch',         'mode': 'fractal_pure', 'weight': 1.0, 'params': {'fractal_type': 'koch',         'order': 5, 'size': 2048.0}},
    {'name': 'pure_hilbert_koch', 'mode': 'fractal_pure', 'weight': 1.0, 'params': {'fractal_type': 'hilbert_koch', 'order': 5, 'size': 2048.0}},

    # Hybrid fractals + composite grid (15-17)
    {'name': 'hybrid_hilbert_koch', 'mode': 'fractal_pure', 'weight': 0.5, 'params': {'fractal_type': 'hilbert_koch', 'order': 5, 'size': 2048.0, 'composite': True}},
    {'name': 'hybrid_koch',         'mode': 'fractal_pure', 'weight': 3.0, 'params': {'fractal_type': 'koch',         'order': 5, 'size': 2048.0, 'composite': True}},
    {'name': 'hybrid_box',          'mode': 'fractal_pure', 'weight': 0.5, 'params': {'fractal_type': 'box',          'order': 7, 'size': 2048.0, 'composite': True}},

    # Box unfilled (18)
    {'name': 'pure_box_unfilled', 'mode': 'fractal_pure', 'weight': 1.0, 'params': {'fractal_type': 'box', 'order': 7, 'size': 2048.0, 'fill_boxes': False}},

    # Segmented (19)
    {'name': 'segmented', 'mode': 'segmented', 'weight': 3.0, 'params': {}},
]


def get_recipe_by_name(name):
    """Look up a recipe by its name. Returns None if not found."""
    for recipe in RECIPES:
        if recipe['name'] == name:
            return recipe
    return None


def select_recipe(rng):
    """Select a recipe using weighted random choice.

    Args:
        rng: numpy RandomState instance for deterministic selection.

    Returns:
        dict: The selected recipe.
    """
    weights = np.array([r['weight'] for r in RECIPES])
    probs = weights / weights.sum()
    idx = rng.choice(len(RECIPES), p=probs)
    return RECIPES[idx]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTHONPATH=. uv run pytest tests/test_recipes.py -v`
Expected: All 10 tests PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/recipes.py tests/test_recipes.py
git commit -m "feat: add recipe deck for orchestrator"
```

---

### Task 2: orchestrate.py — Seed Derivation + Rendering

**Files:**
- Create: `scripts/orchestrate.py`
- Create: `tests/test_orchestrate.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_orchestrate.py
import json
import os
import numpy as np
import pytest
from unittest.mock import patch
from scripts.orchestrate import derive_seed, resolve_params, run_orchestrate


def test_derive_seed_deterministic():
    s1 = derive_seed("2026040914")
    s2 = derive_seed("2026040914")
    assert s1 == s2


def test_derive_seed_positive():
    s = derive_seed("2026040914")
    assert s > 0


def test_derive_seed_varies_by_hour():
    s1 = derive_seed("2026040914")
    s2 = derive_seed("2026040915")
    assert s1 != s2


def test_resolve_params_has_palette():
    rng = np.random.RandomState(42)
    from scripts.recipes import RECIPES
    params = resolve_params(RECIPES[0], rng)
    assert 'palette' in params
    assert params['palette'] in [
        'deep_sea', 'solar', 'rainbow', 'forest',
        'sunset', 'cobalt', 'crimson', 'pebble',
    ]


def test_resolve_params_has_mode():
    rng = np.random.RandomState(42)
    from scripts.recipes import RECIPES
    recipe = RECIPES[0]  # grid_rect
    params = resolve_params(recipe, rng)
    assert params['mode'] == 'grid'


def test_resolve_params_lsystem_has_terminal_shape():
    rng = np.random.RandomState(42)
    from scripts.recipes import get_recipe_by_name
    recipe = get_recipe_by_name('growth_dragon')
    params = resolve_params(recipe, rng)
    assert params['terminal_shape'] in ('circle', 'square')


def test_run_orchestrate_writes_files(tmp_path):
    output_dir = str(tmp_path)
    run_orchestrate(seed=42, recipe_name='grid_rect', output_dir=output_dir)

    assert os.path.exists(os.path.join(output_dir, 'canvas.png'))
    assert os.path.exists(os.path.join(output_dir, 'metadata.json'))

    with open(os.path.join(output_dir, 'metadata.json')) as f:
        meta = json.load(f)
    assert meta['contract_version'] == 1
    assert meta['seed'] == 42
    assert meta['recipe_name'] == 'grid_rect'
    assert 'params' in meta
    assert 'generator_sha' in meta
    assert 'generated_at_utc' in meta
    assert 'final_whitespace' in meta
    assert 'adaptive_passes' in meta


def test_run_orchestrate_deterministic(tmp_path):
    dir1 = str(tmp_path / 'run1')
    dir2 = str(tmp_path / 'run2')
    os.makedirs(dir1)
    os.makedirs(dir2)
    run_orchestrate(seed=99, recipe_name='grid_rect', output_dir=dir1)
    run_orchestrate(seed=99, recipe_name='grid_rect', output_dir=dir2)

    with open(os.path.join(dir1, 'metadata.json')) as f:
        m1 = json.load(f)
    with open(os.path.join(dir2, 'metadata.json')) as f:
        m2 = json.load(f)
    assert m1['seed'] == m2['seed']
    assert m1['params'] == m2['params']
    assert m1['recipe_name'] == m2['recipe_name']
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=. uv run pytest tests/test_orchestrate.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.orchestrate'`

- [ ] **Step 3: Implement orchestrate.py**

```python
#!/usr/bin/env python3
# scripts/orchestrate.py
"""
Tessera ad Infinitum orchestrator.

Derives a seed from the current UTC hour (or --seed override), selects a
weighted-random recipe from the deck, renders a 2048x2048 master canvas,
and writes canvas.png + metadata.json to --output-dir.
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

import numpy as np

from generator.engine import Engine
from scripts.recipes import RECIPES, STYLES, get_recipe_by_name, select_recipe


def derive_seed(hour_string):
    """Derive a deterministic positive 31-bit seed from a YYYYMMDDHH string."""
    return hash(f"tessera-{hour_string}") & 0x7FFFFFFF


def resolve_params(recipe, rng):
    """Build the full params dict for Engine.generate_universe().

    Merges the recipe's fixed params with randomized palette and
    terminal_shape. The recipe's 'mode' becomes params['mode'].

    Args:
        recipe: dict from RECIPES with keys 'name', 'mode', 'params'.
        rng: numpy RandomState for deterministic randomization.

    Returns:
        dict: Fully resolved params for generate_universe().
    """
    params = dict(recipe['params'])
    params['mode'] = recipe['mode']
    params['palette'] = STYLES[rng.randint(len(STYLES))]
    if recipe['mode'] == 'lsystem_growth':
        params['terminal_shape'] = rng.choice(['circle', 'square'])
    return params


def _get_git_sha():
    """Get the current git commit SHA, or 'unknown' if not in a repo."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else 'unknown'
    except Exception:
        return 'unknown'


def _numpy_converter(obj):
    """JSON serializer for numpy types."""
    if isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj


def run_orchestrate(seed, recipe_name=None, output_dir='output'):
    """Run the full orchestration: select recipe, render, write outputs.

    Args:
        seed: integer seed for generation.
        recipe_name: force a specific recipe by name, or None for weighted random.
        output_dir: directory to write canvas.png and metadata.json.
    """
    rng = np.random.RandomState(seed)

    if recipe_name:
        recipe = get_recipe_by_name(recipe_name)
        if recipe is None:
            names = [r['name'] for r in RECIPES]
            raise ValueError(f"Unknown recipe '{recipe_name}'. Available: {names}")
    else:
        recipe = select_recipe(rng)

    params = resolve_params(recipe, rng)

    engine = Engine(size=(2048, 2048))
    img, engine_meta = engine.generate_universe(seed, params)

    os.makedirs(output_dir, exist_ok=True)
    img.save(os.path.join(output_dir, 'canvas.png'))

    metadata = {
        'contract_version': 1,
        'generator_sha': _get_git_sha(),
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'seed': seed,
        'recipe_name': recipe['name'],
        'params': params,
        'final_whitespace': engine_meta.get('final_whitespace'),
        'adaptive_passes': engine_meta.get('adaptive_passes', 0),
    }

    with open(os.path.join(output_dir, 'metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=2, default=_numpy_converter)

    print(f"Done: seed={seed} recipe={recipe['name']} palette={params['palette']}")
    print(f"  whitespace={metadata['final_whitespace']:.2%}  passes={metadata['adaptive_passes']}")


def main():
    parser = argparse.ArgumentParser(description='Tessera ad Infinitum Orchestrator')
    parser.add_argument('--seed', type=int, default=None,
                        help='Override seed (default: derived from UTC hour)')
    parser.add_argument('--output-dir', type=str, default='output',
                        help='Output directory (default: output/)')
    parser.add_argument('--recipe', type=str, default=None,
                        help='Force a specific recipe by name')
    args = parser.parse_args()

    if args.seed is None:
        hour_str = datetime.now(timezone.utc).strftime('%Y%m%d%H')
        seed = derive_seed(hour_str)
        print(f"Derived seed from UTC hour {hour_str}: {seed}")
    else:
        seed = args.seed

    run_orchestrate(seed=seed, recipe_name=args.recipe, output_dir=args.output_dir)


if __name__ == '__main__':
    main()
```

- [ ] **Step 4: Create `scripts/__init__.py`** so tests can import from `scripts.*`

```python
# scripts/__init__.py
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `PYTHONPATH=. uv run pytest tests/test_orchestrate.py -v`
Expected: All 8 tests PASS. Note: `test_run_orchestrate_writes_files` will take a few seconds (renders a 2048x2048 canvas).

- [ ] **Step 6: Commit**

```bash
git add scripts/__init__.py scripts/orchestrate.py tests/test_orchestrate.py
git commit -m "feat: add orchestrate.py with seed derivation and recipe rendering"
```

---

### Task 3: Indexed-PNG Conversion Utility

Build the palette conversion as a standalone function in `scripts/slice.py` and test it before adding cropping.

**Files:**
- Create: `scripts/slice.py` (partial — conversion only)
- Create: `tests/test_slice.py` (partial — conversion tests only)

- [ ] **Step 1: Write failing tests for indexed-PNG conversion**

```python
# tests/test_slice.py
import numpy as np
from PIL import Image
from generator.palette import PEBBLE_64_PALETTE
from scripts.slice import convert_to_indexed, PALETTE_FLAT


def test_palette_flat_length():
    # 64 colors * 3 channels = 192 bytes, padded to 768
    assert len(PALETTE_FLAT) == 768


def test_palette_flat_ordering():
    # First color should be (0, 0, 0)
    assert PALETTE_FLAT[0] == 0
    assert PALETTE_FLAT[1] == 0
    assert PALETTE_FLAT[2] == 0
    # Second color should be (0, 0, 0x55)
    assert PALETTE_FLAT[3] == 0
    assert PALETTE_FLAT[4] == 0
    assert PALETTE_FLAT[5] == 0x55


def test_convert_to_indexed_mode():
    img = Image.new('RGB', (10, 10), (0xFF, 0x00, 0x00))  # pure red
    indexed = convert_to_indexed(img)
    assert indexed.mode == 'P'


def test_convert_to_indexed_preserves_size():
    img = Image.new('RGB', (100, 50), (0, 0, 0))
    indexed = convert_to_indexed(img)
    assert indexed.size == (100, 50)


def test_convert_to_indexed_correct_index():
    # Pure black (0,0,0) is index 0 in PEBBLE_64_PALETTE
    img = Image.new('RGB', (2, 2), (0, 0, 0))
    indexed = convert_to_indexed(img)
    pixels = list(indexed.getdata())
    assert all(p == 0 for p in pixels)


def test_convert_to_indexed_white():
    # Pure white (0xFF,0xFF,0xFF) is the last color: index 63
    img = Image.new('RGB', (2, 2), (0xFF, 0xFF, 0xFF))
    indexed = convert_to_indexed(img)
    pixels = list(indexed.getdata())
    assert all(p == 63 for p in pixels)


def test_convert_to_indexed_known_color():
    # Red (0xFF, 0x00, 0x00): channels are (3, 0, 0) in Pebble index space
    # Index = 3*16 + 0*4 + 0 = 48
    img = Image.new('RGB', (2, 2), (0xFF, 0x00, 0x00))
    indexed = convert_to_indexed(img)
    pixels = list(indexed.getdata())
    assert all(p == 48 for p in pixels)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=. uv run pytest tests/test_slice.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement indexed-PNG conversion**

```python
#!/usr/bin/env python3
# scripts/slice.py
"""
Tessera ad Infinitum slicer.

Reads a master canvas.png + metadata.json, converts to indexed-color PNG
using the Pebble 64 palette, and generates pre-cropped byte-array slices
for each target platform.
"""
import argparse
import json
import os

import numpy as np
from PIL import Image

from generator.palette import PEBBLE_64_PALETTE

# Build the flat palette list for PIL: [R0, G0, B0, R1, G1, B1, ...] padded to 768
PALETTE_FLAT = list(PEBBLE_64_PALETTE.flatten()) + [0] * (768 - len(PEBBLE_64_PALETTE) * 3)


def convert_to_indexed(img):
    """Convert an RGB PIL Image to indexed-color using the Pebble 64 palette.

    Uses PIL quantize() with a custom palette image so that pixel values
    are indices into PEBBLE_64_PALETTE in canonical order.

    Args:
        img: PIL.Image in RGB mode.

    Returns:
        PIL.Image in P (palette) mode.
    """
    # Build a palette image that PIL can use as the quantization target
    palette_img = Image.new('P', (1, 1))
    palette_img.putpalette(PALETTE_FLAT)
    # quantize with dither=0 for exact nearest-color mapping (no dithering)
    indexed = img.quantize(colors=64, palette=palette_img, dither=0)
    return indexed
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTHONPATH=. uv run pytest tests/test_slice.py -v`
Expected: All 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/slice.py tests/test_slice.py
git commit -m "feat: add indexed-PNG conversion for Pebble 64 palette"
```

---

### Task 4: Platform Cropping + Byte-Array Encoding

Add the slicing logic to `scripts/slice.py`.

**Files:**
- Modify: `scripts/slice.py`
- Modify: `tests/test_slice.py`

- [ ] **Step 1: Write failing tests for cropping and encoding**

Append to `tests/test_slice.py`:

```python
from scripts.slice import PLATFORMS, crop_slice, encode_slice, generate_slices


def test_platforms_defined():
    assert 'basalt' in PLATFORMS
    assert 'chalk' in PLATFORMS
    assert 'emery' in PLATFORMS
    assert PLATFORMS['basalt'] == {'w': 144, 'h': 168, 'shape': 'rect'}
    assert PLATFORMS['chalk'] == {'w': 180, 'h': 180, 'shape': 'round'}
    assert PLATFORMS['emery'] == {'w': 200, 'h': 228, 'shape': 'rect'}


def test_crop_slice_basalt_size():
    indexed = convert_to_indexed(Image.new('RGB', (2048, 2048), (0, 0, 0)))
    crop = crop_slice(indexed, x=0, y=0, platform='basalt')
    assert crop.size == (144, 168)


def test_crop_slice_chalk_size():
    indexed = convert_to_indexed(Image.new('RGB', (2048, 2048), (0, 0, 0)))
    crop = crop_slice(indexed, x=0, y=0, platform='chalk')
    assert crop.size == (180, 180)


def test_crop_slice_chalk_round_mask():
    # Make an image with a known color, crop as chalk, check corners are index 0
    img = Image.new('RGB', (2048, 2048), (0xFF, 0xFF, 0xFF))  # white = index 63
    indexed = convert_to_indexed(img)
    crop = crop_slice(indexed, x=0, y=0, platform='chalk')
    pixels = np.array(crop)
    # Top-left corner (0,0) is outside the circle — should be 0
    assert pixels[0, 0] == 0
    # Center (90,90) is inside — should be 63
    assert pixels[90, 90] == 63


def test_crop_slice_clamps_to_bounds():
    indexed = convert_to_indexed(Image.new('RGB', (2048, 2048), (0, 0, 0)))
    # Request a crop that would exceed canvas bounds
    crop = crop_slice(indexed, x=2000, y=2000, platform='emery')
    assert crop.size == (200, 228)


def test_encode_slice_length():
    indexed = convert_to_indexed(Image.new('RGB', (2048, 2048), (0, 0, 0)))
    crop = crop_slice(indexed, x=0, y=0, platform='basalt')
    data = encode_slice(crop)
    assert isinstance(data, bytes)
    assert len(data) == 144 * 168


def test_encode_slice_values():
    # White image → all index 63
    img = Image.new('RGB', (2048, 2048), (0xFF, 0xFF, 0xFF))
    indexed = convert_to_indexed(img)
    crop = crop_slice(indexed, x=0, y=0, platform='basalt')
    data = encode_slice(crop)
    assert all(b == 63 for b in data)


def test_generate_slices_writes_files(tmp_path):
    img = Image.new('RGB', (2048, 2048), (0xFF, 0x00, 0x00))
    indexed = convert_to_indexed(img)
    output_dir = str(tmp_path)

    generate_slices(indexed, seed=42, output_dir=output_dir, count=2, platforms=['basalt'])

    assert os.path.exists(os.path.join(output_dir, 'slices', 'basalt', '000.bin'))
    assert os.path.exists(os.path.join(output_dir, 'slices', 'basalt', '001.bin'))
    assert not os.path.exists(os.path.join(output_dir, 'slices', 'basalt', '002.bin'))

    index_path = os.path.join(output_dir, 'slices', 'index.json')
    assert os.path.exists(index_path)
    with open(index_path) as f:
        index = json.load(f)
    assert index['count_per_platform'] == 2
    assert len(index['offsets']['basalt']) == 2
```

- [ ] **Step 2: Run tests to verify new tests fail**

Run: `PYTHONPATH=. uv run pytest tests/test_slice.py -v`
Expected: 7 pass (from Task 3), new tests FAIL with `ImportError`

- [ ] **Step 3: Implement cropping and encoding**

Add to `scripts/slice.py` (after the existing `convert_to_indexed` function):

```python
PLATFORMS = {
    'basalt': {'w': 144, 'h': 168, 'shape': 'rect'},
    'chalk':  {'w': 180, 'h': 180, 'shape': 'round'},
    'emery':  {'w': 200, 'h': 228, 'shape': 'rect'},
}


def crop_slice(indexed_img, x, y, platform):
    """Crop a platform-sized slice from the indexed image.

    For 'chalk' (round), applies a circular mask setting pixels outside
    the inscribed circle to palette index 0.

    Args:
        indexed_img: PIL.Image in P mode.
        x: top-left x offset.
        y: top-left y offset.
        platform: 'basalt', 'chalk', or 'emery'.

    Returns:
        PIL.Image in P mode, sized to the platform resolution.
    """
    plat = PLATFORMS[platform]
    w, h = plat['w'], plat['h']
    canvas_w, canvas_h = indexed_img.size

    # Clamp so crop stays within canvas
    x = min(x, canvas_w - w)
    y = min(y, canvas_h - h)
    x = max(x, 0)
    y = max(y, 0)

    crop = indexed_img.crop((x, y, x + w, y + h))

    if plat['shape'] == 'round':
        pixels = np.array(crop)
        cy, cx = h / 2.0, w / 2.0
        radius = min(cx, cy)
        yy, xx = np.ogrid[:h, :w]
        outside = (xx - cx) ** 2 + (yy - cy) ** 2 > radius ** 2
        pixels[outside] = 0
        crop = Image.fromarray(pixels, mode='P')
        crop.putpalette(PALETTE_FLAT)

    return crop


def encode_slice(crop):
    """Encode an indexed-color crop as a raw byte array.

    One byte per pixel, value = palette index (0..63).

    Args:
        crop: PIL.Image in P mode.

    Returns:
        bytes: raw pixel data, length = width * height.
    """
    return bytes(crop.getdata())


def generate_slices(indexed_img, seed, output_dir, count=100, platforms=None):
    """Generate pre-cropped byte-array slices for all target platforms.

    Args:
        indexed_img: PIL.Image in P mode (2048x2048).
        seed: integer seed for deterministic offset generation.
        output_dir: base output directory.
        count: number of slices per platform.
        platforms: list of platform names, or None for all.
    """
    if platforms is None:
        platforms = list(PLATFORMS.keys())

    canvas_w, canvas_h = indexed_img.size
    rng = np.random.RandomState(seed)
    manifest = {
        'count_per_platform': count,
        'platforms': {p: PLATFORMS[p] for p in platforms},
        'offsets': {},
    }

    for platform in platforms:
        plat = PLATFORMS[platform]
        w, h = plat['w'], plat['h']
        max_x = canvas_w - w
        max_y = canvas_h - h

        plat_dir = os.path.join(output_dir, 'slices', platform)
        os.makedirs(plat_dir, exist_ok=True)

        offsets = []
        for i in range(count):
            x = int(rng.randint(0, max_x + 1))
            y = int(rng.randint(0, max_y + 1))
            offsets.append([x, y])

            crop = crop_slice(indexed_img, x, y, platform)
            data = encode_slice(crop)

            bin_path = os.path.join(plat_dir, f'{i:03d}.bin')
            with open(bin_path, 'wb') as f:
                f.write(data)

        manifest['offsets'][platform] = offsets

    index_path = os.path.join(output_dir, 'slices', 'index.json')
    with open(index_path, 'w') as f:
        json.dump(manifest, f, indent=2)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTHONPATH=. uv run pytest tests/test_slice.py -v`
Expected: All 15 tests PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/slice.py tests/test_slice.py
git commit -m "feat: add platform cropping and byte-array encoding to slice.py"
```

---

### Task 5: slice.py CLI

Wire up the CLI main so `slice.py` can be run standalone.

**Files:**
- Modify: `scripts/slice.py`
- Modify: `tests/test_slice.py`

- [ ] **Step 1: Write failing test for end-to-end CLI flow**

Append to `tests/test_slice.py`:

```python
from scripts.slice import run_slice


def test_run_slice_end_to_end(tmp_path):
    # Create a fake orchestrate output
    img = Image.new('RGB', (2048, 2048), (0x55, 0xAA, 0xFF))
    output_dir = str(tmp_path)
    img.save(os.path.join(output_dir, 'canvas.png'))
    meta = {'seed': 42, 'contract_version': 1}
    with open(os.path.join(output_dir, 'metadata.json'), 'w') as f:
        json.dump(meta, f)

    run_slice(output_dir=output_dir, count=3, platforms=['basalt', 'emery'])

    # Check indexed PNG was created
    assert os.path.exists(os.path.join(output_dir, 'canvas_indexed.png'))
    idx_img = Image.open(os.path.join(output_dir, 'canvas_indexed.png'))
    assert idx_img.mode == 'P'

    # Check slices
    for plat in ['basalt', 'emery']:
        for i in range(3):
            bin_path = os.path.join(output_dir, 'slices', plat, f'{i:03d}.bin')
            assert os.path.exists(bin_path)
            plat_info = PLATFORMS[plat]
            assert os.path.getsize(bin_path) == plat_info['w'] * plat_info['h']

    # Check chalk was NOT generated
    assert not os.path.exists(os.path.join(output_dir, 'slices', 'chalk'))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. uv run pytest tests/test_slice.py::test_run_slice_end_to_end -v`
Expected: FAIL — `ImportError: cannot import name 'run_slice'`

- [ ] **Step 3: Add run_slice and CLI main**

Add to `scripts/slice.py`:

```python
def run_slice(output_dir='output', count=100, platforms=None):
    """Run the full slicing pipeline.

    Reads canvas.png + metadata.json from output_dir, converts to indexed
    PNG, generates slices, writes all outputs.

    Args:
        output_dir: directory containing canvas.png and metadata.json.
        count: slices per platform.
        platforms: list of platform names, or None for all.
    """
    canvas_path = os.path.join(output_dir, 'canvas.png')
    meta_path = os.path.join(output_dir, 'metadata.json')

    img = Image.open(canvas_path).convert('RGB')
    with open(meta_path) as f:
        meta = json.load(f)

    seed = meta['seed']

    indexed = convert_to_indexed(img)
    indexed.save(os.path.join(output_dir, 'canvas_indexed.png'))
    print(f"Saved indexed PNG ({indexed.size[0]}x{indexed.size[1]})")

    generate_slices(indexed, seed=seed, output_dir=output_dir,
                    count=count, platforms=platforms)

    plat_names = platforms or list(PLATFORMS.keys())
    total = count * len(plat_names)
    print(f"Generated {total} slices ({count} x {len(plat_names)} platforms)")


def main():
    parser = argparse.ArgumentParser(description='Tessera ad Infinitum Slicer')
    parser.add_argument('--output-dir', type=str, default='output',
                        help='Directory with canvas.png + metadata.json')
    parser.add_argument('--count', type=int, default=100,
                        help='Slices per platform (default: 100)')
    parser.add_argument('--platform', type=str, default=None,
                        choices=list(PLATFORMS.keys()),
                        help='Generate for one platform only (default: all)')
    args = parser.parse_args()

    platforms = [args.platform] if args.platform else None
    run_slice(output_dir=args.output_dir, count=args.count, platforms=platforms)


if __name__ == '__main__':
    main()
```

- [ ] **Step 4: Run all slice tests**

Run: `PYTHONPATH=. uv run pytest tests/test_slice.py -v`
Expected: All 16 tests PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/slice.py tests/test_slice.py
git commit -m "feat: add slice.py CLI with end-to-end pipeline"
```

---

### Task 6: upload.py

**Files:**
- Create: `scripts/upload.py`
- Create: `tests/test_upload.py`
- Modify: `pyproject.toml` — add `boto3`

- [ ] **Step 1: Add boto3 dependency**

Edit `pyproject.toml` dependencies:

```toml
[project]
name = "tessera-ad-infinitum-generator"
version = "0.1.0"
dependencies = [
    "numpy",
    "pillow",
    "vnoise",
    "scipy",
    "pytest",
    "setuptools",
    "boto3",
]
```

Run: `uv sync`

- [ ] **Step 2: Write failing tests**

```python
# tests/test_upload.py
import json
import os
import pytest
from scripts.upload import build_upload_plan


def _make_output(tmp_path, num_slices=2):
    """Helper: create a minimal output dir matching orchestrate+slice output."""
    d = str(tmp_path)
    # canvas_indexed.png — just a tiny file
    with open(os.path.join(d, 'canvas_indexed.png'), 'wb') as f:
        f.write(b'fake-png')
    with open(os.path.join(d, 'metadata.json'), 'w') as f:
        json.dump({'seed': 42, 'contract_version': 1}, f)

    for plat in ['basalt', 'chalk', 'emery']:
        plat_dir = os.path.join(d, 'slices', plat)
        os.makedirs(plat_dir, exist_ok=True)
        for i in range(num_slices):
            with open(os.path.join(plat_dir, f'{i:03d}.bin'), 'wb') as f:
                f.write(b'\x00' * 10)

    with open(os.path.join(d, 'slices', 'index.json'), 'w') as f:
        json.dump({'count_per_platform': num_slices}, f)

    return d


def test_build_upload_plan_latest(tmp_path):
    d = _make_output(tmp_path)
    plan = build_upload_plan(d, hour_str='2026040914', skip_archive=False)

    # Should have latest/ entries for canvas, metadata, index, and slice bins
    latest_keys = [e['r2_key'] for e in plan if e['r2_key'].startswith('latest/')]
    assert 'latest/canvas.png' in latest_keys
    assert 'latest/metadata.json' in latest_keys
    assert 'latest/slices/index.json' in latest_keys
    assert 'latest/slices/basalt/000.bin' in latest_keys


def test_build_upload_plan_archive(tmp_path):
    d = _make_output(tmp_path)
    plan = build_upload_plan(d, hour_str='2026040914', skip_archive=False)

    archive_keys = [e['r2_key'] for e in plan if e['r2_key'].startswith('archive/')]
    assert 'archive/2026/04/09/14-canvas.png' in archive_keys
    assert 'archive/2026/04/09/14-metadata.json' in archive_keys
    # Slices should NOT be archived
    assert not any('slices' in k for k in archive_keys)


def test_build_upload_plan_skip_archive(tmp_path):
    d = _make_output(tmp_path)
    plan = build_upload_plan(d, hour_str='2026040914', skip_archive=True)

    archive_keys = [e['r2_key'] for e in plan if e['r2_key'].startswith('archive/')]
    assert len(archive_keys) == 0


def test_build_upload_plan_file_count(tmp_path):
    d = _make_output(tmp_path, num_slices=2)
    plan = build_upload_plan(d, hour_str='2026040914', skip_archive=False)

    # latest: canvas + metadata + index + 3 platforms * 2 slices = 9
    # archive: canvas + metadata = 2
    # total = 11
    assert len(plan) == 11
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `PYTHONPATH=. uv run pytest tests/test_upload.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 4: Implement upload.py**

```python
#!/usr/bin/env python3
# scripts/upload.py
"""
Tessera ad Infinitum R2 uploader.

Reads the output directory produced by orchestrate.py + slice.py and
uploads everything to Cloudflare R2 using the S3-compatible API.
"""
import argparse
import os
from datetime import datetime, timezone

import boto3


def build_upload_plan(output_dir, hour_str, skip_archive=False):
    """Build a list of (local_path, r2_key) upload entries.

    Args:
        output_dir: local directory with canvas_indexed.png, metadata.json, slices/.
        hour_str: 'YYYYMMDDHH' string for archive path construction.
        skip_archive: if True, omit archive/ entries.

    Returns:
        list of dicts with 'local_path' and 'r2_key'.
    """
    plan = []

    canvas_path = os.path.join(output_dir, 'canvas_indexed.png')
    meta_path = os.path.join(output_dir, 'metadata.json')

    # latest/
    plan.append({'local_path': canvas_path, 'r2_key': 'latest/canvas.png'})
    plan.append({'local_path': meta_path, 'r2_key': 'latest/metadata.json'})

    # latest/slices/
    slices_dir = os.path.join(output_dir, 'slices')
    index_path = os.path.join(slices_dir, 'index.json')
    if os.path.exists(index_path):
        plan.append({'local_path': index_path, 'r2_key': 'latest/slices/index.json'})

    for platform in sorted(os.listdir(slices_dir)):
        plat_dir = os.path.join(slices_dir, platform)
        if not os.path.isdir(plat_dir):
            continue
        for bin_file in sorted(os.listdir(plat_dir)):
            if bin_file.endswith('.bin'):
                local = os.path.join(plat_dir, bin_file)
                plan.append({
                    'local_path': local,
                    'r2_key': f'latest/slices/{platform}/{bin_file}',
                })

    # archive/ (master + metadata only, no slices)
    if not skip_archive:
        # Parse YYYYMMDDHH into archive path components
        year = hour_str[0:4]
        month = hour_str[4:6]
        day = hour_str[6:8]
        hour = hour_str[8:10]
        prefix = f'archive/{year}/{month}/{day}/{hour}'
        plan.append({'local_path': canvas_path, 'r2_key': f'{prefix}-canvas.png'})
        plan.append({'local_path': meta_path, 'r2_key': f'{prefix}-metadata.json'})

    return plan


def execute_upload(plan, bucket, endpoint_url, dry_run=False):
    """Execute the upload plan against R2.

    Args:
        plan: list of dicts with 'local_path' and 'r2_key'.
        bucket: R2 bucket name.
        endpoint_url: S3-compatible endpoint URL.
        dry_run: if True, print plan without uploading.
    """
    if dry_run:
        print(f"DRY RUN — {len(plan)} files would be uploaded to {bucket}:")
        for entry in plan:
            size = os.path.getsize(entry['local_path'])
            print(f"  {entry['local_path']} → {entry['r2_key']} ({size} bytes)")
        return

    s3 = boto3.client('s3', endpoint_url=endpoint_url)

    for entry in plan:
        print(f"  Uploading {entry['r2_key']}...", end='', flush=True)
        s3.upload_file(entry['local_path'], bucket, entry['r2_key'])
        print(' done')

    print(f"Uploaded {len(plan)} files to {bucket}")


def main():
    parser = argparse.ArgumentParser(description='Tessera ad Infinitum R2 Uploader')
    parser.add_argument('--output-dir', type=str, default='output',
                        help='Directory with orchestrate + slice output')
    parser.add_argument('--skip-archive', action='store_true',
                        help='Upload to latest/ only, skip archive/')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print upload plan without uploading')
    args = parser.parse_args()

    # R2 config from environment
    account_id = os.environ.get('R2_ACCOUNT_ID', '')
    bucket = os.environ.get('R2_BUCKET', '')
    endpoint_url = f'https://{account_id}.r2.cloudflarestorage.com'

    hour_str = datetime.now(timezone.utc).strftime('%Y%m%d%H')

    plan = build_upload_plan(args.output_dir, hour_str, skip_archive=args.skip_archive)
    print(f"Upload plan: {len(plan)} files → {bucket}")
    execute_upload(plan, bucket, endpoint_url, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `PYTHONPATH=. uv run pytest tests/test_upload.py -v`
Expected: All 4 tests PASS

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml scripts/upload.py tests/test_upload.py
git commit -m "feat: add upload.py for R2 deployment with dry-run support"
```

---

### Task 7: GitHub Actions Workflow

**Files:**
- Create: `.github/workflows/generate.yml`
- Modify: `.gitignore` — add `output/`

- [ ] **Step 1: Add output/ to .gitignore**

Append to `.gitignore`:

```
# Pipeline output
output/
```

- [ ] **Step 2: Create workflow file**

```yaml
# .github/workflows/generate.yml
name: Generate Universe

on:
  schedule:
    - cron: '0 * * * *'
  workflow_dispatch:
    inputs:
      seed:
        description: 'Override seed (skip UTC-hour derivation)'
        required: false
        type: string
      recipe:
        description: 'Force a specific recipe by name'
        required: false
        type: string

env:
  PYTHONPATH: '.'

jobs:
  generate:
    runs-on: ubuntu-latest
    timeout-minutes: 15

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Install dependencies
        run: uv sync

      - name: Orchestrate
        run: |
          ARGS="--output-dir output"
          if [ -n "${{ inputs.seed }}" ]; then
            ARGS="$ARGS --seed ${{ inputs.seed }}"
          fi
          if [ -n "${{ inputs.recipe }}" ]; then
            ARGS="$ARGS --recipe ${{ inputs.recipe }}"
          fi
          uv run python scripts/orchestrate.py $ARGS

      - name: Slice
        run: uv run python scripts/slice.py --output-dir output --count 100

      - name: Upload to R2
        env:
          R2_ACCOUNT_ID: ${{ secrets.R2_ACCOUNT_ID }}
          R2_ACCESS_KEY_ID: ${{ secrets.R2_ACCESS_KEY_ID }}
          R2_SECRET_ACCESS_KEY: ${{ secrets.R2_SECRET_ACCESS_KEY }}
          R2_BUCKET: ${{ secrets.R2_BUCKET }}
          AWS_ACCESS_KEY_ID: ${{ secrets.R2_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.R2_SECRET_ACCESS_KEY }}
        run: uv run python scripts/upload.py --output-dir output
```

Note: `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` are set because `boto3` reads them automatically. `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` are the canonical names in our scripts.

- [ ] **Step 3: Commit**

```bash
git add .gitignore .github/workflows/generate.yml
git commit -m "feat: add GitHub Actions hourly generation workflow"
```

---

### Task 8: End-to-End Local Smoke Test

Run the full pipeline locally (minus upload) to verify everything chains correctly.

**Files:** None — this is a verification step.

- [ ] **Step 1: Run orchestrate with a fixed seed and recipe**

Run: `PYTHONPATH=. uv run python scripts/orchestrate.py --seed 42 --recipe grid_rect --output-dir output`
Expected: Prints seed, recipe, palette, whitespace stats. Creates `output/canvas.png` and `output/metadata.json`.

- [ ] **Step 2: Verify orchestrate output**

Run: `ls -la output/canvas.png output/metadata.json`
Expected: `canvas.png` is ~1-5MB, `metadata.json` exists.

Run: `python -c "import json; m=json.load(open('output/metadata.json')); print(m['contract_version'], m['seed'], m['recipe_name'])"`
Expected: `1 42 grid_rect`

- [ ] **Step 3: Run slice**

Run: `PYTHONPATH=. uv run python scripts/slice.py --output-dir output --count 3 --platform basalt`
Expected: Prints indexed PNG size and slice count. Creates `output/canvas_indexed.png`, `output/slices/basalt/00{0,1,2}.bin`, `output/slices/index.json`.

- [ ] **Step 4: Verify slice output**

Run: `ls -la output/slices/basalt/`
Expected: 3 `.bin` files, each exactly 24192 bytes (144 × 168).

Run: `python -c "import json; idx=json.load(open('output/slices/index.json')); print(idx['count_per_platform'], len(idx['offsets']['basalt']))"`
Expected: `3 3`

- [ ] **Step 5: Run upload in dry-run mode**

Run: `PYTHONPATH=. uv run python scripts/upload.py --output-dir output --dry-run`
Expected: Prints the upload plan (file paths → R2 keys) without uploading.

- [ ] **Step 6: Run full test suite**

Run: `PYTHONPATH=. uv run pytest -v`
Expected: All tests pass (existing generator tests + new orchestrate/slice/upload tests).

- [ ] **Step 7: Commit any fixes and clean up**

```bash
rm -rf output/
git add -A
git commit -m "chore: end-to-end pipeline verification complete"
```

(Only commit if there were fixes. Skip if everything passed clean.)
