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
