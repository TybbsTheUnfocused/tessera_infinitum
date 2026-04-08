import numpy as np
import pytest
from generator.palette import to_pebble_color

def test_to_pebble_color():
    # Test perfect matches
    assert to_pebble_color((0, 0, 0)) == (0, 0, 0)
    assert to_pebble_color((85, 85, 85)) == (85, 85, 85)
    assert to_pebble_color((170, 170, 170)) == (170, 170, 170)
    assert to_pebble_color((255, 255, 255)) == (255, 255, 255)
    
    # Test quantization to nearest
    assert to_pebble_color((10, 80, 200)) == (0, 85, 170)
    assert to_pebble_color((250, 40, 130)) == (255, 0, 170)
