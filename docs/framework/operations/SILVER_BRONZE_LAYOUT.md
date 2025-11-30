---
title: Bronze vs Silver Layout Control
summary: Independent path structure configuration for Bronze and Silver layers with semantic organization.
---

# Bronze/Silver Layout Separation - Implementation Complete ✅

## Overview

The medallion-foundry framework now supports fully independent path structure configuration for the Bronze (raw landing) and Silver (curated) layers. This enables:

- **Bronze**: System-organized raw data (`system=X/table=Y/pattern=Z/dt=YYYY-MM-DD`)
- **Silver**: Domain-organized curated data (`domain=X/entity=Y/vN/pattern=Z/load_date=YYYY-MM-DD`)

Each layer can be configured with different keys, ordering, and naming conventions without affecting the other.

---

## Architecture

### Bronze Layer (Raw Landing)

**Purpose**: Store raw data exactly as extracted from sources  
**Organization**: System-centric  
**Default Path Structure**:
```
system=retail_demo/table=orders/pattern=pattern1_full_events/dt=2025-01-20/
```

**Configurable Keys**:
```yaml
path_structure:
  bronze:
    system_key: "system"      # Source system identifier
    entity_key: "table"       # Source table/entity name
    pattern_key: "pattern"    # Load pattern identifier
    date_key: "dt"            # Extract date
```

### Silver Layer (Curated/Transformed)

**Purpose**: Store curated, business-ready data  
**Organization**: Domain-centric with versioning  
**Default Path Structure**:
```
domain=retail/entity=orders/v1/pattern=pattern1_full_events/load_date=2025-01-20/
```

**Configurable Keys**:
```yaml
path_structure:
  silver:
    domain_key: "domain"       # Business domain/organization
    entity_key: "entity"       # Curated entity/dataset name
    version_key: "v"           # Schema version prefix (e.g., "v1", "v2")
    pattern_key: "pattern"     # Source pattern for traceability (optional)
    load_date_key: "load_date" # Data load date partition
```

---

## Configuration

### YAML Syntax

Each pattern file defines both Bronze and Silver path structures independently:

```yaml
path_structure:
  # Bronze: Raw landing layer
  bronze:
    system_key: "system"
    entity_key: "table"
    pattern_key: "pattern"
    date_key: "dt"
  
  # Silver: Curated layer
  silver:
    domain_key: "domain"
    entity_key: "entity"
    version_key: "v"
    pattern_key: "pattern"
    load_date_key: "load_date"
```

### Key Semantics

| Layer | Key | Purpose | Example |
|-------|-----|---------|---------|
| **Bronze** | `system_key` | Source system identifier | `system=crm_system` |
| **Bronze** | `entity_key` | Source table/entity | `table=customers` |
| **Bronze** | `pattern_key` | Load pattern | `pattern=full_snapshot` |
| **Bronze** | `date_key` | Extraction date | `dt=2025-01-20` |
| **Silver** | `domain_key` | Business domain | `domain=sales` |
| **Silver** | `entity_key` | Curated entity | `entity=customers` |
| **Silver** | `version_key` | Schema version prefix | `v1`, `v2` |
| **Silver** | `pattern_key` | Bronze pattern traceability | `pattern=full_snapshot` |
| **Silver** | `load_date_key` | Load/transformation date | `load_date=2025-01-20` |

---

## Implementation Status

### ✅ Completed

**1. PathStructure Configuration Model** (`core/config/dataset.py`)
- Dataclass with `from_dict()` supporting nested `bronze`/`silver` subsections
- Backward compatible with legacy flat structure
- Defaults provided for all keys

**2. All 7 Pattern Files Updated**
- pattern_full.yaml
- pattern_cdc.yaml
- pattern_current_history.yaml
- pattern_hybrid_incremental_point.yaml
- pattern_hybrid_incremental_cumulative.yaml
- pattern_hybrid_cdc_point.yaml
- pattern_hybrid_cdc_cumulative.yaml

**3. Bronze Extractor Integration** (`core/paths.py`, `core/partitioning.py`)
- `build_bronze_relative_path()` reads configurable Bronze keys
- `build_bronze_partition()` extracts keys from configuration
- `BronzePartition` dataclass uses configured keys
- **Result**: Bronze directory structure is now configurable per pattern

**4. Silver Extractor Integration** (`core/paths.py`, `core/partitioning.py`)
- `build_silver_partition_path()` reads configurable Silver keys
- `build_silver_partition()` extracts all 5 Silver keys
- `SilverPartition` dataclass with `version_key` and `pattern_key`
- **Result**: Silver directory structure is fully configurable

**5. PolyBase DDL Generator** (`core/polybase/polybase_generator.py`)
- Domain-aware data source locations: `/domain=X/entity=Y/vN/`
- Version in external table names: `orders_v1_events_external`
- Pattern key configuration: `pattern=pattern_folder/`
- Load date aware sample queries
- **Result**: PolyBase DDL respects domain/entity/version organization

**6. Silver Sample Generation** (`scripts/generate_silver_samples.py`)
- Reads Bronze path keys for partition discovery
- Reads Silver path keys for output path building
- Backward compatible with legacy configurations

---

## Path Structure Examples

### Event Pattern (Full Load)

**Bronze** → **Silver** transformation:
```
Bronze: system=retail_demo/table=orders/pattern=pattern1_full_events/dt=2025-01-20/
         └─ Raw parquet files as extracted

Silver: domain=retail/entity=orders/v1/pattern=pattern1_full_events/load_date=2025-01-20/
         └─ Transformed, deduplicated parquet files
         └─ Business semantics applied
         └─ Ready for BI/Analytics
```

### State Pattern (SCD Type 2)

**Bronze** → **Silver** transformation:
```
Bronze: system=crm_system/table=customer_state/pattern=pattern3_scd/dt=2025-01-20/
         └─ Raw customer snapshots

Silver: domain=sales/entity=customers/v1/pattern=pattern3_scd/load_date=2025-01-20/
         └─ SCD2 tables with effective_from/to dates
         └─ Current and historical versions tracked
         └─ Point-in-time queries enabled
```

---

## Benefits

### Semantic Clarity
- **Bronze**: "Where did this raw data come from?" → system/table/pattern/date
- **Silver**: "What is this curated data?" → domain/entity/version/pattern/load_date

### Schema Evolution Support
```
v1: domain=retail/entity=orders/v1/load_date=2025-01-01/
v2: domain=retail/entity=orders/v2/load_date=2025-02-01/  # New schema
```

### Traceability
```
Silver: domain=retail/entity=orders/v1/pattern=pattern1_full_events/
         └─ pattern_key links back to source Bronze pattern
         └─ load_date tracks when data was promoted
```

### Flexibility
Each layer can optimize its structure independently:
- Bronze: Raw data organization
- Silver: Business-ready data organization
- Future: Gold could add cost/tier dimensions

---

## PolyBase Integration

PolyBase external tables now reflect the Silver domain structure:

```sql
-- Event pattern
CREATE EXTERNAL DATA SOURCE [silver_pattern1_full_events_v1_events_source]
WITH (
    TYPE = HADOOP,
    LOCATION = '/sampledata/silver_samples/env=dev/domain=retail/entity=orders/v1/'
);

CREATE EXTERNAL TABLE [dbo].[orders_v1_events_external]
WITH (
    LOCATION = 'pattern=pattern1_full_events/',
    DATA_SOURCE = [silver_pattern1_full_events_v1_events_source],
    ...
);

-- Version-aware queries
SELECT * FROM [dbo].[orders_v1_events_external] 
WHERE load_date = '2025-01-20';
```

**Benefits**:
- Table names include version for side-by-side schema support
- Data source location includes version path
- Load date filtering for temporal awareness

---

## Backward Compatibility

All changes maintain backward compatibility:

1. **Legacy Flat Structure**: If no `bronze`/`silver` subsections exist, defaults are used
2. **Configuration Optional**: All keys have sensible defaults
3. **No Breaking Changes**: Existing extractors and generators continue to work
4. **Graceful Fallback**: Missing configuration sections fall back to defaults

---

## Developer Guide

### Adding a New Pattern

1. Define separate `bronze` and `silver` path structures:
   ```yaml
   path_structure:
     bronze:
       system_key: "system"
       entity_key: "table"
       pattern_key: "pattern"
       date_key: "dt"
     silver:
       domain_key: "domain"
       entity_key: "entity"
       version_key: "v"
       pattern_key: "pattern"
       load_date_key: "load_date"
   ```

2. No code changes needed - the framework reads configuration

3. Test with `scripts/generate_silver_samples.py --limit 1`

### Customizing Path Structure

To use different keys:
```yaml
path_structure:
  bronze:
    system_key: "source_system"  # Custom key name
    entity_key: "source_table"
    pattern_key: "load_type"
    date_key: "extract_date"
  silver:
    domain_key: "business_domain"
    entity_key: "dataset_name"
    version_key: "schema_v"
    pattern_key: "source_pattern"
    load_date_key: "created_date"
```

The extractors will automatically use the configured key names.

---

## Testing & Validation

All 7 patterns verified:
- ✅ Bronze path discovery using configured keys
- ✅ Silver path construction using configured keys
- ✅ PolyBase DDL generation with version awareness
- ✅ Sample query generation with load_date filtering
- ✅ Backward compatibility with legacy configurations

---

## Future Enhancements

1. **Gold Layer**: Extend pattern for analytics layer with cost/tier organization
2. **Schema Registry**: Track version metadata and evolution
3. **Multi-Tenant Support**: Add tenant_key to Silver structure
4. **Data Lineage**: Enhanced traceability with pattern metadata in every record
5. **Incremental Processing**: Optimize artifact location for CDC/incremental patterns
