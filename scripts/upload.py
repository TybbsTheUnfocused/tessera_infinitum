#!/usr/bin/env python3
# scripts/upload.py
"""
Tessera ad Infinitum R2 uploader.

Reads the output directory produced by orchestrate.py + slice.py and
uploads everything to Cloudflare R2 using the S3-compatible API.
"""
import argparse
import os
from datetime import datetime, timezone

import boto3


def build_upload_plan(output_dir, hour_str, skip_archive=False):
    """Build a list of (local_path, r2_key) upload entries.

    Args:
        output_dir: local directory with canvas_indexed.png, metadata.json, slices/.
        hour_str: 'YYYYMMDDHH' string for archive path construction.
        skip_archive: if True, omit archive/ entries.

    Returns:
        list of dicts with 'local_path' and 'r2_key'.
    """
    plan = []

    canvas_path = os.path.join(output_dir, 'canvas_indexed.png')
    meta_path = os.path.join(output_dir, 'metadata.json')

    # latest/
    plan.append({'local_path': canvas_path, 'r2_key': 'latest/canvas.png'})
    plan.append({'local_path': meta_path, 'r2_key': 'latest/metadata.json'})

    # latest/slices/
    slices_dir = os.path.join(output_dir, 'slices')
    index_path = os.path.join(slices_dir, 'index.json')
    if os.path.exists(index_path):
        plan.append({'local_path': index_path, 'r2_key': 'latest/slices/index.json'})

    for platform in sorted(os.listdir(slices_dir)):
        plat_dir = os.path.join(slices_dir, platform)
        if not os.path.isdir(plat_dir):
            continue
        for bin_file in sorted(os.listdir(plat_dir)):
            if bin_file.endswith('.bin'):
                local = os.path.join(plat_dir, bin_file)
                plan.append({
                    'local_path': local,
                    'r2_key': f'latest/slices/{platform}/{bin_file}',
                })

    # archive/ (master + metadata only, no slices)
    if not skip_archive:
        # Parse YYYYMMDDHH into archive path components
        year = hour_str[0:4]
        month = hour_str[4:6]
        day = hour_str[6:8]
        hour = hour_str[8:10]
        prefix = f'archive/{year}/{month}/{day}/{hour}'
        plan.append({'local_path': canvas_path, 'r2_key': f'{prefix}-canvas.png'})
        plan.append({'local_path': meta_path, 'r2_key': f'{prefix}-metadata.json'})

    return plan


def execute_upload(plan, bucket, endpoint_url, dry_run=False):
    """Execute the upload plan against R2.

    Args:
        plan: list of dicts with 'local_path' and 'r2_key'.
        bucket: R2 bucket name.
        endpoint_url: S3-compatible endpoint URL.
        dry_run: if True, print plan without uploading.
    """
    if dry_run:
        print(f"DRY RUN — {len(plan)} files would be uploaded to {bucket}:")
        for entry in plan:
            size = os.path.getsize(entry['local_path'])
            print(f"  {entry['local_path']} → {entry['r2_key']} ({size} bytes)")
        return

    s3 = boto3.client('s3', endpoint_url=endpoint_url)

    for entry in plan:
        print(f"  Uploading {entry['r2_key']}...", end='', flush=True)
        s3.upload_file(entry['local_path'], bucket, entry['r2_key'])
        print(' done')

    print(f"Uploaded {len(plan)} files to {bucket}")


def main():
    parser = argparse.ArgumentParser(description='Tessera ad Infinitum R2 Uploader')
    parser.add_argument('--output-dir', type=str, default='output',
                        help='Directory with orchestrate + slice output')
    parser.add_argument('--skip-archive', action='store_true',
                        help='Upload to latest/ only, skip archive/')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print upload plan without uploading')
    args = parser.parse_args()

    # R2 config from environment
    account_id = os.environ.get('R2_ACCOUNT_ID', '')
    bucket = os.environ.get('R2_BUCKET', '')
    endpoint_url = f'https://{account_id}.r2.cloudflarestorage.com'

    hour_str = datetime.now(timezone.utc).strftime('%Y%m%d%H')

    plan = build_upload_plan(args.output_dir, hour_str, skip_archive=args.skip_archive)
    print(f"Upload plan: {len(plan)} files → {bucket}")
    execute_upload(plan, bucket, endpoint_url, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
