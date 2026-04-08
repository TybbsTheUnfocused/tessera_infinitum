def test_hilbert_points():
    from generator.fractals import get_hilbert_curve
    # Order 1: 4 points, Order 2: 16 points
    points = get_hilbert_curve(order=2, size=2048)
    assert len(points) == 16
    # Ensure points are within 2048x2048
    for x, y in points:
        assert 0 <= x <= 2048
        assert 0 <= y <= 2048

def test_dragon_curve():
    from generator.fractals import get_l_system
    # Dragon curve rules: X -> X+YF+, Y -> -FX-Y
    rules = {"X": "X+YF+", "Y": "-FX-Y"}
    points = get_l_system(axiom="FX", rules=rules, iterations=2, step_size=10, angle=90)
    assert len(points) > 0

def test_box_fractal():
    from generator.fractals import get_box_fractal
    paths = get_box_fractal(size=1000, order=2, start_pos=(0, 0))
    # Order 2 with random recursion means we should have at least the base box
    assert len(paths) >= 1
    # Check that each path is a closed square of 5 points
    for item in paths:
        if isinstance(item, tuple):
            path = item[0]
        else:
            path = item
        assert len(path) == 5
        assert path[0] == path[-1]

def test_quadratic_koch_island():
    from generator.fractals import get_quadratic_koch_island
    points = get_quadratic_koch_island(size=100, order=1, start_pos=(0, 0))
    # Base is 5 points (4 segments).
    # Order 1: each of the 4 segments is replaced by 5 segments.
    # Total points = 4 * 5 + 1 = 21 points.
    assert len(points) == 21
    # Should be closed
    assert points[0] == points[-1]
