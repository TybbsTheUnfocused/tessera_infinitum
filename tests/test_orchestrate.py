# tests/test_orchestrate.py
import json
import os
import numpy as np
import pytest
from unittest.mock import patch
from scripts.orchestrate import derive_seed, resolve_params, run_orchestrate


def test_derive_seed_deterministic():
    s1 = derive_seed("2026040914")
    s2 = derive_seed("2026040914")
    assert s1 == s2


def test_derive_seed_positive():
    s = derive_seed("2026040914")
    assert s > 0


def test_derive_seed_varies_by_hour():
    s1 = derive_seed("2026040914")
    s2 = derive_seed("2026040915")
    assert s1 != s2


def test_resolve_params_has_palette():
    rng = np.random.RandomState(42)
    from scripts.recipes import RECIPES
    params = resolve_params(RECIPES[0], rng)
    assert 'palette' in params
    assert params['palette'] in [
        'deep_sea', 'solar', 'rainbow', 'forest',
        'sunset', 'cobalt', 'crimson', 'pebble',
    ]


def test_resolve_params_has_mode():
    rng = np.random.RandomState(42)
    from scripts.recipes import RECIPES
    recipe = RECIPES[0]  # grid_rect
    params = resolve_params(recipe, rng)
    assert params['mode'] == 'grid'


def test_resolve_params_lsystem_has_terminal_shape():
    rng = np.random.RandomState(42)
    from scripts.recipes import get_recipe_by_name
    recipe = get_recipe_by_name('growth_dragon')
    params = resolve_params(recipe, rng)
    assert params['terminal_shape'] in ('circle', 'square')


def test_run_orchestrate_writes_files(tmp_path):
    output_dir = str(tmp_path)
    run_orchestrate(seed=42, recipe_name='grid_rect', output_dir=output_dir)

    assert os.path.exists(os.path.join(output_dir, 'canvas.png'))
    assert os.path.exists(os.path.join(output_dir, 'metadata.json'))

    with open(os.path.join(output_dir, 'metadata.json')) as f:
        meta = json.load(f)
    assert meta['contract_version'] == 1
    assert meta['seed'] == 42
    assert meta['recipe_name'] == 'grid_rect'
    assert 'params' in meta
    assert 'generator_sha' in meta
    assert 'generated_at_utc' in meta
    assert 'final_whitespace' in meta
    assert 'adaptive_passes' in meta


def test_run_orchestrate_deterministic(tmp_path):
    dir1 = str(tmp_path / 'run1')
    dir2 = str(tmp_path / 'run2')
    os.makedirs(dir1)
    os.makedirs(dir2)
    run_orchestrate(seed=99, recipe_name='grid_rect', output_dir=dir1)
    run_orchestrate(seed=99, recipe_name='grid_rect', output_dir=dir2)

    with open(os.path.join(dir1, 'metadata.json')) as f:
        m1 = json.load(f)
    with open(os.path.join(dir2, 'metadata.json')) as f:
        m2 = json.load(f)
    assert m1['seed'] == m2['seed']
    assert m1['params'] == m2['params']
    assert m1['recipe_name'] == m2['recipe_name']
