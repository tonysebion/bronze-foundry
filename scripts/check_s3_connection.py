#!/usr/bin/env python3
"""Script to verify S3/MinIO connection and configuration.

This script mirrors the prior `tests/test_s3_connection.py` but is now
placed under `scripts/` so it's not collected by pytest.
"""

from pathlib import Path
from core.config.environment import EnvironmentConfig
from core.storage.uri import StorageURI
from core.storage.filesystem import create_filesystem
import sys


def load_environment_config():
    """Load and display the dev environment configuration."""
    print("=" * 60)
    print("TEST 1: Loading Environment Configuration")
    print("=" * 60)

    env_file = Path("environments/dev.yaml")

    if not env_file.exists():
        print(f"[ERROR] Environment config not found: {env_file}")
        return None

    env_config = EnvironmentConfig.from_yaml(env_file)

    print(f"[OK] Loaded environment: {env_config.name}")
    print(f"   S3 Endpoint: {env_config.s3.endpoint_url}")
    print(f"   Access Key: {env_config.s3.access_key_id}")
    print(f"   Region: {env_config.s3.region}")
    print("   Buckets:")
    for name, bucket in env_config.s3.buckets.items():
        print(f"     - {name} -> {bucket}")
    print()

    return env_config


def uri_parsing_demo(env_config):
    """Demonstrate URI parsing and bucket resolution."""
    print("=" * 60)
    print("TEST 2: URI Parsing and Bucket Resolution")
    print("=" * 60)

    test_uris = [
        "s3://source_data/source_samples",
        "s3://bronze_data/bronze_samples",
        "s3://mdf/source_samples",
        "./local/path/file.csv",
    ]

    for uri_str in test_uris:
        uri = StorageURI.parse(uri_str)
        fsspec_path = uri.to_fsspec_path(env_config)

        print(f"Original:  {uri_str}")
        print(f"  Backend: {uri.backend}")
        print(f"  Bucket:  {uri.bucket}")
        print(f"  Key:     {uri.key}")
        print(f"  Resolved: {fsspec_path}")
        print()


def s3_connection_test(env_config):
    """Test actual S3 connection to MinIO and list buckets and files."""
    print("=" * 60)
    print("TEST 3: S3 Connection to MinIO")
    print("=" * 60)

    try:
        # Parse S3 URI
        uri = StorageURI.parse("s3://source_data/source_samples")
        print(f"Testing URI: {uri.original}")
        print(f"Resolved to: {uri.to_fsspec_path(env_config)}")
        print()

        # Create filesystem
        print("Creating S3 filesystem...")
        fs = create_filesystem(uri, env_config)
        print(f"[OK] Filesystem created: {type(fs).__name__}")
        print()

        # List root of bucket
        print("Listing bucket root (mdf/)...")
        try:
            root_items = fs.ls("mdf", detail=False)
            print(f"[OK] Found {len(root_items)} items in bucket root:")
            for item in root_items[:10]:
                print(f"   - {item}")
            print()
        except Exception as e:
            print(f"[ERROR] Failed to list bucket root: {e}")
            print()

        # List source_samples directory
        print("Listing source_samples directory...")
        try:
            source_items = fs.ls("mdf/source_samples", detail=False)
            print(f"[OK] Found {len(source_items)} items in source_samples:")
            for item in source_items[:10]:
                print(f"   - {item}")
            print()
        except Exception as e:
            print(f"[ERROR] Failed to list source_samples: {e}")
            print()

        return True

    except Exception as e:
        print(f"[ERROR] Failed to connect to S3: {e}")
        print()
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run the script to check S3 connectivity and config."""
    print()
    print("=" * 60)
    print(" " * 10 + "S3/MinIO Connection Script")
    print("=" * 60)
    print()

    env_config = load_environment_config()
    if not env_config:
        print("❌ Cannot proceed without environment config")
        return 1

    uri_parsing_demo(env_config)
    connection_ok = s3_connection_test(env_config)

    if connection_ok:
        print("[OK] All critical checks passed!")
        return 0
    else:
        print("[ERROR] Connection failed. Please check MinIO and environment settings")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())

