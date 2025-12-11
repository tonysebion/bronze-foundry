from __future__ import annotations

from typing import Any, Dict, List


def infer_schema(records: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    if not records:
        return []
    keys = sorted(
        {key for record in records if isinstance(record, dict) for key in record.keys()}
    )
    schema_snapshot: List[Dict[str, str]] = []
    for key in keys:
        value = next(
            (
                record.get(key)
                for record in records
                if isinstance(record, dict) and key in record
            ),
            None,
        )
        schema_snapshot.append(
            {
                "name": key,
                "dtype": type(value).__name__ if value is not None else "unknown",
            }
        )
    return schema_snapshot
