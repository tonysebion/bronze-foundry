import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_black_formatting_check():
    """Ensure the repository is formatted with black using line-length 120.

    This mirrors the developer tooling and the `run_tests.py --black-check` behavior
    so that style violations are surfaced as a pytest failure in CI and locally.
    """
    targets = [
        "core",
        "extractors",
        "tests",
        "bronze_extract.py",
        "silver_extract.py",
    ]
    # Only include targets that exist in the repo
    targets = [str(ROOT / t) if Path(ROOT / t).exists() else t for t in targets]

    cmd = [sys.executable, "-m", "black", "--check", "--line-length=120", *targets]
    result = subprocess.run(cmd)
    assert result.returncode == 0, "black check failed; run 'black --line-length=120 .' to fix formatting"
