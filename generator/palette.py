import numpy as np

PEBBLE_CHANNELS = np.array([0x00, 0x55, 0xAA, 0xFF])

def to_pebble_color(rgb_tuple):
    """
    Map an arbitrary RGB tuple to the nearest Pebble-safe color.
    Each channel must be one of: 0x00, 0x55, 0xAA, 0xFF.
    
    Args:
        rgb_tuple (tuple): (R, G, B) tuple.
        
    Returns:
        tuple: (R, G, B) tuple in Pebble-safe range.
    """
    return tuple(PEBBLE_CHANNELS[np.abs(PEBBLE_CHANNELS - c).argmin()] for c in rgb_tuple)

def to_pebble_array(colors_array):
    """
    Vectorized version of to_pebble_color.
    
    Args:
        colors_array (np.ndarray): Shape (N, 3) or (H, W, 3).
        
    Returns:
        np.ndarray: Same shape, with values quantized to Pebble channels.
    """
    # Reshape to 1D channel array to use broadcasting
    diff = np.abs(colors_array[..., np.newaxis] - PEBBLE_CHANNELS)
    indices = np.argmin(diff, axis=-1)
    return PEBBLE_CHANNELS[indices]

PEBBLE_64_PALETTE = np.array([(r, g, b) for r in PEBBLE_CHANNELS for g in PEBBLE_CHANNELS for b in PEBBLE_CHANNELS])

# High-contrast Pebble-safe presets
# DEEP_SEA: Blues and Greens
DEEP_SEA = np.array([
    (0x00, 0x00, 0x55), # OxfordBlue
    (0x00, 0x55, 0xAA), # CobaltBlue
    (0x00, 0xAA, 0xAA), # TiffanyBlue
    (0x00, 0xFF, 0xAA), # Malachite
    (0x55, 0xFF, 0x55), # ScreaminGreen
    (0xAA, 0xFF, 0xAA), # MintGreen
])

# SOLAR: Reds, Oranges, Yellows
SOLAR = np.array([
    (0x55, 0x00, 0x00), # BulgarianRose
    (0xAA, 0x00, 0x00), # DarkRed
    (0xFF, 0x00, 0x00), # Red
    (0xFF, 0x55, 0x00), # Orange
    (0xFF, 0xAA, 0x00), # ChromeYellow
    (0xFF, 0xFF, 0x00), # Yellow
])

def _interpolate_palette(values, palette):
    """
    Helper to interpolate values [0, 1] across a palette of colors.
    
    Args:
        values (np.ndarray): Normalized values [0, 1].
        palette (np.ndarray): Array of RGB colors.
        
    Returns:
        np.ndarray: Interpolated RGB colors.
    """
    num_colors = len(palette)
    if num_colors < 2:
        return np.repeat(palette, len(values), axis=0)
    
    # Scale values to [0, num_colors - 1]
    scaled_values = values * (num_colors - 1)
    idx_low = np.floor(scaled_values).astype(int)
    idx_high = np.ceil(scaled_values).astype(int)
    
    # Clip indices to stay within range
    idx_low = np.clip(idx_low, 0, num_colors - 1)
    idx_high = np.clip(idx_high, 0, num_colors - 1)
    
    # Fractional part for interpolation
    frac = scaled_values - idx_low
    
    # Reshape frac for broadcasting with RGB
    frac = frac[..., np.newaxis]
    
    # Interpolate
    colors = (1 - frac) * palette[idx_low] + frac * palette[idx_high]
    
    return colors.astype(np.uint8)

def map_noise_to_color(noise_values, palette):
    """
    Map noise values [0, 1] to a color in the palette.
    
    Args:
        noise_values (np.ndarray): 2D noise field or 1D array.
        palette (np.ndarray): RGB colors.
        
    Returns:
        np.ndarray: RGB values.
    """
    return _interpolate_palette(noise_values, palette)

def map_path_to_color(path_length, palette):
    """
    Map progress [0, 1] along a path to colors.
    
    Args:
        path_length (int): Number of points in the path.
        palette (np.ndarray): RGB colors.
        
    Returns:
        np.ndarray: Array of RGB colors for each point.
    """
    progress = np.linspace(0, 1, path_length)
    return _interpolate_palette(progress, palette)

def map_angle_to_color(angles, palette):
    """
    Map angles [0, 2π] to colors in the palette.
    
    Args:
        angles (np.ndarray): 2D field of angles or 1D array.
        palette (np.ndarray): RGB colors.
        
    Returns:
        np.ndarray: RGB values.
    """
    # Normalize angles to [0, 1]
    norm_angles = (angles % (2 * np.pi)) / (2 * np.pi)
    return _interpolate_palette(norm_angles, palette)
