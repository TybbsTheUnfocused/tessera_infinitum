import numpy as np
from scripts.recipes import RECIPES, STYLES, get_recipe_by_name, select_recipe


def test_recipe_count():
    assert len(RECIPES) == 19


def test_all_recipes_have_required_keys():
    required = {'name', 'mode', 'params', 'weight'}
    for recipe in RECIPES:
        missing = required - set(recipe.keys())
        assert not missing, f"Recipe {recipe.get('name', '?')} missing keys: {missing}"


def test_all_modes_are_valid():
    valid_modes = {'grid', 'lsystem_growth', 'fractal_pure', 'segmented'}
    for recipe in RECIPES:
        assert recipe['mode'] in valid_modes, f"Invalid mode: {recipe['mode']}"


def test_weights_are_positive():
    for recipe in RECIPES:
        assert recipe['weight'] > 0, f"Recipe {recipe['name']} has non-positive weight"


def test_get_recipe_by_name():
    recipe = get_recipe_by_name('grid_rect')
    assert recipe is not None
    assert recipe['mode'] == 'grid'


def test_get_recipe_by_name_missing():
    assert get_recipe_by_name('nonexistent') is None


def test_select_recipe_deterministic():
    rng = np.random.RandomState(42)
    r1 = select_recipe(rng)
    rng = np.random.RandomState(42)
    r2 = select_recipe(rng)
    assert r1['name'] == r2['name']


def test_select_recipe_respects_weights():
    # With enough samples, high-weight recipes should appear more often
    counts = {}
    for i in range(10000):
        rng = np.random.RandomState(i)
        r = select_recipe(rng)
        counts[r['name']] = counts.get(r['name'], 0) + 1
    # segmented has weight 3.0, grid_rect has weight 1.0
    assert counts.get('segmented', 0) > counts.get('grid_rect', 0)


def test_styles_list():
    assert len(STYLES) == 8
    assert 'deep_sea' in STYLES
    assert 'pebble' in STYLES
