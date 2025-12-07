"""Regression guard that runs the upstream `mypy` command."""

from __future__ import annotations

import subprocess
import sys

import pytest


def test_mypy_check() -> None:
    """Run `python -m mypy .` so CI can track drift."""

    cmd = [sys.executable, "-m", "mypy", "."]
    result = subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        pytest.fail(
            "mypy reported type problems:\n"
            f"{result.stdout}\n"
            f"{result.stderr}"
        )
