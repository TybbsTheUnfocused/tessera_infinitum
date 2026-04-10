"""
Recipe deck for the Tessera ad Infinitum orchestrator.

Each recipe is a frozen param dict for Engine.generate_universe().
Palette and terminal_shape are NOT included — they are randomized per run.
"""
import copy

import numpy as np

STYLES = [
    'deep_sea', 'solar', 'rainbow', 'forest',
    'sunset', 'cobalt', 'crimson', 'pebble',
]

# L-system growth base params per rule (from export_all.py proven combos)
_LSYSTEM_PARAMS = {
    'dragon':     {'lsystem_rule': 'dragon',     'iterations': 10, 'step_size': 25, 'num_seeds': 40, 'node_size': 8, 'line_width': 5},
    'gosper':     {'lsystem_rule': 'gosper',     'iterations': 4,  'step_size': 30, 'num_seeds': 30, 'node_size': 8, 'line_width': 5},
    'sierpinski': {'lsystem_rule': 'sierpinski', 'iterations': 6,  'step_size': 35, 'num_seeds': 25, 'node_size': 8, 'line_width': 5},
    'plant':      {'lsystem_rule': 'plant',      'iterations': 5,  'step_size': 25, 'num_seeds': 30, 'node_size': 8, 'line_width': 5},
}

RECIPES = [
    # Grid modes (1-3)
    {'name': 'grid_rect', 'mode': 'grid', 'weight': 1.5,
     'params': {'grid_res': 48, 'cell_padding': 0.2, 'grid_style': 'rect'}},
    {'name': 'grid_dots', 'mode': 'grid', 'weight': 1.5,
     'params': {'grid_res': 48, 'cell_padding': 0.2, 'grid_style': 'dots'}},
    {'name': 'grid_maze', 'mode': 'grid', 'weight': 1.5,
     'params': {'grid_res': 48, 'cell_padding': 0.2, 'grid_style': 'maze'}},

    # Pure L-system growth (4-7)
    {'name': 'growth_dragon',     'mode': 'lsystem_growth', 'weight': 1.0, 'params': {**_LSYSTEM_PARAMS['dragon']}},
    {'name': 'growth_gosper',     'mode': 'lsystem_growth', 'weight': 0.5, 'params': {**_LSYSTEM_PARAMS['gosper']}},
    {'name': 'growth_sierpinski', 'mode': 'lsystem_growth', 'weight': 1.0, 'params': {**_LSYSTEM_PARAMS['sierpinski']}},
    {'name': 'growth_plant',      'mode': 'lsystem_growth', 'weight': 0.5, 'params': {**_LSYSTEM_PARAMS['plant']}},

    # Hybrid L-system growth + composite grid (8-11)
    {'name': 'hybrid_growth_dragon',     'mode': 'lsystem_growth', 'weight': 2.5, 'params': {**_LSYSTEM_PARAMS['dragon'],     'composite': True}},
    {'name': 'hybrid_growth_gosper',     'mode': 'lsystem_growth', 'weight': 2.5, 'params': {**_LSYSTEM_PARAMS['gosper'],     'composite': True}},
    {'name': 'hybrid_growth_sierpinski', 'mode': 'lsystem_growth', 'weight': 2.5, 'params': {**_LSYSTEM_PARAMS['sierpinski'], 'composite': True}},
    {'name': 'hybrid_growth_plant',      'mode': 'lsystem_growth', 'weight': 2.5, 'params': {**_LSYSTEM_PARAMS['plant'],      'composite': True}},

    # Pure fractals (12-14)
    {'name': 'pure_box',          'mode': 'fractal_pure', 'weight': 2.0, 'params': {'fractal_type': 'box',          'order': 7, 'size': 2048.0}},
    {'name': 'pure_koch',         'mode': 'fractal_pure', 'weight': 1.0, 'params': {'fractal_type': 'koch',         'order': 5, 'size': 2048.0}},
    {'name': 'pure_hilbert_koch', 'mode': 'fractal_pure', 'weight': 1.0, 'params': {'fractal_type': 'hilbert_koch', 'order': 5, 'size': 2048.0}},

    # Hybrid fractals + composite grid (15-17)
    {'name': 'hybrid_hilbert_koch', 'mode': 'fractal_pure', 'weight': 0.5, 'params': {'fractal_type': 'hilbert_koch', 'order': 5, 'size': 2048.0, 'composite': True}},
    {'name': 'hybrid_koch',         'mode': 'fractal_pure', 'weight': 1.5, 'params': {'fractal_type': 'koch',         'order': 5, 'size': 2048.0, 'composite': True}},
    {'name': 'hybrid_box',          'mode': 'fractal_pure', 'weight': 1.0, 'params': {'fractal_type': 'box',          'order': 7, 'size': 2048.0, 'composite': True}},

    # Box unfilled (18)
    {'name': 'pure_box_unfilled', 'mode': 'fractal_pure', 'weight': 1.0, 'params': {'fractal_type': 'box', 'order': 7, 'size': 2048.0, 'fill_boxes': False}},

    # Segmented (19)
    {'name': 'segmented', 'mode': 'segmented', 'weight': 3.0, 'params': {}},
]


def get_recipe_by_name(name):
    """Look up a recipe by its name. Returns None if not found.

    Returns a deep copy so callers can safely mutate the result.
    """
    for recipe in RECIPES:
        if recipe['name'] == name:
            return copy.deepcopy(recipe)
    return None


def select_recipe(rng):
    """Select a recipe using weighted random choice.

    Returns a deep copy so callers can safely mutate the result.

    Args:
        rng: numpy RandomState instance for deterministic selection.

    Returns:
        dict: The selected recipe (deep copy).
    """
    weights = np.array([r['weight'] for r in RECIPES])
    probs = weights / weights.sum()
    idx = rng.choice(len(RECIPES), p=probs)
    return copy.deepcopy(RECIPES[idx])
