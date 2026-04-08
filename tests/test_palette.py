import numpy as np
import pytest
from generator.palette import (
    to_pebble_color, 
    to_pebble_array, 
    DEEP_SEA, 
    SOLAR, 
    map_noise_to_color,
    map_path_to_color,
    map_angle_to_color
)

def test_pebble_color_quantization():
    # 0x55 = 85, 0xAA = 170
    assert to_pebble_color((10, 80, 200)) == (0, 85, 170)
    assert to_pebble_color((250, 150, 40)) == (255, 170, 0)

def test_to_pebble_array():
    arr = np.array([
        [10, 80, 200],
        [250, 150, 40]
    ])
    expected = np.array([
        [0, 85, 170],
        [255, 170, 0]
    ])
    res = to_pebble_array(arr)
    assert np.array_equal(res, expected)

def test_presets_are_pebble_safe():
    pebble_channels = [0, 85, 170, 255]
    all_colors = np.vstack([DEEP_SEA, SOLAR])
    for color in all_colors:
        assert all(c in pebble_channels for c in color)

def test_mapping_strategies():
    palette = DEEP_SEA
    
    # Noise mapping
    noise = np.array([0.0, 0.5, 1.0])
    colors = map_noise_to_color(noise, palette)
    assert colors.shape == (3, 3)
    assert np.array_equal(colors[0], palette[0])
    assert np.array_equal(colors[-1], palette[-1])
    
    # Path mapping
    colors_path = map_path_to_color(10, palette)
    assert colors_path.shape == (10, 3)
    
    # Angle mapping
    angles = np.array([0, np.pi, 2*np.pi])
    colors_angles = map_angle_to_color(angles, palette)
    assert colors_angles.shape == (3, 3)
    # 0 and 2pi should map to the same color (palette[0])
    assert np.array_equal(colors_angles[0], palette[0])
    assert np.array_equal(colors_angles[2], palette[0])
