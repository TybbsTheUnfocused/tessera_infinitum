#!/usr/bin/env python3
# scripts/orchestrate.py
"""
Tessera ad Infinitum orchestrator.

Derives a seed from the current UTC hour (or --seed override), selects a
weighted-random recipe from the deck, renders a 2048x2048 master canvas,
and writes canvas.png + metadata.json to --output-dir.
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

import numpy as np

from generator.engine import Engine
from scripts.recipes import RECIPES, STYLES, get_recipe_by_name, select_recipe


def derive_seed(hour_string):
    """Derive a deterministic positive 31-bit seed from a YYYYMMDDHH string."""
    return hash(f"tessera-{hour_string}") & 0x7FFFFFFF


def resolve_params(recipe, rng):
    """Build the full params dict for Engine.generate_universe().

    Merges the recipe's fixed params with randomized palette and
    terminal_shape. The recipe's 'mode' becomes params['mode'].

    Args:
        recipe: dict from RECIPES with keys 'name', 'mode', 'params'.
        rng: numpy RandomState for deterministic randomization.

    Returns:
        dict: Fully resolved params for generate_universe().
    """
    params = dict(recipe['params'])
    params['mode'] = recipe['mode']
    params['palette'] = STYLES[rng.randint(len(STYLES))]
    if recipe['mode'] == 'lsystem_growth':
        params['terminal_shape'] = rng.choice(['circle', 'square'])
    return params


def _get_git_sha():
    """Get the current git commit SHA, or 'unknown' if not in a repo."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else 'unknown'
    except Exception:
        return 'unknown'


def _numpy_converter(obj):
    """JSON serializer for numpy types."""
    if isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj


def run_orchestrate(seed, recipe_name=None, output_dir='output'):
    """Run the full orchestration: select recipe, render, write outputs.

    Args:
        seed: integer seed for generation.
        recipe_name: force a specific recipe by name, or None for weighted random.
        output_dir: directory to write canvas.png and metadata.json.
    """
    rng = np.random.RandomState(seed)

    if recipe_name:
        recipe = get_recipe_by_name(recipe_name)
        if recipe is None:
            names = [r['name'] for r in RECIPES]
            raise ValueError(f"Unknown recipe '{recipe_name}'. Available: {names}")
    else:
        recipe = select_recipe(rng)

    params = resolve_params(recipe, rng)

    engine = Engine(size=(2048, 2048))
    img, engine_meta = engine.generate_universe(seed, params)

    os.makedirs(output_dir, exist_ok=True)
    img.save(os.path.join(output_dir, 'canvas.png'))

    metadata = {
        'contract_version': 1,
        'generator_sha': _get_git_sha(),
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'seed': seed,
        'recipe_name': recipe['name'],
        'params': params,
        'final_whitespace': engine_meta.get('final_whitespace'),
        'adaptive_passes': engine_meta.get('adaptive_passes', 0),
    }

    with open(os.path.join(output_dir, 'metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=2, default=_numpy_converter)

    print(f"Done: seed={seed} recipe={recipe['name']} palette={params['palette']}")
    print(f"  whitespace={metadata['final_whitespace']:.2%}  passes={metadata['adaptive_passes']}")


def main():
    parser = argparse.ArgumentParser(description='Tessera ad Infinitum Orchestrator')
    parser.add_argument('--seed', type=int, default=None,
                        help='Override seed (default: derived from UTC hour)')
    parser.add_argument('--output-dir', type=str, default='output',
                        help='Output directory (default: output/)')
    parser.add_argument('--recipe', type=str, default=None,
                        help='Force a specific recipe by name')
    args = parser.parse_args()

    if args.seed is None:
        hour_str = datetime.now(timezone.utc).strftime('%Y%m%d%H')
        seed = derive_seed(hour_str)
        print(f"Derived seed from UTC hour {hour_str}: {seed}")
    else:
        seed = args.seed

    run_orchestrate(seed=seed, recipe_name=args.recipe, output_dir=args.output_dir)


if __name__ == '__main__':
    main()
