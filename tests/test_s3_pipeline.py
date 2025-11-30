"""Deprecated wrapper — the S3 pipeline check script has moved.

This module intentionally raises a module-skip so pytest doesn't import any
logic; run the new script in `scripts/check_s3_pipeline.py` interactively.
"""

import pytest

pytest.skip(
    "S3 pipeline check moved to scripts/check_s3_pipeline.py; run interactively if needed",
    allow_module_level=True,
)
