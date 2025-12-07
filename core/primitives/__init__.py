"""Backward compatibility shim for core.primitives."""
from core._compat.primitives import *  # noqa: F401,F403
from core._compat.primitives import __all__ as _compat_all

__all__ = list(_compat_all)
