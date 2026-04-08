import numpy as np
import pytest
from generator.noise import generate_noise_field, generate_vector_field

def test_noise_field_shape():
    field = generate_noise_field(shape=(100, 100), scale=10.0, octaves=4)
    assert field.shape == (100, 100)
    assert np.min(field) >= 0.0
    assert np.max(field) <= 1.0

def test_vector_field_angles():
    noise = np.random.rand(10, 10)
    vectors = generate_vector_field(noise)
    assert vectors.shape == (10, 10)
    assert np.all(vectors >= 0)
    assert np.all(vectors <= 2 * np.pi)
