"""Tests for shared environment variable resolution helpers."""

import os

from core.infrastructure.config.env_utils import resolve_env_vars


def test_resolve_simple_string(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN", "abc123")
    assert resolve_env_vars("${TOKEN}") == "abc123"


def test_resolve_nested_structures(monkeypatch):
    monkeypatch.setenv("KEY", "value")
    cfg = {"path": "${KEY}", "list": ["${KEY}", {"nested": "${KEY}"}]}
    resolved = resolve_env_vars(cfg)
    assert resolved["path"] == "value"
    assert resolved["list"][0] == "value"
    assert resolved["list"][1]["nested"] == "value"


def test_missing_env_var_logs(monkeypatch, caplog):
    caplog.set_level("WARNING", logger="core.infrastructure.config.env_utils")
    result = resolve_env_vars("${MISSING}")
    assert "${MISSING}" in result
    assert "Environment variable MISSING not found" in caplog.text
