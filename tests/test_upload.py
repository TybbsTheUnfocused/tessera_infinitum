import json
import os
import pytest
from scripts.upload import build_upload_plan


def _make_output(tmp_path, num_slices=2):
    """Helper: create a minimal output dir matching orchestrate+slice output."""
    d = str(tmp_path)
    # canvas_indexed.png — just a tiny file
    with open(os.path.join(d, 'canvas_indexed.png'), 'wb') as f:
        f.write(b'fake-png')
    with open(os.path.join(d, 'metadata.json'), 'w') as f:
        json.dump({'seed': 42, 'contract_version': 1}, f)

    for plat in ['basalt', 'chalk', 'emery']:
        plat_dir = os.path.join(d, 'slices', plat)
        os.makedirs(plat_dir, exist_ok=True)
        for i in range(num_slices):
            with open(os.path.join(plat_dir, f'{i:03d}.bin'), 'wb') as f:
                f.write(b'\x00' * 10)

    with open(os.path.join(d, 'slices', 'index.json'), 'w') as f:
        json.dump({'count_per_platform': num_slices}, f)

    return d


def test_build_upload_plan_latest(tmp_path):
    d = _make_output(tmp_path)
    plan = build_upload_plan(d, hour_str='2026040914', skip_archive=False)

    # Should have latest/ entries for canvas, metadata, index, and slice bins
    latest_keys = [e['r2_key'] for e in plan if e['r2_key'].startswith('latest/')]
    assert 'latest/canvas.png' in latest_keys
    assert 'latest/metadata.json' in latest_keys
    assert 'latest/slices/index.json' in latest_keys
    assert 'latest/slices/basalt/000.bin' in latest_keys


def test_build_upload_plan_archive(tmp_path):
    d = _make_output(tmp_path)
    plan = build_upload_plan(d, hour_str='2026040914', skip_archive=False)

    archive_keys = [e['r2_key'] for e in plan if e['r2_key'].startswith('archive/')]
    assert 'archive/2026/04/09/14-canvas.png' in archive_keys
    assert 'archive/2026/04/09/14-metadata.json' in archive_keys
    # Slices should NOT be archived
    assert not any('slices' in k for k in archive_keys)


def test_build_upload_plan_skip_archive(tmp_path):
    d = _make_output(tmp_path)
    plan = build_upload_plan(d, hour_str='2026040914', skip_archive=True)

    archive_keys = [e['r2_key'] for e in plan if e['r2_key'].startswith('archive/')]
    assert len(archive_keys) == 0


def test_build_upload_plan_file_count(tmp_path):
    d = _make_output(tmp_path, num_slices=2)
    plan = build_upload_plan(d, hour_str='2026040914', skip_archive=False)

    # latest: canvas + metadata + index + 3 platforms * 2 slices = 9
    # archive: canvas + metadata = 2
    # total = 11
    assert len(plan) == 11
