#!/usr/bin/env python3
import argparse
import json
import os
import sys
import numpy as np
from generator.engine import Engine

def numpy_converter(obj):
    if isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj

def main():
    parser = argparse.ArgumentParser(description='Perlin-Infinite Universe Generator')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--output', type=str, default='output.png', help='Output filename (PNG)')
    parser.add_argument('--mode', type=str, default='path', choices=['path', 'grid', 'lsystem_growth', 'fractal_pure', 'segmented'], help='Generation mode')
    parser.add_argument('--style', type=str, default='deep_sea', 
                        choices=['deep_sea', 'solar', 'rainbow', 'forest', 'sunset', 'cobalt', 'crimson', 'pebble'], 
                        help='Style/Palette')
    parser.add_argument('--stiffness', type=float, default=100.0, help='Distortion stiffness')
    parser.add_argument('--noise-scale', type=float, default=5.0, help='Noise scale')
    parser.add_argument('--noise-octaves', type=int, default=4, help='Noise octaves')
    parser.add_argument('--color-frequency', type=float, default=1.0, help='Color cycle frequency')
    
    # Composite Option
    parser.add_argument('--composite', action='store_true', help='Render a grid background beneath the foreground mode')
    
    # Mode-specific: Grid
    parser.add_argument('--grid-res', type=int, default=64, help='Grid resolution')
    parser.add_argument('--grid-threshold', type=float, default=0.4, help='Noise threshold for grid cells')
    parser.add_argument('--cell-padding', type=float, default=0.1, help='Padding between cells [0-1]')
    parser.add_argument('--cell-stroke', type=int, default=0, help='Cell stroke width')
    parser.add_argument('--grid-style', type=str, default='rect', choices=['rect', 'dots', 'maze'], help='Style of grid cells')
    
    # Mode-specific: L-System Growth
    parser.add_argument('--lsystem-rule', type=str, default='dragon', choices=['dragon', 'gosper', 'sierpinski', 'plant'], help='L-System rule preset')
    parser.add_argument('--iterations', type=int, default=6, help='L-System iterations')
    parser.add_argument('--num-seeds', type=int, default=25, help='Number of independent growth paths')
    parser.add_argument('--terminal-shape', type=str, default='square', choices=['circle', 'square'], help='Node shape')
    parser.add_argument('--node-size', type=float, default=6.0, help='Base node size')
    parser.add_argument('--node-threshold', type=float, default=0.2, help='Noise threshold for nodes')
    parser.add_argument('--line-width', type=int, default=4, help='Path line width')
    parser.add_argument('--step-size', type=float, default=25.0, help='Step size for L-System')
    
    # Mode-specific: Fractal Pure
    parser.add_argument('--fractal', type=str, default='box', choices=['box', 'koch', 'hilbert', 'hilbert_koch', 'lsystem'], help='Fractal type')
    parser.add_argument('--size', type=float, default=2048.0, help='Fractal bounds size')
    parser.add_argument('--order', type=int, default=7, help='Fractal recursion order')
    parser.add_argument('--no-box-fill', action='store_true', help='Disable box fractal fills entirely')
    
    parser.add_argument('--count', type=int, default=1, help='Number of unique images to generate')
    
    args = parser.parse_args()
    
    # Base params
    base_params = {
        'mode': args.mode,
        'composite': args.composite,
        'palette': args.style,
        'stiffness': args.stiffness,
        'noise_scale': args.noise_scale,
        'noise_octaves': args.noise_octaves,
        'color_frequency': args.color_frequency,
        
        'grid_res': args.grid_res,
        'grid_threshold': args.grid_threshold,
        'cell_padding': args.cell_padding,
        'cell_stroke': args.cell_stroke,
        'grid_style': args.grid_style,
        
        'lsystem_rule': args.lsystem_rule,
        'iterations': args.iterations,
        'num_seeds': args.num_seeds,
        'terminal_shape': args.terminal_shape,
        'node_size': args.node_size,
        'node_threshold': args.node_threshold,
        'line_width': args.line_width,
        'step_size': args.step_size,
        
        'fractal_type': args.fractal,
        'size': args.size,
        'order': args.order,
        'fill_boxes': not args.no_box_fill
    }
    
    # L-system defaults
    if args.fractal == 'lsystem' or args.mode == 'lsystem_geom':
        base_params.update({
            'axiom': 'F',
            'rules': {'F': 'F+F-F-F+F'},
            'iterations': 4,
            'step_size': 20.0,
            'angle': 90.0
        })
    
    engine = Engine(size=(2048, 2048))
    
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    for i in range(args.count):
        current_seed = args.seed + i
        
        if args.count > 1:
            base_file = os.path.basename(args.output)
            base_name = os.path.splitext(base_file)[0]
            current_output = os.path.join(output_dir, f"{base_name}_{current_seed}.png")
        else:
            current_output = args.output
            
        print(f"[{i+1}/{args.count}] Generating universe | mode={args.mode} | seed={current_seed} | style={args.style}")
        
        try:
            img, metadata = engine.generate_universe(current_seed, base_params)
            img.save(current_output)
            
            json_path = os.path.splitext(current_output)[0] + '.json'
            with open(json_path, 'w') as f:
                json.dump(metadata, f, indent=4, default=numpy_converter)
            
        except Exception as e:
            print(f"Error for seed {current_seed}: {e}")
            continue

if __name__ == '__main__':
    main()
