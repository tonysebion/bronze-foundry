"""Legacy marker for tests package; moved to `tests/support/` to avoid pytest package discovery.

This file is intentionally left minimal. If you need test package level data, prefer
`tests/support` to avoid pytest collection confusion. For now this file will remain a no-op.
"""


# NOTE: We keep this file as a placeholder for legacy usage. Where possible, prefer
# moving utilities into `tests/support/` and avoid referencing the test-package itself.
