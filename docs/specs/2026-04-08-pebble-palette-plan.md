# Pebble Palette & Color Mapping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Pebble 64-color quantization and vectorized mapping strategies.

**Architecture:**
- `generator/palette.py`: Contains the `PEBBLE_64_PALETTE` constant, quantization logic, presets, and vectorized mapping functions.
- `tests/test_palette.py`: Contains unit tests for all functions in `palette.py`.

**Tech Stack:**
- Python 3.13
- NumPy
- Pytest

---

### Task 1: Pebble 64-color Quantization

**Files:**
- Create: `generator/palette.py`
- Test: `tests/test_palette.py`

- [ ] **Step 1: Write the failing test for quantization**
```python
import numpy as np
import pytest
from generator.palette import to_pebble_color

def test_to_pebble_color():
    assert to_pebble_color((0, 0, 0)) == (0, 0, 0)
    assert to_pebble_color((255, 255, 255)) == (255, 255, 255)
    assert to_pebble_color((10, 80, 200)) == (0, 85, 170)
```

- [ ] **Step 2: Run test to verify it fails**
Run: `uv run pytest tests/test_palette.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Implement `to_pebble_color` and `PEBBLE_64_PALETTE`**
```python
import numpy as np

PEBBLE_CHANNELS = [0x00, 0x55, 0xAA, 0xFF]

def to_pebble_color(rgb_tuple):
    return tuple(min(PEBBLE_CHANNELS, key=lambda x: abs(x - c)) for c in rgb_tuple)

PEBBLE_64_PALETTE = [(r, g, b) for r in PEBBLE_CHANNELS for g in PEBBLE_CHANNELS for b in PEBBLE_CHANNELS]
```

- [ ] **Step 4: Run test to verify it passes**
Run: `uv run pytest tests/test_palette.py -v`

- [ ] **Step 5: Commit**
```bash
git add generator/palette.py tests/test_palette.py
git commit -m "feat: add pebble color quantization"
```

---

### Task 2: Palette Presets

**Files:**
- Modify: `generator/palette.py`
- Test: `tests/test_palette.py`

- [ ] **Step 1: Write tests for presets**
```python
from generator.palette import DEEP_SEA, SOLAR

def test_presets_are_pebble_safe():
    for color in DEEP_SEA + SOLAR:
        assert all(c in [0, 85, 170, 255] for c in color)
```

- [ ] **Step 2: Run test to verify it fails**
Run: `uv run pytest tests/test_palette.py -v`
Expected: FAIL (ImportError)

- [ ] **Step 3: Define `DEEP_SEA` and `SOLAR` presets**
```python
DEEP_SEA = [
    (0, 0, 85),     # Dark Blue
    (0, 85, 170),   # Medium Blue
    (0, 170, 170),  # Cyan
    (0, 255, 170)   # Greenish Cyan
]

SOLAR = [
    (170, 0, 0),    # Dark Red
    (255, 85, 0),   # Orange
    (255, 170, 0),  # Yellow-Orange
    (255, 255, 85)  # Light Yellow
]
```

- [ ] **Step 4: Run test to verify it passes**
Run: `uv run pytest tests/test_palette.py -v`

- [ ] **Step 5: Commit**
```bash
git add generator/palette.py tests/test_palette.py
git commit -m "feat: add deep sea and solar palette presets"
```

---

### Task 3: Vectorized Mapping Strategies

**Files:**
- Modify: `generator/palette.py`
- Test: `tests/test_palette.py`

- [ ] **Step 1: Write tests for mapping strategies**
```python
from generator.palette import map_noise_to_color

def test_map_noise_to_color_vectorized():
    palette = [(0, 0, 0), (255, 255, 255)]
    noise = np.array([0.0, 0.5, 1.0])
    expected = np.array([[0, 0, 0], [127, 127, 127], [255, 255, 255]])
    result = map_noise_to_color(noise, palette)
    np.testing.assert_allclose(result, expected, atol=1)
```

- [ ] **Step 2: Run test to verify it fails**
Run: `uv run pytest tests/test_palette.py -v`
Expected: FAIL (ImportError)

- [ ] **Step 3: Implement vectorized mapping functions**
```python
def _lerp_palette(values, palette):
    palette = np.array(palette)
    n_colors = len(palette)
    if n_colors < 2:
        return np.broadcast_to(palette[0], (*values.shape, 3))
    
    # Scale values to [0, n_colors - 1]
    scaled_values = values * (n_colors - 1)
    indices = np.clip(scaled_values.astype(int), 0, n_colors - 2)
    fractions = scaled_values - indices
    
    # Expand fractions for broadcasting: (N, 1)
    fractions = fractions[..., np.newaxis]
    
    colors_a = palette[indices]
    colors_b = palette[indices + 1]
    
    return colors_a + (colors_b - colors_a) * fractions

def map_noise_to_color(noise_values, palette):
    return _lerp_palette(noise_values, palette)

def map_path_to_color(path_progress, palette):
    return _lerp_palette(path_progress, palette)

def map_angle_to_color(angles, palette):
    # Map [0, 2π] to [0, 1]
    normalized_angles = (angles % (2 * np.pi)) / (2 * np.pi)
    return _lerp_palette(normalized_angles, palette)
```

- [ ] **Step 4: Run test to verify it passes**
Run: `uv run pytest tests/test_palette.py -v`

- [ ] **Step 5: Final Commit**
```bash
git add generator/palette.py tests/test_palette.py
git commit -m "feat: implement vectorized color mapping strategies"
```
