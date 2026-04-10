# Modal Migration Design

**Date:** 2026-04-10
**Status:** Draft
**Motivation:** GitHub Actions cron scheduling is unreliable (best-effort, delays of 2+ hours observed). Move the hourly generation pipeline to Modal for precise, consistent scheduling and execution.

## Decision

Single Modal app with one cron-scheduled function that runs the full pipeline: orchestrate, slice, upload. No changes to existing Python code; Modal wraps and calls the existing functions.

### Why not alternatives

- **External cron -> GH Actions `workflow_dispatch`:** Fixes scheduling delay but not runner queue delay. Two unreliable hops instead of one.
- **Multi-function Modal pipeline:** Overengineered. The pipeline is sequential, takes 2-5 minutes, and shares artifacts via the filesystem. Splitting into separate containers adds inter-stage networking and shared Volume complexity for no benefit.

## Architecture

### New file: `modal_app.py` (repo root)

Single file containing:

1. **`app`** — `modal.App("tessera-infinitum")`
2. **`image`** — Debian slim + Python 3.13, pip-installs `numpy`, `pillow`, `vnoise`, `scipy`, `boto3`. Copies `generator/` and `scripts/` into the image at `/app/`.
3. **`generate_universe_cron`** — The main function, decorated with `schedule=modal.Cron("0 * * * *")` and `secrets=[modal.Secret.from_name("r2-credentials")]`.
4. **`run_pipeline`** — A local `@app.local_entrypoint()` for manual testing via `modal run modal_app.py`.

### Cron function: `generate_universe_cron`

Executes three stages sequentially, reusing existing code with no modifications:

```
1. Derive seed from UTC hour  (orchestrate.derive_seed)
2. run_orchestrate(seed, output_dir="/tmp/output")
3. run_slice(output_dir="/tmp/output", count=100)
4. Build upload plan + execute_upload to R2
```

Output directory is `/tmp/output` (ephemeral container filesystem, discarded after each run).

Timeout: 900 seconds (15 minutes, matching the current GH Actions `timeout-minutes`).

### Secrets

A Modal Secret named **`r2-credentials`** with these environment variables:

| Variable | Source |
|---|---|
| `R2_ACCOUNT_ID` | Same value as GH Actions secret |
| `R2_ACCESS_KEY_ID` | Same value as GH Actions secret |
| `R2_SECRET_ACCESS_KEY` | Same value as GH Actions secret |
| `R2_BUCKET` | Same value as GH Actions secret |
| `AWS_ACCESS_KEY_ID` | Same value as `R2_ACCESS_KEY_ID` (boto3 needs this) |
| `AWS_SECRET_ACCESS_KEY` | Same value as `R2_SECRET_ACCESS_KEY` (boto3 needs this) |

### Manual trigger

A `@app.local_entrypoint()` function `run_pipeline` that accepts optional `--seed` and `--recipe` arguments, for testing the full pipeline without waiting for the cron schedule:

```
modal run modal_app.py              # derives seed from current UTC hour
modal run modal_app.py --seed 42    # override seed
modal run modal_app.py --recipe grid_maze  # force recipe
```

This calls the same `generate_universe_cron` function remotely.

## Cost

- Modal charges ~$0.192/CPU-hour for standard containers.
- At 2 min average per run: ~$0.0064/run, ~$2.30/month for 720 hourly runs.
- At 5 min worst case: ~$0.016/run, ~$4.60/month.
- Modal free tier provides $30/month in credits — well within budget.

## What stays unchanged

- All existing Python code: `generator/`, `scripts/orchestrate.py`, `scripts/slice.py`, `scripts/upload.py`, `scripts/recipes.py`.
- Seed derivation logic, determinism guarantees, metadata contract (`contract_version`).
- Pebble 64 palette order and canvas dimensions (2048x2048).
- The GitHub Actions workflow file remains in the repo as a `workflow_dispatch` backup.

## What changes

- **Scheduling:** GH Actions cron -> Modal cron. Precise to-the-second execution.
- **Execution environment:** GH Actions Ubuntu runner -> Modal Debian container.
- **New file:** `modal_app.py` at repo root.
- **New dependency:** `modal` added to `pyproject.toml` dev dependencies (only needed for deploy, not for the generator itself).

## Deployment steps

1. Install Modal CLI locally: `pip install modal` (or `uv pip install modal`).
2. Authenticate: `modal token new` (opens browser for login).
3. Create the `r2-credentials` secret in Modal dashboard or via CLI.
4. Deploy: `modal deploy modal_app.py`.
5. Verify: check Modal dashboard for the cron schedule, trigger a manual run, confirm R2 upload.

## Testing

- Run `modal run modal_app.py --seed 42 --recipe grid_rect` to verify end-to-end pipeline.
- Check Modal logs for orchestrate/slice/upload output.
- Verify R2 receives `latest/canvas.png`, `latest/metadata.json`, `latest/slices/`, and `archive/` entries.
- Let the cron run for one cycle and confirm timing precision.
