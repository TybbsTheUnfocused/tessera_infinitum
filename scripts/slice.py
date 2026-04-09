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
