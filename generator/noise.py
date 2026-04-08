import numpy as np

# Workaround for vnoise dependency on pkg_resources which is missing in some environments
try:
    import pkg_resources
except ImportError:
    import sys
    from unittest.mock import MagicMock
    mock_pkg = MagicMock()
    mock_pkg.get_distribution.return_value.version = "0.1.0"
    sys.modules["pkg_resources"] = mock_pkg

import vnoise

def generate_noise_field(shape=(100, 100), scale=10.0, octaves=4):
    """
    Generate a 2D noise field using vnoise.
    
    Args:
        shape (tuple): Shape of the field (rows, cols).
        scale (float): Scale of the noise.
        octaves (int): Number of octaves for fractal noise.
        
    Returns:
        np.ndarray: 2D noise field with values in [0, 1].
    """
    noise = vnoise.Noise()
    res_y, res_x = shape
    
    # Generate coordinates for x and y
    # x corresponds to columns (width), y to rows (height)
    # vnoise.noise2(x, y) returns shape (len(x), len(y))
    # So we should pass (np.linspace for res_y, np.linspace for res_x) 
    # OR transpose the result.
    
    y_coords = np.linspace(0, scale, res_y)
    x_coords = np.linspace(0, scale, res_x)
    
    # Generate 2D noise field. With grid_mode=True (default), 
    # it returns shape (len(y_coords), len(x_coords)) which matches (res_y, res_x)
    field = noise.noise2(y_coords, x_coords, octaves=octaves)
    
    # Normalize to [0, 1]
    f_min, f_max = field.min(), field.max()
    if f_max > f_min:
        field = (field - f_min) / (f_max - f_min)
    else:
        field = np.zeros_like(field)
        
    return field

def generate_vector_field(noise_field):
    """
    Map normalized noise values [0, 1] to angles [0, 2π].
    
    Args:
        noise_field (np.ndarray): 2D noise field.
        
    Returns:
        np.ndarray: 2D field of angles.
    """
    return noise_field * 2 * np.pi
