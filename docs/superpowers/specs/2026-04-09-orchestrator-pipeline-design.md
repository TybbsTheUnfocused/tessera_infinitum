# Orchestrator Pipeline Design

**Date:** 2026-04-09
**Status:** Approved
**Subsystem:** 1 of 5 (Orchestrator → Slicer → Upload → GitHub Actions)
**Parent spec:** `2026-04-08-cloud-architecture-design.md`

## 1. Overview

Three modular scripts chained by the filesystem, plus a GitHub Actions workflow that runs them hourly. Each script has a single responsibility and communicates only through files in a shared `--output-dir`. No script imports from another.

```
orchestrate.py          slice.py                    upload.py
──────────────          ────────                    ─────────
seed from UTC hour      reads canvas.png +          reads output dir
recipe selection        metadata.json               uploads latest/* to R2
Engine.generate()       indexed-PNG conversion      archives master to R2
                        100 crops × 3 platforms
writes:                 raw byte-array encode       env-var auth
  canvas.png                                        (R2_ACCESS_KEY_ID, etc.)
  metadata.json         writes:
                          canvas_indexed.png
                          slices/{platform}/{N}.bin
                          slices/index.json
```

All scripts accept `--output-dir` (default: `output/`).

## 2. orchestrate.py — Seed Derivation + Curated Rendering

### 2.1 Seed derivation

```python
seed = hash("tessera-{YYYYMMDDHH}") & 0x7FFFFFFF  # positive 31-bit int
```

Deterministic from the UTC hour. An optional `--seed` flag overrides this for testing/reproducibility.

### 2.2 Recipe system

The orchestrator maintains a deck of **19 structural recipes**, each a frozen param dict derived from the proven combinations in `scripts/export_all.py`. A recipe fixes the generation mode and its mode-specific params. Two things are always randomized per run (seeded):

- **Palette:** uniform random from all 8 styles (`deep_sea`, `solar`, `rainbow`, `forest`, `sunset`, `cobalt`, `crimson`, `pebble`).
- **Terminal shape** (for lsystem_growth recipes): uniform random `circle` / `square`.

### 2.3 Recipe deck

| # | Mode | Variant | Key params | Weight |
|---|------|---------|-----------|--------|
| 1 | `grid` | rect | `grid_res`=48, `cell_padding`=0.2, `grid_style`=rect | 1.0 |
| 2 | `grid` | dots | `grid_res`=48, `cell_padding`=0.2, `grid_style`=dots | 1.0 |
| 3 | `grid` | maze | `grid_res`=48, `cell_padding`=0.2, `grid_style`=maze | 1.0 |
| 4 | `lsystem_growth` | dragon | `iterations`=10, `step_size`=25, `num_seeds`=40, `node_size`=8, `line_width`=5 | 1.0 |
| 5 | `lsystem_growth` | gosper | `iterations`=4, `step_size`=30, `num_seeds`=30, `node_size`=8, `line_width`=5 | 0.5 |
| 6 | `lsystem_growth` | sierpinski | `iterations`=6, `step_size`=35, `num_seeds`=25, `node_size`=8, `line_width`=5 | 1.0 |
| 7 | `lsystem_growth` | plant | `iterations`=5, `step_size`=25, `num_seeds`=30, `node_size`=8, `line_width`=5 | 0.5 |
| 8 | `lsystem_growth` + `composite` | dragon | same as #4 + grid base | 3.0 |
| 9 | `lsystem_growth` + `composite` | gosper | same as #5 + grid base | 3.0 |
| 10 | `lsystem_growth` + `composite` | sierpinski | same as #6 + grid base | 3.0 |
| 11 | `lsystem_growth` + `composite` | plant | same as #7 + grid base | 3.0 |
| 12 | `fractal_pure` | box | `order`=7, `size`=2048 | 1.0 |
| 13 | `fractal_pure` | koch | `order`=5, `size`=2048 | 1.0 |
| 14 | `fractal_pure` | hilbert_koch | `order`=5, `size`=2048 | 1.0 |
| 15 | `fractal_pure` + `composite` | hilbert_koch | same as #14 + grid base | 0.5 |
| 16 | `fractal_pure` + `composite` | koch | same as #13 + grid base | 3.0 |
| 17 | `fractal_pure` + `composite` | box | same as #12 + grid base | 0.5 |
| 18 | `fractal_pure` | box (unfilled) | `order`=7, `size`=2048, `fill_boxes`=False | 1.0 |
| 19 | `segmented` | default | default params | 3.0 |

**Weight distribution:** ~60% hybrid/segmented, ~30% standard, ~10% lower-weighted. Weights are normalized to probabilities at selection time.

### 2.4 Rendering

```python
engine = Engine(size=(2048, 2048))
img, metadata = engine.generate_universe(seed, resolved_params)
```

The adaptive density loop inside `generate_universe` (whitespace < 50%, up to 15 passes) is the quality backstop — it fills voids with sub-renders regardless of which recipe was selected.

### 2.5 Output

- `{output_dir}/canvas.png` — full 2048×2048 RGB PNG
- `{output_dir}/metadata.json` — full contract metadata including:
  - `contract_version`: 1
  - `generator_sha`: git SHA at render time
  - `generated_at_utc`: ISO 8601 timestamp
  - `seed`: the integer seed used
  - `recipe_name`: human-readable recipe identifier (e.g., `"hybrid_growth_dragon"`)
  - `params`: the fully resolved param dict passed to `generate_universe`
  - `final_whitespace`, `adaptive_passes`: from engine metadata

### 2.6 CLI

```
usage: orchestrate.py [--seed SEED] [--output-dir DIR] [--recipe NAME]
```

- `--seed`: override UTC-hour derivation
- `--output-dir`: default `output/`
- `--recipe`: force a specific recipe by name (for testing)

## 3. slice.py — Indexed-PNG Conversion + Pre-Cropping

### 3.1 Indexed-PNG conversion

Converts `canvas.png` to an indexed-color PNG with `PEBBLE_64_PALETTE` as the fixed palette. Uses `PIL.Image.quantize()` with a custom palette image built from `PEBBLE_64_PALETTE` (not `Image.ADAPTIVE`, which would reorder indices). This preserves the canonical palette ordering so that byte-array indices map directly to `PEBBLE_64_PALETTE[i]`. Saved as `{output_dir}/canvas_indexed.png`. This is the version archived to R2.

### 3.2 Target platforms (color only)

| Platform | Device | Resolution | Shape | Crop method |
|----------|--------|-----------|-------|-------------|
| basalt | Pebble Time / Steel | 144×168 | rect | direct crop |
| chalk | Pebble Time Round | 180×180 | round | crop + circular alpha mask (outside = index 0) |
| emery | Pebble Time 2 | 200×228 | rect | direct crop |

Primary test platform: **basalt** (Pebble Time).

### 3.3 Slice generation

For each platform, generates N crops (default 100) at random `(x, y)` offsets seeded from the master seed (read from `metadata.json`). Offsets are clamped so no crop exceeds the 2048×2048 canvas bounds.

Each crop is encoded as a **flat byte array** — one byte per pixel, value = index into `PEBBLE_64_PALETTE` (0..63). File size is exactly `W × H` bytes per slice.

### 3.4 Output

- `{output_dir}/canvas_indexed.png`
- `{output_dir}/slices/basalt/{000..099}.bin`
- `{output_dir}/slices/chalk/{000..099}.bin`
- `{output_dir}/slices/emery/{000..099}.bin`
- `{output_dir}/slices/index.json` — manifest:

```json
{
  "count_per_platform": 100,
  "platforms": {
    "basalt": { "w": 144, "h": 168, "shape": "rect" },
    "chalk":  { "w": 180, "h": 180, "shape": "round" },
    "emery":  { "w": 200, "h": 228, "shape": "rect" }
  },
  "offsets": {
    "basalt": [[x0, y0], [x1, y1], ...],
    "chalk":  [[x0, y0], ...],
    "emery":  [[x0, y0], ...]
  }
}
```

### 3.5 CLI

```
usage: slice.py [--output-dir DIR] [--count N] [--platform PLATFORM]
```

- `--output-dir`: default `output/`
- `--count`: slices per platform, default 100 (use 1 for POC)
- `--platform`: generate slices for one platform only (default: all three)

## 4. upload.py — R2 Upload

### 4.1 Responsibility

Pure I/O. Reads the output dir, uploads to Cloudflare R2 using `boto3` with S3-compatible endpoint.

### 4.2 R2 layout

```
latest/
  canvas.png                        # indexed-color master
  metadata.json                     # generation contract
  slices/
    basalt/{000..099}.bin
    chalk/{000..099}.bin
    emery/{000..099}.bin
    index.json
archive/
  YYYY/MM/DD/HH-canvas.png          # master only
  YYYY/MM/DD/HH-metadata.json       # slices NOT archived
```

`latest/slices/*` is overwritten in place each hour. Only the master + metadata are archived.

### 4.3 Authentication

Environment variables: `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`, `R2_ACCOUNT_ID`.

POC uses static GitHub secrets. Production target is OIDC federation.

### 4.4 CLI

```
usage: upload.py [--output-dir DIR] [--skip-archive] [--dry-run]
```

- `--output-dir`: default `output/`
- `--skip-archive`: upload to `latest/` only
- `--dry-run`: print upload plan without touching R2

## 5. GitHub Actions Workflow

`.github/workflows/generate.yml`

### 5.1 Triggers

```yaml
on:
  schedule:
    - cron: '0 * * * *'
  workflow_dispatch:
    inputs:
      seed:
        description: 'Override seed (skip UTC-hour derivation)'
        required: false
```

### 5.2 Job steps

1. Checkout repo
2. Set up Python + `uv sync`
3. `uv run python scripts/orchestrate.py --output-dir output/` (with optional `--seed` from dispatch input)
4. `uv run python scripts/slice.py --output-dir output/ --count 100`
5. `uv run python scripts/upload.py --output-dir output/`

### 5.3 Failure mode

If any step fails, the workflow fails and the previous hour's `latest/` remains in R2. No partial uploads in POC — sequential upload is acceptable for a single consumer.

### 5.4 SLA

GitHub scheduled workflows are best-effort (5-15min delays common, paused after 60 days of inactivity). Acceptable for hourly cadence.

## 6. Dependencies

New Python dependencies required:
- `boto3` — for R2 upload via S3-compatible API (used only by `upload.py`)

No new dependencies for `orchestrate.py` or `slice.py` — they use only what the generator already has (numpy, Pillow, scipy).
