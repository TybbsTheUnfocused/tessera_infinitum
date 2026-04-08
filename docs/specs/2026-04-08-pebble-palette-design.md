# Design Specification: Pebble 64-color Palette & Mapping

## Objective
Implement Pebble 64-color quantization and vectorized mapping strategies for the Perlin-Infinite generator.

## 1. Pebble 64-color Logic
- **Channels:** Each RGB channel must be one of `0x00`, `0x55`, `0xAA`, `0xFF`.
- **Quantization:** `to_pebble_color(rgb_tuple)` maps arbitrary (R, G, B) to the nearest Pebble color.
  - This is done by rounding each channel (0-255) to the nearest of {0, 85, 170, 255}.
- **Palette Presets:**
  - `DEEP_SEA`: [Blues/Greens] (Pebble-safe RGB tuples)
  - `SOLAR`: [Reds/Yellows] (Pebble-safe RGB tuples)
  - `PEBBLE_64_PALETTE`: A list of all 64 possible combinations.

## 2. Vectorized Mapping Strategies
All mapping functions must support NumPy arrays of inputs for performance.

- `map_noise_to_color(noise_values, palette)`:
  - Maps normalized noise values [0, 1] to a color in the palette using linear interpolation (lerp).
- `map_path_to_color(path_progress, palette)`:
  - Maps progress [0, 1] along the path to a color using lerp.
- `map_angle_to_color(angles, palette)`:
  - Maps angles [0, 2π] to a color using lerp.

## 3. Implementation Details
- **File:** `generator/palette.py`
- **Testing:** `tests/test_palette.py`
- **Performance:** Use NumPy's vectorization for mapping strategies.

## 4. Success Criteria
- [ ] Quantization correctly maps RGB values to the nearest Pebble color.
- [ ] Palette presets (`DEEP_SEA`, `SOLAR`) are correctly defined with Pebble-safe colors.
- [ ] Vectorized mapping strategies correctly interpolate between colors in the palette.
- [ ] All functions handle NumPy arrays and single values efficiently.
