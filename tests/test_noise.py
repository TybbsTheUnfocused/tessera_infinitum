import numpy as np
import pytest
from generator.noise import generate_noise_field, generate_vector_field

def test_noise_field_shape():
    field = generate_noise_field(shape=(100, 100), scale=10.0, octaves=4)
    assert field.shape == (100, 100)
    assert np.min(field) >= 0.0
    assert np.max(field) <= 1.0

def test_noise_determinism():
    seed = 42
    field1 = generate_noise_field(shape=(50, 50), seed=seed)
    field2 = generate_noise_field(shape=(50, 50), seed=seed)
    assert np.allclose(field1, field2)

def test_noise_uniqueness():
    field1 = generate_noise_field(shape=(50, 50), seed=100)
    field2 = generate_noise_field(shape=(50, 50), seed=101)
    assert not np.allclose(field1, field2)
