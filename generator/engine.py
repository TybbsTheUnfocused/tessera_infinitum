import numpy as np
from scipy.ndimage import map_coordinates, binary_fill_holes
from PIL import Image, ImageDraw
from generator.noise import generate_noise_field, generate_vector_field
from generator.fractals import get_hilbert_curve, get_l_system
from generator.palette import (
    PEBBLE_64_PALETTE, DEEP_SEA, SOLAR, RAINBOW, FOREST, SUNSET, COBALT, CRIMSON,
    map_path_to_color, to_pebble_array, lighten_color
)

def distort_path(path, noise_field, vector_field, stiffness=1.0):
    """
    Apply noise-driven path distortion using bilinear interpolation.
    
    Args:
        path: List of (x, y) tuples.
        noise_field: 2D array of noise values.
        vector_field: 2D array of angles (in radians).
        stiffness: Float multiplier for the distortion.
        
    Returns:
        List of distorted (x, y) tuples.
    """
    if not path:
        return []
    
    # Convert path to (N, 2) array
    pts = np.array(path, dtype=float)
    x = pts[:, 0]
    y = pts[:, 1]
    
    # noise_field.shape is (height, width) -> (rows, cols)
    # So height is Y dimension, width is X dimension
    h, w = noise_field.shape
    
    # map_coordinates expects coordinates in (dim1, dim2, ...) order.
    # For a 2D array (H, W), dim1 is row (Y) and dim2 is column (X).
    # We clip coordinates to bounds to avoid out-of-bounds sampling errors.
    sample_coords = np.empty((2, len(path)))
    sample_coords[0] = np.clip(y, 0, h - 1) # Y corresponds to rows
    sample_coords[1] = np.clip(x, 0, w - 1) # X corresponds to columns
    
    # Sample noise and angles using bilinear interpolation (order=1)
    noise_vals = map_coordinates(noise_field, sample_coords, order=1)
    angle_vals = map_coordinates(vector_field, sample_coords, order=1)
    
    # Formula: P' = P + (Noise * [cos(Angle), sin(Angle)] * Stiffness)
    dx = noise_vals * np.cos(angle_vals) * stiffness
    dy = noise_vals * np.sin(angle_vals) * stiffness
    
    distorted_pts = pts + np.column_stack([dx, dy])
    
    return [tuple(p) for p in distorted_pts]

class Engine:
    """
    Pipeline orchestrator for Perlin-Infinite generation.
    """
    def __init__(self, size=(2048, 2048)):
        self.size = size

    def _render_grid_mode(self, draw, noise_field, palette, params):
        """
        Rectilinear Cellular Grid generation.
        """
        grid_res = params.get('grid_res', 64)
        threshold = params.get('grid_threshold', 0.4)
        padding_factor = params.get('cell_padding', 0.1) # [0, 1]
        stroke_width = params.get('cell_stroke', 0)
        
        h, w = self.size
        cell_w = w / grid_res
        cell_h = h / grid_res
        
        # Determine color mapping strategy
        color_by_noise = params.get('color_by_noise', True)
        
        from generator.palette import map_noise_to_color
        
        for i in range(grid_res):
            for j in range(grid_res):
                # Sample noise at center of cell
                # noise_field.shape is (h, w)
                sample_y = int((i + 0.5) * cell_h)
                sample_x = int((j + 0.5) * cell_w)
                
                # Clip samples
                sample_y = min(max(sample_y, 0), h - 1)
                sample_x = min(max(sample_x, 0), w - 1)
                
                val = noise_field[sample_y, sample_x]
                
                if val > threshold:
                    # Calculate cell bounds
                    x1 = j * cell_w
                    y1 = i * cell_h
                    x2 = (j + 1) * cell_w
                    y2 = (i + 1) * cell_h
                    
                    # Apply padding
                    pad_w = (cell_w * padding_factor) / 2
                    pad_h = (cell_h * padding_factor) / 2
                    
                    rect = [x1 + pad_w, y1 + pad_h, x2 - pad_w, y2 - pad_h]
                    
                    # Determine color
                    if color_by_noise:
                        # Map localized noise to palette
                        color = map_noise_to_color(np.array([val]), palette)[0]
                    else:
                        # Global gradient based on position
                        norm_pos = (i / grid_res + j / grid_res) / 2
                        color = map_noise_to_color(np.array([norm_pos]), palette)[0]
                    
                    color = tuple(to_pebble_array(np.array([color]))[0])
                    
                    # Draw
                    if stroke_width > 0:
                        draw.rectangle(rect, fill=color, outline=(0, 0, 0), width=stroke_width)
                    else:
                        draw.rectangle(rect, fill=color)
                        
        return {"grid_res": grid_res, "threshold": threshold}

    def _is_collision_free(self, mask, p1, p2, seed_id, buffer=0):
        """Check if the line segment from p1 to p2 hits another seed's path."""
        x0, y0 = int(p1[0]), int(p1[1])
        x1, y1 = int(p2[0]), int(p2[1])
        
        # Check bounds
        h, w = mask.shape
        if not (0 <= x0 < w and 0 <= x1 < w and 0 <= y0 < h and 0 <= y1 < h):
            return False
            
        min_x = max(0, min(x0, x1) - buffer)
        max_x = min(w, max(x0, x1) + buffer + 1)
        min_y = max(0, min(y0, y1) - buffer)
        max_y = min(h, max(y0, y1) + buffer + 1)
        
        region = mask[min_y:max_y, min_x:max_x]
        # It's a collision if there are pixels > 0 that are NOT our own seed_id
        return not np.any((region > 0) & (region != seed_id))

    def _mark_collision(self, mask, p1, p2, seed_id, line_width):
        """Mark the segment in the collision mask."""
        x0, y0 = int(p1[0]), int(p1[1])
        x1, y1 = int(p2[0]), int(p2[1])
        h, w = mask.shape
        
        buffer = max(1, line_width // 2)
        min_x = max(0, min(x0, x1) - buffer)
        max_x = min(w, max(x0, x1) + buffer + 1)
        min_y = max(0, min(y0, y1) - buffer)
        max_y = min(h, max(y0, y1) + buffer + 1)
        mask[min_y:max_y, min_x:max_x] = seed_id

    def _render_lsystem_growth_mode(self, img, draw, noise_field, palette, params, seed):
        """
        Collision-Aware L-System Growth.
        """
        from generator.fractals import LSYSTEM_RULES
        
        rule_name = params.get('lsystem_rule', 'dragon')
        if rule_name in LSYSTEM_RULES:
            rule_set = LSYSTEM_RULES[rule_name]
            axiom = rule_set['axiom']
            rules = rule_set['rules']
            angle = rule_set['angle']
        else:
            axiom = params.get('axiom', 'F')
            rules = params.get('rules', {'F': 'F+F-F-F+F'})
            angle = params.get('angle', 90.0)
            
        iterations = params.get('iterations', 4)
        step_size = params.get('step_size', 10.0)
        num_seeds = params.get('num_seeds', 15)
        
        # Mask for collision detection (int to distinguish seeds)
        h, w = self.size
        collision_mask = np.zeros((h, w), dtype=int)
        
        terminal_shape = params.get('terminal_shape', 'square')
        node_threshold = params.get('node_threshold', 0.2)
        node_base_size = params.get('node_size', 2.0)
        line_width = params.get('line_width', 3)
        
        # Pre-calculate full sequence of operations
        state = axiom
        for _ in range(iterations):
            next_state = ""
            for char in state:
                next_state += rules.get(char, char)
            state = next_state
            
        import math
        
        all_drawn_points = 0
        
        # Color strategy
        color_frequency = params.get('color_frequency', 1.0)
        # Pre-generate a large array of colors to sample from
        color_map = map_path_to_color(len(state) * num_seeds, palette, frequency=color_frequency)
        color_map = to_pebble_array(color_map)
        color_idx = 0
        
        from generator.palette import darken_color
        
        for s in range(num_seeds):
            seed_id = s + 1
            # Random starting point - spread out more
            start_x = np.random.randint(w // 8, 7 * w // 8)
            start_y = np.random.randint(h // 8, 7 * h // 8)
            start_angle = np.random.choice([0.0, 90.0, 180.0, 270.0])
            
            curr_x, curr_y = start_x, start_y
            curr_angle = start_angle
            stack = []
            
            from generator.palette import lighten_color
            
            for char in state:
                if char in ('F', 'A', 'B', 'G'):
                    rad = math.radians(curr_angle)
                    next_x = curr_x + step_size * math.cos(rad)
                    next_y = curr_y + step_size * math.sin(rad)
                    
                    p1 = (curr_x, curr_y)
                    p2 = (next_x, next_y)
                    
                    # Fix blobbiness: Add buffer so paths don't clump
                    if self._is_collision_free(collision_mask, p1, p2, seed_id, buffer=line_width):
                        # Sample noise for color and node properties
                        sample_y = min(max(int(next_y), 0), h - 1)
                        sample_x = min(max(int(next_x), 0), w - 1)
                        node_noise = noise_field[sample_y, sample_x]
                        
                        # Fix monochrome: Pick color based on noise field so it shifts naturally
                        noise_mapped_idx = int(node_noise * len(color_map)) % len(color_map)
                        color = tuple(color_map[noise_mapped_idx])
                        
                        # Draw segment
                        draw.line([p1, p2], fill=color, width=line_width)
                        self._mark_collision(collision_mask, p1, p2, seed_id, line_width)
                        
                        if node_noise > node_threshold:
                            node_size = node_base_size * (0.5 + node_noise)
                            # Fill: Light and vibrant version of outline (Never dark!)
                            fill_color = lighten_color(color, factor=0.7)
                            fill_color = tuple(to_pebble_array(np.array([fill_color]))[0])
                            
                            rect = [next_x - node_size, next_y - node_size, 
                                    next_x + node_size, next_y + node_size]
                            
                            if terminal_shape == 'square':
                                draw.rectangle(rect, fill=fill_color, outline=color, width=1)
                            else:
                                draw.ellipse(rect, fill=fill_color, outline=color, width=1)
                                
                        curr_x, curr_y = next_x, next_y
                        all_drawn_points += 1
                        color_idx += 1
                    else:
                        # Collision: try turning instead of dying immediately
                        curr_angle += angle * np.random.choice([1, -1])
                        
                elif char == '+':
                    curr_angle += angle
                elif char == '-':
                    curr_angle -= angle
                elif char == '[':
                    stack.append((curr_x, curr_y, curr_angle))
                elif char == ']':
                    if stack:
                        curr_x, curr_y, curr_angle = stack.pop()
                        
        return {"drawn_segments": all_drawn_points}

    def _render_fractal_pure_mode(self, draw, noise_field, palette, params):
        """
        Pure Geometric Fractals.
        """
        from generator.fractals import get_box_fractal, get_quadratic_koch_island
        
        fractal_type = params.get('fractal_type', 'box')
        order = params.get('order', 3)
        size = params.get('size', 1500.0)
        
        start_x = (self.size[0] - size) / 2
        start_y = (self.size[1] - size) / 2
        
        color_frequency = params.get('color_frequency', 1.0)
        
        if fractal_type == 'box':
            paths = get_box_fractal(size=size, order=order, start_pos=(start_x, start_y))
            colors = map_path_to_color(len(paths), palette, frequency=color_frequency)
            colors = to_pebble_array(colors)
            
            from generator.palette import lighten_color
            
            for i, item in enumerate(paths):
                # Unpack tuple (path, box_size, is_leaf)
                is_leaf = False
                if isinstance(item, tuple):
                    if len(item) == 3:
                        path, box_size, is_leaf = item
                    else:
                        path, box_size = item
                else:
                    path, box_size = item, size
                    
                color = tuple(colors[i])
                
                # Fill probability is ONLY for leaf nodes (boxes with no children)
                fill_prob = 0.0
                if is_leaf:
                    # Scales inversely with size (target ~30-40% for smallest boxes)
                    fill_prob = 0.4 * (1.0 - (box_size / size))
                
                if np.random.rand() < fill_prob:
                    # Pick a contrasting bright color from the generated color array
                    offset = len(colors) // max(1, len(colors) // 3)
                    base_fill = tuple(colors[(i + offset) % len(colors)])
                    
                    # Ensure vibrancy by lightening the selected color
                    fill_color = lighten_color(base_fill, factor=0.6)
                    fill_color = tuple(to_pebble_array(np.array([fill_color]))[0])
                    
                    draw.polygon(path, fill=fill_color, outline=color, width=2)
                else:
                    draw.polygon(path, fill=None, outline=color, width=2)
                
            return {"fractal_type": "box", "paths": len(paths)}
            
        elif fractal_type == 'koch':
            path = get_quadratic_koch_island(size=size, order=order, start_pos=(start_x, start_y))
            colors = map_path_to_color(len(path), palette, frequency=color_frequency)
            colors = to_pebble_array(colors)
            
            for i in range(len(path) - 1):
                color = tuple(colors[i])
                draw.line([path[i], path[i+1]], fill=color, width=4)
                
            return {"fractal_type": "koch", "points": len(path)}
            
        elif fractal_type == 'hilbert_koch':
            from generator.fractals import get_hilbert_koch_curve
            path = get_hilbert_koch_curve(order=max(1, order - 2), koch_order=2, size=size)
            
            # Center it
            pts = np.array(path)
            min_p = pts.min(axis=0)
            max_p = pts.max(axis=0)
            center_offset = (np.array(self.size) - (max_p - min_p)) / 2 - min_p
            path = [tuple(p + center_offset) for p in pts]
            
            colors = map_path_to_color(len(path), palette, frequency=color_frequency)
            colors = to_pebble_array(colors)
            
            for i in range(len(path) - 1):
                color = tuple(colors[i])
                draw.line([path[i], path[i+1]], fill=color, width=4)
                
            return {"fractal_type": "hilbert_koch", "points": len(path)}
        
        return {}

    def _render_path_mode(self, draw, noise_field, vector_field, palette, params):
        """
        Classic distorted path generation.
        """
        stiffness = params.get('stiffness', 50.0)
        fractal_type = params.get('fractal_type', 'hilbert')
        
        # 2. Generate Fractal Path
        if fractal_type == 'hilbert':
            order = params.get('order', 6)
            path = get_hilbert_curve(order, self.size[0])
        elif fractal_type == 'lsystem':
            axiom = params.get('axiom', 'F')
            rules = params.get('rules', {'F': 'F+F-F-F+F'})
            iterations = params.get('iterations', 4)
            step_size = params.get('step_size', 20.0)
            angle = params.get('angle', 90.0)
            path = get_l_system(axiom, rules, iterations, step_size, angle)
            
            # Center L-system path
            pts = np.array(path)
            min_p = pts.min(axis=0)
            max_p = pts.max(axis=0)
            center_offset = (np.array(self.size) - (max_p - min_p)) / 2 - min_p
            path = [tuple(p + center_offset) for p in pts]
        else:
            raise ValueError(f"Unsupported fractal type: {fractal_type}")
            
        # 3. Distort Fractal Path
        distorted_path = distort_path(path, noise_field, vector_field, stiffness=stiffness)
        
        # 4. Map Colors
        color_frequency = params.get('color_frequency', 1.0)
        colors = map_path_to_color(len(distorted_path), palette, frequency=color_frequency)
        colors = to_pebble_array(colors)
        
        # 5. Rasterization
        if len(distorted_path) > 1:
            for i in range(len(distorted_path) - 1):
                p1 = distorted_path[i]
                p2 = distorted_path[i+1]
                color = tuple(colors[i])
                draw.line([p1, p2], fill=color, width=4)
        
        return {"bounding_box": draw.im.getbbox() if hasattr(draw, 'im') else None}

    def generate_universe(self, seed, params=None):
        """
        Generate a complete universe from a seed and parameters.
        
        Args:
            seed (int): Random seed.
            params (dict, optional): Generation parameters.
            
        Returns:
            tuple: (PIL.Image, dict) resulting image and metadata.
        """
        if params is None:
            params = {}
            
        np.random.seed(seed)
        
        # Extract base params
        mode = params.get('mode', 'path')
        noise_scale = params.get('noise_scale', 5.0)
        noise_octaves = params.get('noise_octaves', 4)
        palette_name = params.get('palette', 'deep_sea')
        
        # 1. Generate Noise Field & Vector Field
        noise_field = generate_noise_field(
            shape=(self.size[1], self.size[0]), 
            scale=noise_scale, 
            octaves=noise_octaves,
            seed=seed
        )
        vector_field = generate_vector_field(noise_field)
        
        # 2. Select Palette
        palettes = {
            'solar': SOLAR,
            'deep_sea': DEEP_SEA,
            'rainbow': RAINBOW,
            'forest': FOREST,
            'sunset': SUNSET,
            'cobalt': COBALT,
            'crimson': CRIMSON,
            'pebble': PEBBLE_64_PALETTE
        }
        palette = palettes.get(palette_name, DEEP_SEA)
        
        # 3. Rasterization
        # Background: White (#FFFFFF)
        img = Image.new('RGB', self.size, color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        render_metadata = {}
        
        # Composite Base Layer
        if params.get('composite', False):
            # Render grid underneath
            render_metadata['grid'] = self._render_grid_mode(draw, noise_field, palette, params)
            
        if mode == 'grid':
            render_metadata['grid'] = self._render_grid_mode(draw, noise_field, palette, params)
        elif mode == 'lsystem_growth':
            render_metadata['lsystem'] = self._render_lsystem_growth_mode(img, draw, noise_field, palette, params, seed)
        elif mode == 'fractal_pure':
            render_metadata['pure'] = self._render_fractal_pure_mode(draw, noise_field, palette, params)
        else:
            render_metadata['path'] = self._render_path_mode(draw, noise_field, vector_field, palette, params)
                
        metadata = {
            "seed": seed,
            "params": params,
            "bounding_box": img.getbbox()
        }
        if render_metadata:
            metadata.update(render_metadata)
        
        return img, metadata
