"""Shared helpers for running storage health checks."""

from __future__ import annotations

from typing import Any, Callable, Optional

from core.infrastructure.io.storage.base import (
    HealthCheckTracker,
    attempt_health_check_action,
)

WriteAction = Callable[[], Any]
ReadAction = Callable[[], Any]
ListAction = Callable[[], Any]
DeleteAction = Callable[[], Any]
ReadValidator = Callable[[Any], bool]


def validate_storage_permissions(
    tracker: HealthCheckTracker,
    *,
    write_action: WriteAction,
    read_action: ReadAction,
    list_action: ListAction,
    delete_action: DeleteAction,
    read_validator: Optional[ReadValidator] = None,
    error_formatter: Optional[Callable[[BaseException], str]] = None,
    write_error_message: str = "Write permission failed",
    read_error_message: str = "Read permission failed",
    list_error_message: str = "List permission failed",
    delete_error_message: str = "Delete permission failed",
    read_failure_message: str = "Read content mismatch",
) -> None:
    """Run the standard write/read/list/delete permission checks."""

    write_result = attempt_health_check_action(
        tracker,
        write_action,
        error_message=write_error_message,
        error_formatter=error_formatter,
    )
    if write_result is not None:
        tracker.permissions["write"] = True

        read_result = attempt_health_check_action(
            tracker,
            read_action,
            error_message=read_error_message,
            error_formatter=error_formatter,
        )
        if read_result is not None:
            is_valid = (
                read_validator(read_result)
                if read_validator
                else bool(read_result)
            )
            if is_valid:
                tracker.permissions["read"] = True
            else:
                tracker.add_error(read_failure_message)

    list_result = attempt_health_check_action(
        tracker,
        list_action,
        error_message=list_error_message,
        error_formatter=error_formatter,
    )
    if list_result is not None:
        tracker.permissions["list"] = True

    if tracker.permissions["write"]:
        delete_result = attempt_health_check_action(
            tracker,
            delete_action,
            error_message=delete_error_message,
            error_formatter=error_formatter,
        )
        if delete_result is not None:
            tracker.permissions["delete"] = True
