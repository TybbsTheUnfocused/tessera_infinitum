import math
import random

LSYSTEM_RULES = {
    'dragon': {
        'axiom': 'FX',
        'rules': {'X': 'X+YF+', 'Y': '-FX-Y'},
        'angle': 90.0,
        'step_scale': 0.707
    },
    'gosper': {
        'axiom': 'A',
        'rules': {'A': 'A-B--B+A++AA+B-', 'B': '+A-BB--B-A++A+B'},
        'angle': 60.0,
        'step_scale': 0.378
    },
    'sierpinski': {
        'axiom': 'F-G-G',
        'rules': {'F': 'F-G+F+G-F', 'G': 'GG'},
        'angle': 120.0,
        'step_scale': 0.5
    },
    'plant': {
        'axiom': 'X',
        'rules': {'X': 'F+[[X]-X]-F[-FX]+X', 'F': 'FF'},
        'angle': 25.0,
        'step_scale': 0.5
    }
}

def get_hilbert_curve(order: int, size: int) -> list[tuple[float, float]]:
    """Generate Hilbert curve points for a given order and total size."""
    n = 2**order
    total_points = n * n
    points = []
    
    step = size / (n - 1) if n > 1 else size
    
    def rot(n, x, y, rx, ry):
        if ry == 0:
            if rx == 1:
                x = n - 1 - x
                y = n - 1 - y
            return y, x
        return x, y

    def d2xy(n, d):
        t = d
        x = y = 0
        s = 1
        while s < n:
            rx = 1 & (t // 2)
            ry = 1 & (t ^ rx)
            x, y = rot(s, x, y, rx, ry)
            x += s * rx
            y += s * ry
            t //= 4
            s *= 2
        return x, y

    for d in range(total_points):
        hx, hy = d2xy(n, d)
        points.append((hx * step, hy * step))
        
    return points

def get_l_system(axiom: str, rules: dict[str, str], iterations: int, step_size: float, angle: float, start_pos=(0.0, 0.0), start_angle=0.0) -> list[tuple[float, float]]:
    """Generate points from an L-System."""
    state = axiom
    for _ in range(iterations):
        next_state = ""
        for char in state:
            next_state += rules.get(char, char)
        state = next_state
        
    points = [start_pos]
    curr_x, curr_y = start_pos
    curr_angle = start_angle
    
    stack = []
    
    for char in state:
        if char in ('F', 'A', 'B', 'G'):
            rad = math.radians(curr_angle)
            curr_x += step_size * math.cos(rad)
            curr_y += step_size * math.sin(rad)
            points.append((curr_x, curr_y))
        elif char == '+':
            curr_angle += angle
        elif char == '-':
            curr_angle -= angle
        elif char == '[':
            stack.append((curr_x, curr_y, curr_angle))
        elif char == ']':
            if stack:
                curr_x, curr_y, curr_angle = stack.pop()
                points.append((curr_x, curr_y)) # Move back without drawing
                
    return points

def get_box_fractal(size: float, order: int, start_pos=(0.0, 0.0)) -> list[list[tuple[float, float]]]:
    """
    Generate recursive box fractals.
    Returns a list of paths, where each path is a closed square.
    """
    paths = []
    
    def divide(x, y, s, current_order):
        if current_order == 0:
            return
            
        new_s = s / 2
        quadrants = [
            (x - new_s/2, y - new_s/2),
            (x + new_s/2, y - new_s/2),
            (x - new_s/2, y + new_s/2),
            (x + new_s/2, y + new_s/2)
        ]
        
        is_leaf = False
        chosen = []
        if current_order == 1:
            is_leaf = True
        else:
            # 10% chance to stop early and become a leaf
            if random.random() < 0.1:
                is_leaf = True
            else:
                num_recurse = random.choices([2, 3, 4], weights=[0.1, 0.4, 0.5])[0]
                chosen = random.sample(quadrants, num_recurse)
                
        # Add the current box
        half = s / 2
        paths.append(([
            (x - half, y - half),
            (x + half, y - half),
            (x + half, y + half),
            (x - half, y + half),
            (x - half, y - half)
        ], s, is_leaf))
        
        for qx, qy in chosen:
            divide(qx, qy, new_s, current_order - 1)
            
    divide(start_pos[0] + size/2, start_pos[1] + size/2, size, order)
    return paths

def get_hilbert_koch_curve(order: int, koch_order: int, size: int) -> list[tuple[float, float]]:
    """
    Generate a Hilbert curve and apply Koch island bumps to its segments.
    """
    base_points = get_hilbert_curve(order, size)
    
    def iterate(points):
        new_points = []
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i+1]
            
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            
            sign = 1 if random.random() > 0.5 else -1
            
            pA = (p1[0] + dx/3, p1[1] + dy/3)
            pB = (pA[0] - sign * dy/3, pA[1] + sign * dx/3)
            pC = (pB[0] + dx/3, pB[1] + dy/3)
            pD = (p1[0] + 2*dx/3, p1[1] + 2*dy/3)
            
            new_points.extend([p1, pA, pB, pC, pD])
        new_points.append(points[-1])
        return new_points

    current_points = base_points
    for _ in range(koch_order):
        current_points = iterate(current_points)
        
    return current_points

def get_quadratic_koch_island(size: float, order: int, start_pos=(0.0, 0.0)) -> list[tuple[float, float]]:
    """
    Generate a Quadratic Koch Island curve.
    Bumps are randomly flipped inwards or outwards.
    """
    # Start with a base square
    base_points = [
        (start_pos[0], start_pos[1]),
        (start_pos[0] + size, start_pos[1]),
        (start_pos[0] + size, start_pos[1] + size),
        (start_pos[0], start_pos[1] + size),
        (start_pos[0], start_pos[1])
    ]

    
    def iterate(points):
        new_points = []
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i+1]
            
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            
            # The line is broken into 3 segments. The middle segment has a square bump.
            # We randomly decide the direction of the bump (inward/outward).
            sign = 1 if random.random() > 0.5 else -1
            
            pA = (p1[0] + dx/3, p1[1] + dy/3)
            pB = (pA[0] - sign * dy/3, pA[1] + sign * dx/3)
            pC = (pB[0] + dx/3, pB[1] + dy/3)
            pD = (p1[0] + 2*dx/3, p1[1] + 2*dy/3)
            
            new_points.extend([p1, pA, pB, pC, pD])
        new_points.append(points[-1])
        return new_points

    current_points = base_points
    for _ in range(order):
        current_points = iterate(current_points)
        
    return current_points
