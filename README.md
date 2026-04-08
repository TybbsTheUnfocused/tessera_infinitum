# Perlin-Infinite Generator

Generative art engine for Pebble watchfaces using Perlin noise and fractal paths.

## Features
- **Unified Field Engine**: Combines Perlin noise with fractal paths (Hilbert, L-Systems).
- **Pebble-Safe Palette**: Automatic 64-color quantization for Pebble Time hardware.
- **Fluid Gradients**: Periodic color mapping with frequency modulation.
- **Overlapping Hilbert Fills**: Generate multiple distorted paths with filled enclosed regions for complex textures.
- **High Resolution**: 2048x2048 master canvas generation.
- **White Background**: High-contrast output optimized for watchface visibility.

## Installation
Requires [uv](https://github.com/astral-sh/uv).

```bash
uv sync
```

## Usage
Generate artwork using the CLI:

```bash
export PYTHONPATH=.
uv run python scripts/generate.py --seed 42 --style rainbow --color-frequency 5.0 --output generations/test.png
```

### Options
- `--seed`: Random seed for deterministic generation.
- `--style`: Color palette (`deep_sea`, `solar`, `rainbow`, `forest`, `sunset`, `cobalt`, `crimson`, `pebble`).
- `--color-frequency`: Number of times to cycle the palette along the path (higher = more modular/fluid).
- `--hilbert-fill`: Enable overlapping Hilbert curves with filled regions for "Ego - AlterEgo" style textures.
- `--stiffness`: Distortion strength of the noise field.
- `--noise-scale`: Scale of the underlying Perlin noise.
- `--fractal`: Base path type (`hilbert` or `lsystem`).
- `--order`: Hilbert curve order (for `hilbert` fractal).
- `--count`: Generate a batch of unique images starting from the seed.

## Project Structure
- `generator/`: Core engine, noise, and palette logic.
- `scripts/`: CLI tools for generation.
- `generations/`: Output directory for images and metadata.
- `tests/`: Pytest suite.
