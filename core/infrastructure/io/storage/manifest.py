"""Manifest inspection helpers moved into the infrastructure layer."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.foundation.primitives.patterns import LoadPattern
from core.infrastructure.io.storage.checksum import verify_checksum_manifest

logger = logging.getLogger(__name__)

__all__ = ["ManifestInspector", "ManifestInspectionResult"]


class ManifestInspectionResult:
    """Result of manifest inspection."""

    def __init__(
        self,
        exists: bool = False,
        valid: bool = False,
        needs_cleanup: bool = False,
        previous_schema: Optional[List[Dict[str, Any]]] = None,
        error_message: Optional[str] = None,
    ) -> None:
        self.exists = exists
        self.valid = valid
        self.needs_cleanup = needs_cleanup
        self.previous_schema = previous_schema
        self.error_message = error_message


class ManifestInspector:
    """Inspect Bronze manifests and derive necessary state."""

    def __init__(
        self,
        output_dir: Path,
        load_pattern: Optional[LoadPattern] = None,
    ) -> None:
        self.output_dir = output_dir
        self.load_pattern = load_pattern
        self.manifest_path = output_dir / "_checksums.json"

    def inspect(self) -> ManifestInspectionResult:
        if not self.manifest_path.exists():
            return ManifestInspectionResult(exists=False)

        expected_pattern = self.load_pattern.value if self.load_pattern else None

        try:
            manifest = verify_checksum_manifest(
                self.output_dir,
                expected_pattern=expected_pattern,
            )
            schema = self._extract_schema(manifest)
            return ManifestInspectionResult(
                exists=True,
                valid=True,
                previous_schema=schema,
            )
        except (ValueError, FileNotFoundError) as exc:
            loaded_manifest = self._load_manifest_json()
            schema = self._extract_schema(loaded_manifest)
            return ManifestInspectionResult(
                exists=True,
                valid=False,
                needs_cleanup=True,
                previous_schema=schema,
                error_message=str(exc),
            )

    def _load_manifest_json(self) -> Optional[Dict[str, Any]]:
        if not self.manifest_path.exists():
            return None
        try:
            text = self.manifest_path.read_text(encoding="utf-8")
            data: Dict[str, Any] = json.loads(text)
            return data
        except Exception:
            return None

    def _extract_schema(
        self, manifest: Optional[Dict[str, Any]]
    ) -> Optional[List[Dict[str, Any]]]:
        if not manifest:
            return None
        schema = manifest.get("schema")
        if isinstance(schema, list):
            return schema
        return None
