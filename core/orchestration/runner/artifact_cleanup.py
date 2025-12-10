"""Artifact cleanup utilities for Bronze extraction.

Provides consistent cleanup logic for local and remote artifacts.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core.infrastructure.io.storage.plan import StoragePlan

logger = logging.getLogger(__name__)

__all__ = ["ArtifactCleanup"]


class ArtifactCleanup:
    """Handles cleanup of local and remote artifacts.

    Provides consistent cleanup logic for:
    - Full directory cleanup (for resets/reruns)
    - Individual file cleanup (for failure recovery)
    """

    def __init__(
        self,
        output_dir: Path,
        storage_plan: Optional["StoragePlan"] = None,
    ) -> None:
        """Initialize cleanup helper.

        Args:
            output_dir: Local output directory
            storage_plan: Optional storage plan for remote cleanup
        """
        self.output_dir = output_dir
        self.storage_plan = storage_plan

    def cleanup_directory(self) -> None:
        """Remove and recreate the output directory.

        Used when resetting a partition for a clean rerun.
        """
        if not self.output_dir.exists():
            return

        logger.info("Clearing existing artifacts at %s before rerun", self.output_dir)
        shutil.rmtree(self.output_dir, ignore_errors=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def cleanup_files(self, files: List[Path], cleanup_enabled: bool = True) -> None:
        """Clean up individual files on failure.

        Args:
            files: List of file paths to clean up
            cleanup_enabled: Whether cleanup is enabled (from config)
        """
        if not cleanup_enabled or not files:
            return

        logger.info("Cleaning up %d files due to failure", len(files))

        for file_path in files:
            self._cleanup_local_file(file_path)
            self._cleanup_remote_file(file_path)

    def _cleanup_local_file(self, file_path: Path) -> None:
        """Remove a local file if it exists."""
        try:
            if file_path.exists():
                file_path.unlink()
                logger.debug("Deleted local file %s", file_path)
        except Exception as error:
            logger.warning("Failed to cleanup local file %s: %s", file_path, error)

    def _cleanup_remote_file(self, file_path: Path) -> None:
        """Remove a remote file if storage plan is configured."""
        if not self.storage_plan:
            return

        remote_path = self.storage_plan.remote_path_for(file_path)
        try:
            if self.storage_plan.delete(file_path):
                logger.info("Deleted remote artifact %s", remote_path)
            else:
                logger.debug(
                    "Remote artifact %s was not deleted (disabled or missing)",
                    remote_path,
                )
        except Exception as error:
            logger.warning(
                "Failed to delete remote artifact %s: %s",
                remote_path,
                error,
            )
