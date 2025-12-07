"""Backward compatibility shim for storage checksum utilities."""

import sys

from core.io.storage import checksum as checksum_impl

sys.modules[__name__] = checksum_impl
