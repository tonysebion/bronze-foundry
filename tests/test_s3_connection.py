"""Deprecated wrapper — the S3 connection check script has moved.

This module intentionally raises a module-skip so pytest won't import any
logic; the script to run interactively is `scripts/check_s3_connection.py`.
"""

import pytest

pytest.skip(
    "S3 connection check moved to scripts/check_s3_connection.py; run interactively if needed",
    allow_module_level=True,
)
