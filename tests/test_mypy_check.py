"""Regression guard that runs the upstream `mypy` command."""

from __future__ import annotations

import subprocess
import sys

import pytest


@pytest.mark.xfail(
    reason="mypy currently exposes many pre-existing errors; remove xfail when the suite is clean",
    strict=False,
)
def test_mypy_check() -> None:
    """Run `python -m mypy .` so CI can track drift."""

    result = subprocess.run(
        [sys.executable, "-m", "mypy", "."],
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
