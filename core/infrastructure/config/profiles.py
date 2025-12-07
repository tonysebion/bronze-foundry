"""Model profile resolution for Silver layer configuration.

This module provides profile-to-model mappings that allow users to specify
high-level intent (e.g., "analytics", "operational") rather than specific
SilverModel values.
"""

from __future__ import annotations

from typing import Dict, Optional

from core.foundation.primitives.models import SilverModel


# =============================================================================
# Model Profiles - Configuration-level mappings from intent to implementation
# =============================================================================

MODEL_PROFILES: Dict[str, SilverModel] = {
    "analytics": SilverModel.SCD_TYPE_2,
    "operational": SilverModel.SCD_TYPE_1,
    "merge_ready": SilverModel.FULL_MERGE_DEDUPE,
    "cdc_delta": SilverModel.INCREMENTAL_MERGE,
    "snapshot": SilverModel.PERIODIC_SNAPSHOT,
}


def resolve_profile(profile_name: str | None) -> Optional[SilverModel]:
    """Resolve a profile name to a SilverModel.

    Args:
        profile_name: The profile name to resolve (e.g., "analytics", "snapshot").
            Case-insensitive with whitespace trimmed.

    Returns:
        The corresponding SilverModel, or None if profile_name is None or unknown.
    """
    if profile_name is None:
        return None
    key = profile_name.strip().lower()
    return MODEL_PROFILES.get(key)
