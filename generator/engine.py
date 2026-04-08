import numpy as np
from scipy.ndimage import map_coordinates
from PIL import Image, ImageDraw
from generator.noise import generate_noise_field, generate_vector_field
from generator.fractals import get_hilbert_curve, get_l_system
from generator.palette import PEBBLE_64_PALETTE, DEEP_SEA, SOLAR, map_path_to_color, to_pebble_array

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
        
        # Extract params with defaults
        stiffness = params.get('stiffness', 50.0)
        noise_scale = params.get('noise_scale', 5.0)
        noise_octaves = params.get('noise_octaves', 4)
        fractal_type = params.get('fractal_type', 'hilbert')
        palette_name = params.get('palette', 'deep_sea')
        
        # 1. Generate Noise Field & Vector Field
        # Note: shape is (rows, cols) -> (height, width)
        noise_field = generate_noise_field(
            shape=(self.size[1], self.size[0]), 
            scale=noise_scale, 
            octaves=noise_octaves
        )
        vector_field = generate_vector_field(noise_field)
        
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
        if palette_name == 'solar':
            palette = SOLAR
        elif palette_name == 'deep_sea':
            palette = DEEP_SEA
        else:
            palette = PEBBLE_64_PALETTE
            
        colors = map_path_to_color(len(distorted_path), palette)
        colors = to_pebble_array(colors)
        
        # 5. Rasterization
        # Background: Cream/White (Pebble-safe #FFFF55 / 255, 255, 85 or White #FFFFFF)
        # Using a soft cream #FFFFAA (255, 255, 170)
        img = Image.new('RGB', self.size, color=(255, 255, 170))
        draw = ImageDraw.Draw(img)
        
        if len(distorted_path) > 1:
            for i in range(len(distorted_path) - 1):
                p1 = distorted_path[i]
                p2 = distorted_path[i+1]
                color = tuple(colors[i])
                draw.line([p1, p2], fill=color, width=4)
                
        metadata = {
            "seed": seed,
            "params": params,
            "bounding_box": img.getbbox()
        }
        
        return img, metadata
