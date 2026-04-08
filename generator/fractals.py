import math

def get_hilbert_curve(order: int, size: int) -> list[tuple[float, float]]:
    """
    Generate Hilbert curve points for a given order and total size.
    
    Args:
        order (int): The order of the Hilbert curve (e.g., 2).
        size (int): The total bounding box size (e.g., 2048).
        
    Returns:
        list[tuple[float, float]]: List of (x, y) coordinates.
    """
    n = 2**order
    total_points = n * n
    points = []
    
    # Unit step size
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

def get_l_system(axiom: str, rules: dict[str, str], iterations: int, step_size: float, angle: float) -> list[tuple[float, float]]:
    """
    Generate points from an L-System.
    
    Args:
        axiom (str): Initial string.
        rules (dict): Production rules.
        iterations (int): Number of iterations.
        step_size (float): Distance to move forward.
        angle (float): Angle in degrees to rotate.
        
    Returns:
        list[tuple[float, float]]: List of (x, y) coordinates.
    """
    state = axiom
    for _ in range(iterations):
        next_state = ""
        for char in state:
            next_state += rules.get(char, char)
        state = next_state
        
    points = [(0.0, 0.0)]
    curr_x, curr_y = 0.0, 0.0
    curr_angle = 0.0
    
    for char in state:
        if char == 'F':
            rad = math.radians(curr_angle)
            curr_x += step_size * math.cos(rad)
            curr_y += step_size * math.sin(rad)
            points.append((curr_x, curr_y))
        elif char == '+':
            curr_angle += angle
        elif char == '-':
            curr_angle -= angle
            
    return points
