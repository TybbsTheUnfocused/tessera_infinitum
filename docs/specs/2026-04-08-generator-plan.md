# Perlin-Infinite Generator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a parameterized Python engine to generate 2048x2048 procedural artwork using noise and fractals.

**Architecture:** A "Unified Field" approach where multi-octave Perlin noise distorts and colors recursive fractal paths (Hilbert, Dragon, etc.).

**Tech Stack:** Python 3.12+, `uv`, `numpy`, `pillow`, `vnoise`.

---

## File Structure

- `generator/`: Core logic package
  - `__init__.py`
  - `noise.py`: Noise and vector field generation (NumPy)
  - `fractals.py`: L-System and space-filling curve logic
  - `palette.py`: Pebble 64-color palette and mapping strategies
  - `engine.py`: Orchestration of the generation pipeline
- `scripts/`: Operational scripts
  - `generate.py`: CLI entry point for testing and production
- `tests/`: Test suite
  - `test_noise.py`
  - `test_fractals.py`
  - `test_palette.py`
- `pyproject.toml`: Project dependencies and metadata

---

### Task 1: Environment & Project Setup

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`

- [ ] **Step 1: Initialize git repository**
```bash
git init
```

- [ ] **Step 2: Create pyproject.toml with dependencies**
```toml
[project]
name = "perlin-infinite-generator"
version = "0.1.0"
dependencies = [
    "numpy",
    "pillow",
    "vnoise",
    "pytest"
]
```

- [ ] **Step 3: Create .venv and install dependencies using uv**
```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```

- [ ] **Step 4: Create .gitignore**
```text
.venv/
__pycache__/
*.png
*.json
.pytest_cache/
```

- [ ] **Step 5: Commit setup**
```bash
git add pyproject.toml .gitignore
git commit -m "chore: initial project setup"
```

---

### Task 2: Noise Core & Vector Field

**Files:**
- Create: `generator/noise.py`
- Test: `tests/test_noise.py`

- [ ] **Step 1: Write test for noise generation**
```python
import numpy as np
from generator.noise import generate_noise_field

def test_noise_field_shape():
    field = generate_noise_field(shape=(100, 100))
    assert field.shape == (100, 100)
    assert np.min(field) >= 0.0
    assert np.max(field) <= 1.0
```

- [ ] **Step 2: Implement generate_noise_field**
Using `vnoise` for vectorized noise generation.

- [ ] **Step 3: Write test for vector field (Angles)**
```python
def test_vector_field_angles():
    from generator.noise import generate_vector_field
    noise = np.random.rand(10, 10)
    vectors = generate_vector_field(noise)
    assert np.all(vectors >= 0)
    assert np.all(vectors <= 2 * np.pi)
```

- [ ] **Step 4: Implement generate_vector_field**

- [ ] **Step 5: Run tests**
```bash
pytest tests/test_noise.py
```

- [ ] **Step 6: Commit**
```bash
git add generator/noise.py tests/test_noise.py
git commit -m "feat: add noise and vector field generation"
```

---

### Task 3: Fractal Path Logic

**Files:**
- Create: `generator/fractals.py`
- Test: `tests/test_fractals.py`

- [ ] **Step 1: Write test for Hilbert curve**
```python
def test_hilbert_points():
    from generator.fractals import get_hilbert_curve
    points = get_hilbert_curve(order=2, size=100)
    assert len(points) == 16
```

- [ ] **Step 2: Implement Hilbert curve generator**

- [ ] **Step 3: Write test for L-System parser (Dragon curve)**
```python
def test_dragon_curve():
    from generator.fractals import get_l_system
    # Dragon curve rules
    rules = {"X": "X+YF+", "Y": "-FX-Y"}
    points = get_l_system(axiom="FX", rules=rules, iterations=2)
    assert len(points) > 0
```

- [ ] **Step 4: Implement L-System parser**

- [ ] **Step 5: Run tests**
```bash
pytest tests/test_fractals.py
```

- [ ] **Step 6: Commit**
```bash
git add generator/fractals.py tests/test_fractals.py
git commit -m "feat: add fractal path generators"
```

---

### Task 4: Unified Field Distortion

**Files:**
- Modify: `generator/engine.py`
- Test: `tests/test_engine.py`

- [ ] **Step 1: Write test for path distortion**
```python
def test_distort_path():
    from generator.engine import distort_path
    path = [(0, 0), (10, 10)]
    noise_field = np.zeros((100, 100)) # Simple case
    distorted = distort_path(path, noise_field, stiffness=1.0)
    assert len(distorted) == len(path)
```

- [ ] **Step 2: Implement distort_path using bilinear interpolation**
Must use `scipy.ndimage.map_coordinates` (add `scipy` to `pyproject.toml`) to sample the noise field at arbitrary path coordinates.

- [ ] **Step 3: Run tests**
```bash
pytest tests/test_engine.py
```

- [ ] **Step 4: Commit**
```bash
git add generator/engine.py tests/test_engine.py
git commit -m "feat: implement noise-driven path distortion with bilinear interpolation"
```

---

### Task 5: Pebble Palette & Color Mapping

**Files:**
- Create: `generator/palette.py`
- Test: `tests/test_palette.py`

- [ ] **Step 1: Write test for Pebble quantization**
```python
def test_pebble_color():
    from generator.palette import to_pebble_color
    assert to_pebble_color((10, 80, 200)) == (0, 0x55, 0xAA)
```

- [ ] **Step 2: Implement to_pebble_color and PEBBLE_64_PALETTE**

- [ ] **Step 3: Define Palette Presets**
Implement `PALETTE_PRESETS` (e.g., `DEEP_SEA` [Blues/Greens], `SOLAR` [Reds/Yellows]) using Pebble-safe colors.

- [ ] **Step 4: Write test for Noise-to-Color mapping**
```python
def test_map_noise_to_color():
    from generator.palette import map_noise_to_color
    colors = [(255, 255, 255), (0, 0, 0)]
    val = 0.5
    res = map_noise_to_color(val, colors)
    # Check if result is a valid Pebble color
```

- [ ] **Step 5: Implement mapping strategies (Noise, Path, Angle)**
Must use NumPy vectorization.

- [ ] **Step 6: Run tests**
```bash
pytest tests/test_palette.py
```

- [ ] **Step 7: Commit**
```bash
git add generator/palette.py tests/test_palette.py
git commit -m "feat: add pebble palette and vectorized color mapping"
```

---

### Task 6: Orchestration & Export

**Files:**
- Create: `scripts/generate.py`
- Modify: `generator/engine.py`

- [ ] **Step 1: Implement Pipeline Orchestrator in engine.py**
Combines Noise -> Path -> Distortion -> Color -> Rasterization.

- [ ] **Step 2: Implement generate.py CLI**
Accepts `--seed`, `--output`, and style params.

- [ ] **Step 3: Implement Metadata Generation**
Export `metadata.json` alongside the PNG (seed, parameters, bounds).

- [ ] **Step 4: Manual Verification**
Run `python scripts/generate.py --output test_universe.png` and inspect the result.

- [ ] **Step 5: Commit**
```bash
git add scripts/generate.py generator/engine.py
git commit -m "feat: complete generator orchestration and CLI with metadata export"
```
