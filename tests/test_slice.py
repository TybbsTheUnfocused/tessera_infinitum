import json
import os

import numpy as np
from PIL import Image
from generator.palette import PEBBLE_64_PALETTE
from scripts.slice import (
    convert_to_indexed, PALETTE_FLAT, PLATFORMS,
    crop_slice, encode_slice, generate_slices, run_slice,
)


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
