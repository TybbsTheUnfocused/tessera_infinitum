#!/usr/bin/env python3
import argparse
import json
import os
import sys
import numpy as np
from generator.engine import Engine

def main():
    parser = argparse.ArgumentParser(description='Perlin-Infinite Universe Generator')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--output', type=str, default='output.png', help='Output filename (PNG)')
    parser.add_argument('--style', type=str, default='deep_sea', choices=['deep_sea', 'solar', 'pebble'], help='Style/Palette')
    parser.add_argument('--stiffness', type=float, default=100.0, help='Distortion stiffness')
    parser.add_argument('--noise-scale', type=float, default=5.0, help='Noise scale')
    parser.add_argument('--noise-octaves', type=int, default=4, help='Noise octaves')
    parser.add_argument('--fractal', type=str, default='hilbert', choices=['hilbert', 'lsystem'], help='Fractal type')
    parser.add_argument('--order', type=int, default=6, help='Hilbert curve order')
    
    args = parser.parse_args()
    
    params = {
        'palette': args.style,
        'stiffness': args.stiffness,
        'noise_scale': args.noise_scale,
        'noise_octaves': args.noise_octaves,
        'fractal_type': args.fractal,
        'order': args.order
    }
    
    # If L-system is chosen, add some defaults if not specified
    if args.fractal == 'lsystem':
        params.update({
            'axiom': 'F',
            'rules': {'F': 'F+F-F-F+F'},
            'iterations': 4,
            'step_size': 20.0,
            'angle': 90.0
        })
    
    engine = Engine(size=(2048, 2048))
    
    print(f"Generating universe with seed={args.seed}, style={args.style}, fractal={args.fractal}...")
    
    try:
        img, metadata = engine.generate_universe(args.seed, params)
        
        # Save image
        img.save(args.output)
        print(f"Successfully saved image to: {args.output}")
        
        # Save metadata
        json_path = os.path.splitext(args.output)[0] + '.json'
        # Convert any numpy types to standard python types for JSON serialization
        def numpy_converter(obj):
            if isinstance(obj, (np.integer, np.floating)):
                return obj.item()
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            return obj

        with open(json_path, 'w') as f:
            json.dump(metadata, f, indent=4, default=numpy_converter)
        print(f"Successfully saved metadata to: {json_path}")
        
    except Exception as e:
        print(f"Error during generation: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
