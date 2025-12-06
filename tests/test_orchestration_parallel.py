"""Tests for parallel orchestration module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import date
from pathlib import Path

from core.orchestration.parallel import run_parallel_extracts, _safe_run_extract
from core.pipeline.runtime.context import RunContext
from core.primitives.foundations.patterns import LoadPattern


class TestRunParallelExtracts:
    """Tests for run_parallel_extracts function."""

    def _make_context(self, name: str) -> RunContext:
        """Create a RunContext for testing."""
        return RunContext(
            cfg={"source": {"system": "test", "table": "test_table"}},
            run_date=date(2024, 1, 15),
            relative_path=f"system=test/table={name}",
            local_output_dir=Path("/tmp/bronze"),
            bronze_path=Path(f"/tmp/bronze/system=test/table={name}"),
            source_system="test",
            source_table=name,
            dataset_id=f"test.{name}",
            config_name=name,
            load_pattern=LoadPattern.SNAPSHOT,
            env_config=None,
            run_id=f"test-run-{name}",
        )

    @patch("core.orchestration.parallel.run_extract")
    def test_single_successful_extraction(self, mock_run_extract):
        """Test single successful extraction."""
        mock_run_extract.return_value = 0

        contexts = [self._make_context("config1")]
        results = run_parallel_extracts(contexts, max_workers=1)

        assert len(results) == 1
        config_name, status, error = results[0]
        assert config_name == "config1"
        assert status == 0
        assert error is None

    @patch("core.orchestration.parallel.run_extract")
    def test_multiple_successful_extractions(self, mock_run_extract):
        """Test multiple successful extractions."""
        mock_run_extract.return_value = 0

        contexts = [
            self._make_context("config1"),
            self._make_context("config2"),
            self._make_context("config3"),
        ]
        results = run_parallel_extracts(contexts, max_workers=2)

        assert len(results) == 3
        successful = sum(1 for _, status, _ in results if status == 0)
        assert successful == 3

    @patch("core.orchestration.parallel.run_extract")
    def test_single_failed_extraction(self, mock_run_extract):
        """Test single failed extraction."""
        mock_run_extract.side_effect = ValueError("Test error")

        contexts = [self._make_context("config1")]
        results = run_parallel_extracts(contexts, max_workers=1)

        assert len(results) == 1
        config_name, status, error = results[0]
        assert config_name == "config1"
        assert status == -1
        assert isinstance(error, ValueError)

    @patch("core.orchestration.parallel.run_extract")
    def test_mixed_success_and_failure(self, mock_run_extract):
        """Test mixed success and failure results."""
        def mock_extract(context):
            if context.config_name == "config2":
                raise RuntimeError("Config2 failed")
            return 0

        mock_run_extract.side_effect = mock_extract

        contexts = [
            self._make_context("config1"),
            self._make_context("config2"),
            self._make_context("config3"),
        ]
        results = run_parallel_extracts(contexts, max_workers=2)

        assert len(results) == 3

        # Find results by config name
        results_by_name = {name: (status, error) for name, status, error in results}

        assert results_by_name["config1"][0] == 0
        assert results_by_name["config2"][0] == -1
        assert results_by_name["config3"][0] == 0

    @patch("core.orchestration.parallel.run_extract")
    def test_empty_contexts_list(self, mock_run_extract):
        """Test with empty contexts list."""
        results = run_parallel_extracts([], max_workers=2)
        assert results == []
        mock_run_extract.assert_not_called()

    @patch("core.orchestration.parallel.run_extract")
    def test_max_workers_zero_normalized_to_one(self, mock_run_extract):
        """Test that max_workers <= 0 is normalized to 1."""
        mock_run_extract.return_value = 0

        contexts = [self._make_context("config1")]
        results = run_parallel_extracts(contexts, max_workers=0)

        assert len(results) == 1
        assert results[0][1] == 0

    @patch("core.orchestration.parallel.run_extract")
    def test_max_workers_negative_normalized_to_one(self, mock_run_extract):
        """Test that negative max_workers is normalized to 1."""
        mock_run_extract.return_value = 0

        contexts = [self._make_context("config1")]
        results = run_parallel_extracts(contexts, max_workers=-5)

        assert len(results) == 1
        assert results[0][1] == 0

    @patch("core.orchestration.parallel.run_extract")
    def test_nonzero_return_status(self, mock_run_extract):
        """Test extraction with non-zero return status (not an exception)."""
        mock_run_extract.return_value = 1  # Non-zero status

        contexts = [self._make_context("config1")]
        results = run_parallel_extracts(contexts, max_workers=1)

        assert len(results) == 1
        config_name, status, error = results[0]
        assert config_name == "config1"
        assert status == 1  # Returns actual status, not -1
        assert error is None


class TestSafeRunExtract:
    """Tests for _safe_run_extract helper function."""

    def _make_context(self, name: str) -> RunContext:
        """Create a RunContext for testing."""
        return RunContext(
            cfg={"source": {"system": "test", "table": "test_table"}},
            run_date=date(2024, 1, 15),
            relative_path=f"system=test/table={name}",
            local_output_dir=Path("/tmp/bronze"),
            bronze_path=Path(f"/tmp/bronze/system=test/table={name}"),
            source_system="test",
            source_table=name,
            dataset_id=f"test.{name}",
            config_name=name,
            load_pattern=LoadPattern.SNAPSHOT,
            env_config=None,
            run_id=f"test-run-{name}",
        )

    @patch("core.orchestration.parallel.run_extract")
    def test_successful_extraction(self, mock_run_extract):
        """Test successful extraction returns status 0."""
        mock_run_extract.return_value = 0
        context = self._make_context("test")

        status, error = _safe_run_extract(context)

        assert status == 0
        assert error is None

    @patch("core.orchestration.parallel.run_extract")
    def test_failed_extraction_returns_error(self, mock_run_extract):
        """Test failed extraction returns -1 and error."""
        mock_run_extract.side_effect = ValueError("Test error")
        context = self._make_context("test")

        status, error = _safe_run_extract(context)

        assert status == -1
        assert isinstance(error, ValueError)
        assert str(error) == "Test error"

    @patch("core.orchestration.parallel.run_extract")
    def test_exception_type_preserved(self, mock_run_extract):
        """Test that exception type is preserved."""
        class CustomError(Exception):
            pass

        mock_run_extract.side_effect = CustomError("Custom error")
        context = self._make_context("test")

        status, error = _safe_run_extract(context)

        assert status == -1
        assert isinstance(error, CustomError)


class TestParallelExtractsLogging:
    """Tests to verify logging behavior."""

    def _make_context(self, name: str) -> RunContext:
        """Create a RunContext for testing."""
        return RunContext(
            cfg={"source": {"system": "test", "table": "test_table"}},
            run_date=date(2024, 1, 15),
            relative_path=f"system=test/table={name}",
            local_output_dir=Path("/tmp/bronze"),
            bronze_path=Path(f"/tmp/bronze/system=test/table={name}"),
            source_system="test",
            source_table=name,
            dataset_id=f"test.{name}",
            config_name=name,
            load_pattern=LoadPattern.SNAPSHOT,
            env_config=None,
            run_id=f"test-run-{name}",
        )

    @patch("core.orchestration.parallel.run_extract")
    @patch("core.orchestration.parallel.logger")
    def test_logs_start_message(self, mock_logger, mock_run_extract):
        """Test that start message is logged."""
        mock_run_extract.return_value = 0

        contexts = [self._make_context("config1")]
        run_parallel_extracts(contexts, max_workers=2)

        # Check that info was called at least once
        assert mock_logger.info.called

    @patch("core.orchestration.parallel.run_extract")
    @patch("core.orchestration.parallel.logger")
    def test_logs_completion_summary(self, mock_logger, mock_run_extract):
        """Test that completion summary is logged."""
        mock_run_extract.return_value = 0

        contexts = [self._make_context("config1"), self._make_context("config2")]
        run_parallel_extracts(contexts, max_workers=2)

        # Check that summary was logged
        info_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("complete" in call.lower() for call in info_calls)
