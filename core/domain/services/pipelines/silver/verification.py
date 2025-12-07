"""Checksum verification for Bronze data before Silver promotion."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Tuple

from core.infrastructure.io.storage import (
    ChecksumVerificationResult,
    QuarantineResult,
    verify_checksum_manifest_with_result,
    quarantine_corrupted_files,
)

if TYPE_CHECKING:
    from core.infrastructure.config import DatasetConfig

logger = logging.getLogger(__name__)


@dataclass
class VerificationConfig:
    """Configuration for checksum verification."""

    verify_checksum: Optional[bool] = None
    skip_verification_if_fresh: bool = True
    freshness_threshold_seconds: int = 300
    quarantine_on_failure: bool = True


class ChecksumVerifier:
    """Verifies Bronze data checksums before Silver promotion.

    This class handles:
    - Determining if verification should run based on config and freshness
    - Verifying checksums against the manifest
    - Quarantining corrupted files if enabled
    """

    def __init__(
        self,
        bronze_path: Path,
        dataset: "DatasetConfig",
        config: Optional[VerificationConfig] = None,
    ) -> None:
        """Initialize the verifier.

        Args:
            bronze_path: Path to Bronze partition to verify.
            dataset: Dataset configuration with Silver settings.
            config: Optional verification configuration.
        """
        self.bronze_path = bronze_path
        self.dataset = dataset
        self.config = config or VerificationConfig()

    def should_verify(self) -> bool:
        """Determine if checksum verification should run.

        Returns True if:
        - verify_checksum is explicitly True, OR
        - verify_checksum is None and dataset.silver.require_checksum is True

        Returns False if:
        - verify_checksum is explicitly False
        - Fast path: manifest is fresh (less than freshness_threshold seconds old)
        """
        # Explicit override takes precedence
        if self.config.verify_checksum is not None:
            verify = self.config.verify_checksum
        else:
            # Fall back to dataset config
            verify = getattr(self.dataset.silver, "require_checksum", False)

        if not verify:
            return False

        # Fast path: skip verification if manifest is very fresh
        if self.config.skip_verification_if_fresh:
            manifest_path = self.bronze_path / "_checksums.json"
            if manifest_path.exists():
                try:
                    mtime = manifest_path.stat().st_mtime
                    age_seconds = time.time() - mtime
                    if age_seconds < self.config.freshness_threshold_seconds:
                        logger.debug(
                            "Skipping checksum verification - manifest age %.1fs < threshold %ds",
                            age_seconds,
                            self.config.freshness_threshold_seconds,
                        )
                        return False
                except OSError:
                    pass  # Proceed with verification if we can't check freshness

        return True

    def verify(
        self,
    ) -> Tuple[ChecksumVerificationResult, Optional[QuarantineResult]]:
        """Verify Bronze chunk checksums and quarantine corrupted files.

        Returns:
            Tuple of verification result and optional quarantine result.
        """
        result = verify_checksum_manifest_with_result(self.bronze_path)

        if result.valid:
            logger.info(
                "Bronze checksum verification passed: %d files verified in %.1fms",
                len(result.verified_files),
                result.verification_time_ms,
            )
            return result, None

        corrupted = result.mismatched_files + result.missing_files
        logger.error(
            "Bronze checksum verification failed for %s: %d corrupted/missing files",
            self.bronze_path,
            len(corrupted),
        )

        quarantine_result: Optional[QuarantineResult] = None
        if self.config.quarantine_on_failure and result.mismatched_files:
            quarantine_result = quarantine_corrupted_files(
                self.bronze_path,
                result.mismatched_files,
                reason="checksum_verification_failed",
            )
            logger.warning(
                "Quarantined %d corrupted files to %s",
                quarantine_result.count,
                quarantine_result.quarantine_path,
            )

        return result, quarantine_result
