"""Backward compatibility shim for Azure storage utilities."""

import sys

from core.io.storage import azure as azure_impl

sys.modules[__name__] = azure_impl
