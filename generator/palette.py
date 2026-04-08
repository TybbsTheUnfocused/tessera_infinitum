import numpy as np

PEBBLE_CHANNELS = [0x00, 0x55, 0xAA, 0xFF]

def to_pebble_color(rgb_tuple):
    """
    Map an arbitrary RGB tuple to the nearest Pebble-safe color.
    Each channel must be one of: 0x00, 0x55, 0xAA, 0xFF.
    
    Args:
        rgb_tuple (tuple): (R, G, B) tuple.
        
    Returns:
        tuple: (R, G, B) tuple in Pebble-safe range.
    """
    return tuple(min(PEBBLE_CHANNELS, key=lambda x: abs(x - c)) for c in rgb_tuple)

PEBBLE_64_PALETTE = [(r, g, b) for r in PEBBLE_CHANNELS for g in PEBBLE_CHANNELS for b in PEBBLE_CHANNELS]
