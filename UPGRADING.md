# Upgrading Guide

## 1.0.0 -> Unreleased (toward 1.1.0)

### New Capabilities
- Typed config models (Pydantic) embedded in loaded config dicts under `__typed_model__`.
- `SilverArtifactWriter` protocol (`core.silver.writer`) and `DefaultSilverArtifactWriter` implementation.
- Partition abstractions: `BronzePartition`, `SilverPartition` (centralized path logic).
- Clear documentation that Bronze sample fixtures must be created before running extractors/tests (e.g., via `python scripts/generate_sample_data.py`).
- Structured deprecation & compatibility warnings.

### Deprecations (Removal Target 1.3.0)
| Code   | Description | Action Required |
|--------|-------------|-----------------|
| CFG001 | Implicit fallback using `platform.bronze.output_dir` as `local_path` | Add explicit `platform.bronze.local_path` |
| CFG002 | Legacy `source.api.url` key | Rename to `source.api.base_url` |
| CFG003 | Missing `source.api.endpoint` defaulting to `/` | Add explicit `endpoint` |
| API001 | Positional `write_silver_outputs` wrapper (REMOVED) | The wrapper has been removed; use `DefaultSilverArtifactWriter().write()` |
| STREAM001 | Legacy `silver_extract.py --stream` / `--resume` flags | Migrate to `SilverProcessor` chunking; update automation and docs to rely on metadata/checksums (see `docs/framework/operations/legacy-streaming.md`). |

### Migration Steps
1. Use `DefaultSilverArtifactWriter` instead of the removed wrapper.
2. Update configs: add `platform.bronze.local_path` where missing.
3. Replace any `source.api.url` with `base_url` and ensure `endpoint` present.
4. (Optional) Begin consuming typed models:
   ```python
   cfg = load_config(path)
   typed = cfg.get("__typed_model__")  # RootConfig instance
   ```
5. Ensure Bronze fixtures exist before testing or extraction by running `python scripts/generate_sample_data.py` (or providing an equivalent `sampledata/source_samples` tree); the old bootstrap helper is no longer available.
6. Remove any workflows or docs still invoking `--stream`/`--resume`; reruns now rely on `_metadata.json`/`_checksums.json` plus Bronze load patterns.

### Future (Post 1.1.0)
- Wrapper removal warnings will escalate to errors in 1.2.0 before deletion in 1.3.0.
- Expect stricter type enforcement and possible removal of dict fallbacks after 1.3.0.

### Troubleshooting
- If you see `BronzeFoundryCompatibilityWarning`, implement the required explicit config change.
- For `BronzeFoundryDeprecationWarning`, plan to remediate before the stated removal version.
