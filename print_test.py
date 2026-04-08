from generator.engine import Engine
engine = Engine(size=(512, 512))
params = {'mode': 'fractal_pure', 'fractal_type': 'box', 'order': 2}
img, metadata = engine.generate_universe(seed=42, params=params)
print(metadata)
