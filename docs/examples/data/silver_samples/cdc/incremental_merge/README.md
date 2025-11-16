# Cdc silver samples (incremental merge)

This folder contains silver artifacts produced from the Bronze `cdc` samples using the `incremental_merge` Silver model.

- **Source Bronze pattern**: `cdc`
- **Silver model**: `incremental_merge`
- **Regeneration command**: `python scripts/generate_silver_samples.py --formats both`

For details on the Silver model presets, see `docs/EXTRACTION_GUIDANCE.md` and the matching config in `docs/examples/configs/`.
