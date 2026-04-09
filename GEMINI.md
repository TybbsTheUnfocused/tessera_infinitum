# Tessera ad Infinitum: Project Context

## Project Overview
A generative art watchface for Pebble, utilizing multi-octave Perlin noise and an edge-compute hybrid architecture.

## Core Mandates
- **Palette Rigor:** Strictly adhere to the [Pebble 64-color palette](https://developer.rebble.io/developer.pebble.com/guides/tools-and-resources/color-picker/index.html) (channels: 0x00, 0x55, 0xAA, 0xFF).
- **Background:** Always use White (#FFFFFF) for high contrast.
- **Color Mapping:** Use `color_frequency` to cycle through palettes for fluid, modular gradients.
- **Region Filling:** Support `hilbert_fill` mode to identify and shade enclosed regions between multiple distorted paths.
- **Storage:** All art generations and metadata are stored in `generations/`.
- **Efficiency:** Python generation time < 10s for 2048x2048 canvases.

## Available Palettes
`deep_sea`, `solar`, `rainbow`, `forest`, `sunset`, `cobalt`, `crimson`, `pebble`.

## Current Phase: Algorithmic Prototyping
Focusing on the Python-based artwork generation script to achieve the "Ego - AlterEgo" aesthetic by Laurens Lapre using noise and vector fields.

## Tech Stack
- **Backend:** Python (Perlin/Simplex noise, NumPy, PIL/Pillow, SciPy).
- **Middleware:** PebbleKit JS (Canvas API/Image manipulation).
- **Frontend:** Pebble C (Rebble SDK).
