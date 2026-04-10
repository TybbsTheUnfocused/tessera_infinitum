"""
Tessera ad Infinitum — Modal deployment.

Runs the hourly generation pipeline (orchestrate -> slice -> upload)
on a precise cron schedule via Modal, replacing the GitHub Actions cron.

Deploy:  modal deploy modal_app.py
Test:    modal run modal_app.py [--seed 42] [--recipe grid_rect]
"""
import os
import sys

import modal

app = modal.App("tessera-infinitum")

image = (
    modal.Image.debian_slim(python_version="3.13")
    .pip_install("numpy", "pillow", "vnoise", "scipy", "boto3", "setuptools")
    .add_local_python_source("generator")
    .add_local_python_source("scripts")
)

r2_secret = modal.Secret.from_name("r2-credentials")


@app.function(
    image=image,
    secrets=[r2_secret],
    schedule=modal.Cron("0 * * * *"),
    timeout=900,
)
def generate_universe_cron():
    """Run the full pipeline: orchestrate, slice, upload to R2."""
    from datetime import datetime, timezone

    from scripts.orchestrate import derive_seed, run_orchestrate
    from scripts.slice import run_slice
    from scripts.upload import build_upload_plan, execute_upload

    hour_str = datetime.now(timezone.utc).strftime("%Y%m%d%H")
    seed = derive_seed(hour_str)
    output_dir = "/tmp/output"

    print(f"=== Tessera ad Infinitum — {hour_str} ===")
    print(f"Seed: {seed}")

    # Stage 1: Orchestrate (render 2048x2048 canvas)
    print("\n--- Stage 1: Orchestrate ---")
    run_orchestrate(seed=seed, output_dir=output_dir)

    # Stage 2: Slice (indexed PNG + 300 byte-array slices)
    print("\n--- Stage 2: Slice ---")
    run_slice(output_dir=output_dir, count=100)

    # Stage 3: Upload to R2
    print("\n--- Stage 3: Upload ---")
    account_id = os.environ["R2_ACCOUNT_ID"]
    bucket = os.environ["R2_BUCKET"]
    endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"

    plan = build_upload_plan(output_dir, hour_str)
    execute_upload(plan, bucket, endpoint_url)

    print(f"\n=== Done: {hour_str} seed={seed} ===")


@app.local_entrypoint()
def run_pipeline(seed: int = 0, recipe: str = ""):
    """Manual trigger: modal run modal_app.py [--seed 42] [--recipe grid_rect]"""
    if seed or recipe:
        # For manual runs with overrides, call orchestrate directly on Modal
        # rather than the cron function (which derives seed from UTC hour)
        _run_with_overrides.remote(seed=seed if seed else None, recipe=recipe if recipe else None)
    else:
        generate_universe_cron.remote()


@app.function(
    image=image,
    secrets=[r2_secret],
    timeout=900,
)
def _run_with_overrides(seed: int = None, recipe: str = None):
    """Manual run with seed/recipe overrides."""
    import json
    import os
    from datetime import datetime, timezone

    from scripts.orchestrate import derive_seed, run_orchestrate
    from scripts.slice import run_slice
    from scripts.upload import build_upload_plan, execute_upload

    hour_str = datetime.now(timezone.utc).strftime("%Y%m%d%H")

    if seed is None:
        seed = derive_seed(hour_str)

    output_dir = "/tmp/output"

    print(f"=== Tessera ad Infinitum (manual) — {hour_str} ===")
    print(f"Seed: {seed}, Recipe: {recipe or 'auto'}")

    run_orchestrate(seed=seed, recipe_name=recipe, output_dir=output_dir)
    run_slice(output_dir=output_dir, count=100)

    account_id = os.environ["R2_ACCOUNT_ID"]
    bucket = os.environ["R2_BUCKET"]
    endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"

    plan = build_upload_plan(output_dir, hour_str)
    execute_upload(plan, bucket, endpoint_url)

    print(f"\n=== Done: {hour_str} seed={seed} ===")
