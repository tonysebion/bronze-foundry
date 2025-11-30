# Silver Path Structure Fix

## Issue Found
The S3 silver_samples folder had incorrect path structure that didn't respect the `path_structure` YAML configuration.

**Incorrect structures generated:**
1. First attempt: Duplicate `silver_model` directory levels
2. Second attempt: Wrong directory order (`sample=` first instead of `domain=`)

## Root Cause
The `generate_silver_samples.py` script was:
1. Not reading the `path_structure.silver` configuration from the pattern YAML
2. Passing a `--silver-base` argument that forced silver_extract.py to use legacy path building instead of config-aware building
3. Hardcoding directory names like `sample=` and `silver_model=` that don't match the YAML specification

## Solution Applied

### Change 1: Updated `_rewrite_local_silver_config()`
Now sets `silver.output_dir` in the config so silver_extract.py will use the temp directory and apply config-based path building.

**Before**:
```python
def _rewrite_local_silver_config(original: Path, target: Path) -> Path:
```

**After**:
```python
def _rewrite_local_silver_config(original: Path, target: Path, silver_output_dir: Path) -> Path:
    # ...
    silver["output_dir"] = str(silver_output_dir)
```

### Change 2: Removed `--silver-base` argument
This forces silver_extract.py to use the config-based path building via `build_silver_partition_path()` which respects `path_structure`.

**Before**:
```python
cmd = [..., "--silver-base", str(silver_base)]
```

**After**:
```python
cmd = [...]  # No --silver-base argument
```

### Change 3: Updated `_build_s3_silver_prefix()`
Now reads the actual path_structure keys from the YAML and constructs the prefix accordingly.

**Before**:
```python
sample_key = path_config_keys.get("sample_key", "sample")
silver_model_key = path_config_keys.get("silver_model_key", "silver_model")
silver_subpath = Path(f"{sample_key}={config.pattern_folder}") / f"{silver_model_key}={config.silver_model}"
```

**After**:
```python
domain_key = path_config_keys.get("domain_key", "domain")
entity_key = path_config_keys.get("entity_key", "entity")
version_key = path_config_keys.get("version_key", "v")
pattern_key = path_config_keys.get("pattern_key", "pattern")
load_date_key = path_config_keys.get("load_date_key", "load_date")

# Build path: domain/entity/version/[pattern]/load_date
path_parts = [
    f"{domain_key}={config.domain}",
    f"{entity_key}={config.entity}",
    f"{version_key}{version}",
]
```

## After (Correct - Matches YAML Specification)
```
silver_samples/
  domain=retail_demo/
    entity=orders/
      v1/
        load_date=2025-11-13/
          event_date=2025-11-13/
            events.parquet
```

## YAML Specification Match
Pattern YAML specifies (from `path_structure.silver`):
```yaml
domain_key: "domain"        # ✅ domain=retail_demo
entity_key: "entity"        # ✅ entity=orders
version_key: "v"            # ✅ v1
pattern_key: "pattern"      # (optional: include_pattern_folder=False)
load_date_key: "load_date"  # ✅ load_date=2025-11-13
```

## Verification
✅ Domain-aware organization: Business domains first
✅ Entity organization: Entities under their domain
✅ Versioning support: Multiple versions can coexist (v1, v2, etc.)
✅ Load date partitioning: Incremental load support
✅ Event date sub-partitioning: CDC/temporal patterns working
✅ Configuration-driven: Respects path_structure from YAML

## Files Modified
- `scripts/generate_silver_samples.py`:
  - Line 326: Updated `_rewrite_local_silver_config()` signature and implementation
  - Line 285: Rewrote `_build_s3_silver_prefix()` to use actual path_structure keys
  - Line 615: Removed `--silver-base` argument from silver_extract.py call
  - Line 600-665: Simplified path building logic to rely on silver_extract.py's config-aware path building

