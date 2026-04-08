#!/usr/bin/env python3
import os
import sys
import subprocess

# Define the permutations
STYLES = ['deep_sea', 'solar', 'rainbow', 'forest', 'sunset', 'cobalt', 'crimson', 'pebble']
LSYSTEM_RULES = {
    'dragon': {'iterations': 10, 'step_size': 25, 'num_seeds': 40, 'node_size': 8},
    'gosper': {'iterations': 4, 'step_size': 30, 'num_seeds': 30, 'node_size': 8},
    'sierpinski': {'iterations': 6, 'step_size': 35, 'num_seeds': 25, 'node_size': 8},
    'plant': {'iterations': 5, 'step_size': 25, 'num_seeds': 30, 'node_size': 8}
}
FRACTAL_TYPES = ['box', 'koch', 'hilbert_koch']
TERMINAL_SHAPES = ['square', 'circle']

OUTPUT_DIR = "generations/export_all"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def run_gen(filename, args):
    cmd = ["uv", "run", "python", "scripts/generate.py", "--output", os.path.join(OUTPUT_DIR, filename)] + args
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, env={**os.environ, "PYTHONPATH": "."})

def main():
    seed = 200000
    
    # 1. Grid Mode (just one representative image)
    run_gen("grid_showcase.png", [
        "--mode", "grid", "--style", "rainbow", "--seed", str(seed),
        "--grid-res", "48", "--cell-padding", "0.2"
    ])
    seed += 1
        
    # 2. L-System Growth Modes (One normal, one hybrid for each rule)
    for rule, params in LSYSTEM_RULES.items():
        shape = TERMINAL_SHAPES[seed % len(TERMINAL_SHAPES)]
        style = STYLES[seed % len(STYLES)]
        
        # Normal
        run_gen(f"growth_{rule}_{style}.png", [
            "--mode", "lsystem_growth", "--style", style, "--seed", str(seed),
            "--lsystem-rule", rule, "--terminal-shape", shape,
            "--iterations", str(params['iterations']), 
            "--num-seeds", str(params['num_seeds']), 
            "--step-size", str(params['step_size']),
            "--node-size", str(params['node_size']),
            "--line-width", "5"
        ])
        seed += 1
        
        # Hybrid
        hybrid_style = STYLES[seed % len(STYLES)]
        shape = TERMINAL_SHAPES[seed % len(TERMINAL_SHAPES)]
        run_gen(f"hybrid_growth_{rule}_{hybrid_style}.png", [
            "--mode", "lsystem_growth", "--style", hybrid_style, "--seed", str(seed),
            "--lsystem-rule", rule, "--terminal-shape", shape,
            "--iterations", str(params['iterations']), 
            "--num-seeds", str(params['num_seeds']), 
            "--step-size", str(params['step_size']),
            "--node-size", str(params['node_size']), 
            "--line-width", "5", "--composite"
        ])
        seed += 1

    # 3. Pure Fractal Modes (One normal, one hybrid for each fractal)
    for frac in FRACTAL_TYPES:
        style = STYLES[seed % len(STYLES)]
        run_gen(f"pure_{frac}_{style}.png", [
            "--mode", "fractal_pure", "--style", style, "--seed", str(seed),
            "--fractal", frac, "--order", "7" if frac == 'box' else "5",
            "--size", "2048"
        ])
        seed += 1
        
        # Hybrid
        hybrid_style = STYLES[seed % len(STYLES)]
        run_gen(f"hybrid_{frac}_{hybrid_style}.png", [
            "--mode", "fractal_pure", "--style", hybrid_style, "--seed", str(seed),
            "--fractal", frac, "--order", "7" if frac == 'box' else "5",
            "--size", "2048", "--composite"
        ])
        seed += 1

if __name__ == '__main__':
    main()
