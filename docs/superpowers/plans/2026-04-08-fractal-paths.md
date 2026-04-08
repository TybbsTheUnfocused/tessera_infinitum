# Task 3: Fractal Path Logic Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Hilbert curve and L-System generators for generating fractal paths.

**Architecture:** Use recursion for the Hilbert curve and a rule-based parser for L-Systems. Both will return a list of (x, y) tuples.

**Tech Stack:** Python.

---

### Task 1: Hilbert Curve Generator

**Files:**
- Create: `generator/fractals.py`
- Test: `tests/test_fractals.py`

- [ ] **Step 1: Write the failing test for Hilbert curve**

```python
def test_hilbert_points():
    from generator.fractals import get_hilbert_curve
    # Order 1: 4 points, Order 2: 16 points
    points = get_hilbert_curve(order=2, size=2048)
    assert len(points) == 16
    # Ensure points are within 2048x2048
    for x, y in points:
        assert 0 <= x <= 2048
        assert 0 <= y <= 2048
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_fractals.py::test_hilbert_points -v`
Expected: FAIL (ModuleNotFoundError or ImportError)

- [ ] **Step 3: Implement Hilbert curve generator**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_fractals.py::test_hilbert_points -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add generator/fractals.py tests/test_fractals.py
git commit -m "feat: implement Hilbert curve generator"
```

---

### Task 2: L-System Parser (Dragon Curve)

**Files:**
- Modify: `generator/fractals.py`
- Modify: `tests/test_fractals.py`

- [ ] **Step 1: Write the failing test for L-System**

```python
def test_dragon_curve():
    from generator.fractals import get_l_system
    # Dragon curve rules: X -> X+YF+, Y -> -FX-Y
    rules = {"X": "X+YF+", "Y": "-FX-Y"}
    points = get_l_system(axiom="FX", rules=rules, iterations=2, step_size=10, angle=90)
    assert len(points) > 0
    # Dragon curve with 2 iterations:
    # 0: FX
    # 1: FX+YF+
    # 2: FX+YF++-FX-YF+
    # F counts should determine point length (axiom F + rules applications)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_fractals.py::test_dragon_curve -v`
Expected: FAIL (ImportError: cannot import name 'get_l_system')

- [ ] **Step 3: Implement L-System parser**

```python
import math

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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_fractals.py::test_dragon_curve -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add generator/fractals.py tests/test_fractals.py
git commit -m "feat: implement L-System parser"
```
