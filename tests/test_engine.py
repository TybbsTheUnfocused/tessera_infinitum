import numpy as np
import pytest
from generator.engine import distort_path, Engine
from PIL import Image

def test_distort_path_zero():
    path = [(0, 0), (10, 10)]
    noise_field = np.zeros((100, 100)) # Simple case
    vector_field = np.zeros((100, 100))
    distorted = distort_path(path, noise_field, vector_field, stiffness=10.0)
    assert len(distorted) == len(path)
    # With zero noise/vectors, it should stay the same
    assert distorted[0] == (0, 0)
    assert distorted[1] == (10, 10)

def test_distort_path_with_values():
    path = [(0, 0)]
    noise_field = np.ones((10, 10)) # All noise = 1
    vector_field = np.full((10, 10), np.pi / 2) # All angle = pi/2 (up, +y)
    # P' = P + (1 * [cos(pi/2), sin(pi/2)] * 5)
    # P' = (0, 0) + (1 * [0, 1] * 5) = (0, 5)
    distorted = distort_path(path, noise_field, vector_field, stiffness=5.0)
    assert distorted[0] == (pytest.approx(0), pytest.approx(5))

def test_distort_path_interpolation():
    # Test bilinear interpolation
    noise_field = np.zeros((10, 10))
    noise_field[0, 0] = 0
    noise_field[0, 1] = 1
    # Sampling at x=0.5, y=0 should give 0.5 noise if noise_field[row, col] is [y, x]
    
    vector_field = np.zeros((10, 10)) # all angle = 0
    
    path = [(0.5, 0)]
    # x=0.5, y=0.
    # sample_coords[0] = y = 0
    # sample_coords[1] = x = 0.5
    # map_coordinates(noise_field, [[0], [0.5]]) should give 0.5
    
    distorted = distort_path(path, noise_field, vector_field, stiffness=10.0)
    # dx = 0.5 * cos(0) * 10 = 5
    # dy = 0.5 * sin(0) * 10 = 0
    # P' = (0.5 + 5, 0 + 0) = (5.5, 0)
    assert distorted[0] == (pytest.approx(5.5), pytest.approx(0))

def test_distort_path_clipping():
    # Test clipping
    noise_field = np.ones((10, 10)) * 2
    vector_field = np.zeros((10, 10))
    
    # Point outside bounds (100, 100) should be clipped to (9, 9)
    path = [(100, 100)]
    distorted = distort_path(path, noise_field, vector_field, stiffness=1.0)
    # noise at (9,9) is 2, angle 0.
    # P' = (100, 100) + (2 * [1, 0] * 1) = (102, 100)
    assert distorted[0] == (pytest.approx(102), pytest.approx(100))

def test_engine_generate_universe():
    engine = Engine(size=(100, 100))
    seed = 42
    params = {
        'palette': 'solar',
        'stiffness': 1.0,
        'noise_scale': 1.0,
        'fractal_type': 'hilbert',
        'order': 2
    }
    img, metadata = engine.generate_universe(seed, params)
    
    assert isinstance(img, Image.Image)
    assert img.size == (100, 100)
    assert metadata['seed'] == seed
    assert metadata['params'] == params
    assert 'bounding_box' in metadata

def test_engine_lsystem():
    engine = Engine(size=(100, 100))
    seed = 42
    params = {
        'palette': 'deep_sea',
        'stiffness': 1.0,
        'noise_scale': 1.0,
        'fractal_type': 'lsystem',
        'iterations': 1
    }
    img, metadata = engine.generate_universe(seed, params)
    
    assert isinstance(img, Image.Image)
    assert img.size == (100, 100)
    assert metadata['params']['fractal_type'] == 'lsystem'
