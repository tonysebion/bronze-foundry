# Documentation Gaps & Discrepancies Report

**Date:** December 6, 2025  
**Status:** 5 gaps identified, 1 critical gap fixed

---

## Summary

This report identifies 5 documentation gaps and discrepancies that could confuse users or cause implementation errors. The most critical issue (CLI flag inconsistency) has been addressed.

---

## 🔴 Gap #1: CLI Flag Inconsistency (CRITICAL) – **FIXED**

### Problem
Documentation inconsistently references CLI validation flags:
- Some sections mention `--validate` (non-existent flag)
- Some mention `--validate-only` (actual flag)
- Purpose of `--validate-only` vs `--dry-run` is unclear (both seem like "validation")

### Impact
**HIGH** – Users following Quick Start hit "unknown flag" errors and cannot validate configs before running.

### Files Affected
- `README.md` (line 39, 117)
- `docs/index.md` (Common Tasks table)

### Fix Applied ✅
- Updated `docs/index.md` to clarify both flags with explicit descriptions:
  - `--validate-only`: Check YAML syntax and configuration schema
  - `--dry-run`: Test connections without running extraction
- Added explicit validation flag mention to README.md Architecture Principles
- Expanded Bronze extraction flag documentation with clear use-case explanations

### Evidence
**Before:**
```bash
python bronze_extract.py --config config/my.yaml --validate  # (incorrect flag)
```

**After:**
```bash
# Check syntax/schema only
python bronze_extract.py --config config/my.yaml --validate-only

# Test connections without extraction  
python bronze_extract.py --config config/my.yaml --dry-run
```

---

## 🟠 Gap #2: Storage Backend Configuration Pattern Inconsistency

### Problem
Example configs show two different storage patterns without explaining abstraction:

**Local examples** (`api_example.yaml`):
```yaml
bronze:
  options:
    local_output_dir: ./output
```

**Cloud examples** (`s3_example.yaml`):
```yaml
platform:
  storage:
    source:
      backend: s3
      bucket: my-bucket
```

Users don't understand why local uses `local_output_dir` while S3 uses `storage.source.bucket`.

### Impact
**MEDIUM** – Confuses new users trying to migrate from local to cloud storage. Config pattern discovery is non-obvious.

### Files Affected
- `docs/examples/configs/examples/api_example.yaml`
- `docs/examples/configs/examples/s3_example.yaml`
- `README.md` (no explanation of storage abstraction)

### Recommendation
Add a **Storage Configuration Patterns** section to README explaining:
- How `local_output_dir` maps to filesystem storage
- How `storage.source/bronze/silver` abstracts cloud backends
- Migration path from local → S3/Azure

### Status
**NOT YET FIXED** – Requires new documentation section and example updates

---

## 🟠 Gap #3: Intent Config vs Legacy Config Confusion

### Problem
Documentation claims configs are "unified" (Bronze + Silver in one file) but:
- README line ~160: "each config now has both sections"
- Yet many old references still mention separate Bronze/Silver configs
- No migration guide for legacy configs → intent configs

### Impact
**MEDIUM** – Users with older configs are confused about whether to split/merge files or stay with legacy approach.

### Files Affected
- `README.md` (lines 160–170: intent config explanation)
- `docs/examples/configs/examples/` (mixed legacy + unified examples)
- Missing: Migration guide from legacy → intent config

### Recommendation
Add a **Config Migration Guide** explaining:
1. **Legacy approach** (separate Bronze + Silver files)
2. **New approach** (unified intent config with both sections)
3. **How to migrate** existing configs without breaking

### Status
**NOT YET FIXED** – Requires migration documentation + example consolidation

---

## 🟡 Gap #4: Python Version Specificity Missing

### Problem
- README badge says "Python 3.8+" but examples use f-strings, type hints (e.g., `dict[str, Any]`) that require 3.9+
- `pyproject.toml` lists support for 3.8–3.13 but:
  - CI likely doesn't test 3.8
  - Code may have 3.9+ idioms
- No version matrix showing what features work where

### Impact
**LOW-MEDIUM** – Users on Python 3.8 hit cryptic syntax errors. No clear guidance on minimum required version.

### Files Affected
- `README.md` (badge and Quick Start)
- `pyproject.toml` (requires-python)
- CI/CD config (what versions are tested?)

### Recommendation
1. Clarify: "Tested on Python 3.9–3.13. 3.8 may work but not officially supported."
2. Update Quick Start: "Use Python 3.9 or later for best compatibility"
3. Add a version matrix in docs if 3.8 support is desired

### Status
**NOT YET FIXED** – Needs version matrix + Quick Start update

---

## 🟡 Gap #5: Example Config Structure Mismatch

### Problem
README describes examples as "simple" starting points, but they contain advanced features:
- `api_example.yaml` – 48 lines, includes full Silver model definition
- `file_example.yaml` – includes intraday partitioning, change-tracking options
- Beginners expecting "minimal Bronze config" get overwhelmed

### Impact
**LOW** – Discourages beginners; forces reverse-engineering of "simple" examples to strip down to bare minimum.

### Files Affected
- `docs/examples/configs/examples/` – all examples have `silver:` sections
- `README.md` (line ~95: "Copy and edit the quick test config")
- `docs/index.md` (Quick Start links to these "example" configs)

### Recommendation
Create **two tiers** of examples:
1. **Minimal examples** (Bronze-only, 5–10 lines, one per source type)
2. **Full examples** (Bronze + Silver, advanced features) in `advanced/` folder
3. Update README to link minimal examples for Quick Start

### Status
**NOT YET FIXED** – Requires new minimal example files + documentation updates

---

## Implementation Priority

| Gap | Priority | Effort | Impact | Status |
|-----|----------|--------|--------|--------|
| #1 CLI Flags | 🔴 Critical | 1 hour | Blocks Quick Start | ✅ **DONE** |
| #2 Storage Patterns | 🟠 High | 2 hours | Confuses cloud migration | ⏳ Pending |
| #3 Intent Config | 🟠 High | 3 hours | Breaks config compatibility | ⏳ Pending |
| #4 Python Version | 🟡 Medium | 1 hour | Cryptic errors on 3.8 | ⏳ Pending |
| #5 Example Structure | 🟡 Medium | 2 hours | Overwhelms beginners | ⏳ Pending |

---

## Next Steps

1. ✅ **Gap #1 (DONE):** CLI flag consistency fixed in docs/index.md and README.md
2. ⏳ **Gap #2:** Create Storage Configuration Patterns section in README
3. ⏳ **Gap #3:** Add Config Migration Guide in docs/framework/
4. ⏳ **Gap #4:** Update version matrix and Quick Start with Python 3.9+ requirement
5. ⏳ **Gap #5:** Create minimal example configs and restructure examples/ directory

---

## Files Modified

- ✅ `docs/index.md` – Updated Common Tasks CLI table with clear flag descriptions
- ✅ `README.md` – Added validation flag clarification to Architecture Principles and intro text

---

## References

- Bronze CLI implementation: `bronze_extract.py` (lines 50–110)
- Silver CLI implementation: `silver_extract.py` (similar structure)
- Config examples: `docs/examples/configs/examples/`
- Configuration schema: `core/infrastructure/config/dataset.py`
