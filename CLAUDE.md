# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Tessera ad Infinitum — a Python generative art engine for Pebble watchfaces. Produces 2048×2048 images by combining multi-octave Perlin noise, fractal paths (Hilbert, L-system, box, Koch), and a strict Pebble 64-color palette (channels limited to 0x00, 0x55, 0xAA, 0xFF). Background is always white (#FFFFFF) for contrast. See `GEMINI.md` for the design mandates and `docs/project_spec.md` for the fuller spec.

The end-state product is **"One Generation, Infinite Watchfaces"**: a master 2048×2048 canvas is rendered on a schedule and individual Pebble watches fetch randomized crops of it. The cloud/delivery design is specified in `docs/superpowers/specs/2026-04-08-cloud-architecture-design.md` — this repo is currently the generator component of that pipeline. The orchestrator script it references (`scripts/orchestrator.py`) does not yet exist; only `scripts/generate.py` and `scripts/export_all.py` do.

Note: `README.md` is out of date relative to the engine — it only documents the original `path` mode. The engine now supports multiple generation modes (see Architecture).

## Commands

Dependency management uses `uv` (see `pyproject.toml`). `PYTHONPATH=.` is required because the `generator` package is imported as a top-level module from scripts/tests.

```bash
uv sync                                   # install deps
export PYTHONPATH=.                       # required for generator imports

# Generate a single image (writes PNG + sidecar JSON metadata)
uv run python scripts/generate.py --seed 42 --mode path --style rainbow --output generations/test.png

# Batch generate (increments seed; suffixes filename with seed)
uv run python scripts/generate.py --seed 100 --count 10 --mode fractal_pure --fractal box --output generations/batch.png

# Tests
uv run pytest                             # full suite
uv run pytest tests/test_engine.py        # single file
uv run pytest tests/test_engine.py::test_name  # single test
```

CLI modes: `path` (default), `grid`, `lsystem_growth`, `fractal_pure`, `segmented`. Each mode has its own flag group in `scripts/generate.py` — consult `--help` rather than guessing, since the README does not list them.

## Architecture

The pipeline is a single orchestrator, `generator/engine.py::Engine.generate_universe(seed, params)`, which:

1. **Generates fields** via `generator/noise.py`: a scalar `noise_field` (multi-octave Perlin via `vnoise`) and a `vector_field` of angles derived from the noise gradient. Shape is `(height, width)` — note row/col = y/x throughout.
2. **Selects a palette** from `generator/palette.py`. All final colors are snapped to the Pebble 64 palette via `to_pebble_array` before drawing. `map_path_to_color` produces periodic color cycles controlled by `color_frequency`; `map_noise_to_color` maps scalar noise values. Helpers: `lighten_color`, `darken_color`.
3. **Dispatches to a render mode** (`_render_*_mode`) which rasterizes onto a PIL `Image`:
   - `path`: draws a fractal (Hilbert or L-system) distorted by the noise+vector field via `distort_path` (bilinear sampling with `scipy.ndimage.map_coordinates`).
   - `grid`: rectilinear cellular grid thresholded by noise, styled as `rect`/`dots`/`maze`.
   - `lsystem_growth`: multiple L-system "seeds" grown with a per-pixel `collision_mask` (int-labeled) so paths avoid each other; on collision, branches turn instead of dying. Rule presets in `generator/fractals.py::LSYSTEM_RULES`.
   - `fractal_pure`: pure geometric fractals (`box`, `koch`, `hilbert_koch`) from `generator/fractals.py`. Box fractal fills only leaf cells below a size threshold.
   - `segmented`: splits canvas into a 2×2 grid, recursively instantiates a smaller `Engine` per region with a different sub-mode, then runs a connector pass over the whole canvas.
4. **Adaptive density loop** (important and easy to miss): after the primary render, while whitespace ratio > 50% and up to `MAX_PASSES=15`, the engine finds the largest connected "mostly-white" region via `scipy.ndimage` (dilation + `label` + `find_objects`), instantiates a sub-`Engine` sized to that void, and pastes an additional `fractal_pure` or `lsystem_growth` fill into it. This means final output is almost never just the chosen mode — it is the chosen mode plus iterative void-filling, which is what drives the "Ego - AlterEgo" aesthetic.
5. **Returns** `(PIL.Image, metadata_dict)`. `scripts/generate.py` writes the image and a sidecar `.json` of the metadata + params next to it.

### Conventions to preserve

- **Coordinate order:** fields are indexed `[y, x]` (rows, cols). `distort_path` deliberately builds `sample_coords` as `(y, x)` because `map_coordinates` takes `(dim1, dim2)`. Clipping to bounds is mandatory — do not remove it.
- **Pebble palette is mandatory.** Any new draw code must pass colors through `to_pebble_array` before handing them to PIL, or output will contain non-palette colors.
- **White background is a hard rule** (per `GEMINI.md`). The adaptive density loop and `_get_whitespace_ratio` both assume `(255,255,255)` is background; changing the background color will break both.
- **Seeding:** `np.random.seed(seed)` is set inside `generate_universe`. Sub-passes derive their seeds as `seed + pass_idx * 1000` (adaptive loop) or `seed + idx * 100` (segmented mode) so batch runs with `--count` stay deterministic.
- **Package import path:** scripts and tests import `from generator.X import Y`. There is no installed package entry point — always run with `PYTHONPATH=.` (or via `uv run` from the repo root).

## Outputs

`generations/` holds generated PNGs + their `.json` metadata sidecars. `showcases/` holds curated outputs. Both are safe to delete/regenerate.

## Downstream contract (cloud pipeline)

Per the cloud architecture spec, this generator is wrapped by a GitHub Actions hourly cron (`scripts/orchestrator.py`, not yet written) that: (1) derives a seed from the UTC hour, (2) renders the master 2048×2048 canvas, (3) saves it as an **indexed-color PNG** using the Pebble 64 palette, (4) **pre-crops 100 slices per color platform** (`basalt` 144×168, `chalk` 180×180 round, `emery` 200×228) at seeded random offsets, (5) encodes each slice as a raw Pebble-64 byte array (one palette index per pixel), and (6) uploads master + metadata + slices to Cloudflare R2. The edge Worker is a thin proxy that picks a slice index by hashing `client_id + hour_bucket` and serves the cached `.bin`. Historical slices are not archived — only the master is, and deterministic regeneration is the replay mechanism.

Implications for work in this repo:

- **`metadata.json` is a public versioned contract** (see `contract_version` in the spec). Renaming or removing fields is a breaking change. Adding fields is free. Load-bearing keys: `contract_version`, `generator_sha`, `seed`, `params`, `slice_manifest`, `final_whitespace`.
- **Determinism is load-bearing.** Never change seed-derivation logic (`np.random.seed(seed)` in `generate_universe`, `+pass_idx*1000` in the adaptive loop, `+idx*100` in segmented mode) without bumping `contract_version` — archived masters must byte-replay from `(generator_sha, seed, params)`.
- **Pebble 64 palette order is load-bearing.** Byte-array slices reference palette *indices*, not RGB. Reordering `PEBBLE_64_PALETTE` silently corrupts every client's color mapping. If you must reorder, bump `contract_version`.
- **Canvas must remain exactly 2048×2048 RGB-white-background.** The orchestrator's indexed-PNG conversion and the slice offsets in `slice_manifest` assume this. Alpha channels, non-square canvases, or off-palette antialiasing will break the byte-array encode.
- **Target platforms are color only** — basalt, chalk, emery. B&W platforms (aplite, diorite) are explicitly out of scope. Don't add code paths for 1-bit output.
