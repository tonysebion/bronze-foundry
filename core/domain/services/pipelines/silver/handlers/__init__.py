"""Silver pattern handlers for entity-specific processing.

This package contains handlers for each Silver entity pattern:
- EventHandler: Processes EVENT entity types
- StateHandler: Processes STATE and DERIVED_STATE entity types
- DerivedEventHandler: Processes DERIVED_EVENT entity types

Each handler implements the BasePatternHandler interface.
"""

from core.domain.services.pipelines.silver.handlers.base import BasePatternHandler
from core.domain.services.pipelines.silver.handlers.event_handler import EventHandler
from core.domain.services.pipelines.silver.handlers.state_handler import StateHandler
from core.domain.services.pipelines.silver.handlers.derived_event_handler import (
    DerivedEventHandler,
)

__all__ = [
    "BasePatternHandler",
    "EventHandler",
    "StateHandler",
    "DerivedEventHandler",
]
