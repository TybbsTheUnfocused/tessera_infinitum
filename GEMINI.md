# Perlin-Infinite: Project Context

## Project Overview
A generative art watchface for Pebble, utilizing multi-octave Perlin noise and an edge-compute hybrid architecture.

## Core Mandates
- **Palette Rigor:** Strictly adhere to the [Pebble 64-color palette](https://developer.rebble.io/developer.pebble.com/guides/tools-and-resources/color-picker/index.html) for color watches and 1-bit dithering for monochrome.
- **Deterministic Cropping:** Middleware must use `watchToken` + `hour` for deterministic cropping of the master canvas.
- **Efficiency:** The Python generator must produce high-resolution (e.g., 2048x2048) canvases hourly.

## Current Phase: Algorithmic Prototyping
Focusing on the Python-based artwork generation script to achieve the "Ego - AlterEgo" aesthetic by Laurens Lapre using noise and vector fields.

## Tech Stack
- **Backend:** Python (Perlin/Simplex noise, NumPy, PIL/Pillow).
- **Middleware:** PebbleKit JS (Canvas API/Image manipulation).
- **Frontend:** Pebble C (Rebble SDK).
