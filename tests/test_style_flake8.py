import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_flake8_lint_check():
    """Run flake8 to ensure linting rules are satisfied across the repo."""
    # Exclude vendor/build directories already excluded by .flake8
    # Configure max-line-length to stay consistent with Black
    cmd = [
        sys.executable,
        "-m",
        "flake8",
        "--max-line-length=120",
        str(ROOT),
    ]
    result = subprocess.run(cmd)
    assert result.returncode == 0, "flake8 linting failed; fix issues reported by flake8"
