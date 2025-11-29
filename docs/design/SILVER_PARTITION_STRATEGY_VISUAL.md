# Silver Layer Partition Strategy: Visual Comparison

## Overview

This document shows the actual partition structure vs. the ideal structure for each pattern, with visual trees and query examples.

---

## Pattern 1: Full Events ✅

### Directory Structure (OPTIMAL)

```
silver_samples/sample=pattern1_full_events/
  silver_model=incremental_merge/
    domain=retail_demo/
      entity=orders/
        v1/
          load_date=2025-11-13/
            event_date=2025-11-13/
              events.parquet
              _metadata.json
            event_date=2025-11-14/
              events.parquet
            event_date=2025-11-15/
              events.parquet
            ...
```

### Query Pattern

```sql
-- Time-range query (works great with partition pruning)
SELECT * FROM [dbo].[orders_events_external]
WHERE event_date >= '2025-11-13'
  AND event_date <= '2025-11-15'
  AND status = 'completed';

-- Point-in-time query
SELECT * FROM [dbo].[orders_events_external]
WHERE event_date = '2025-11-14'
  AND customer_id = 'CUST123'
ORDER BY event_ts DESC;
```

### Partition Pruning

✅ **Excellent** - Polybase scans only event_date=2025-11-14 partition

---

## Pattern 3: SCD Type 2 State ✅

### Directory Structure (OPTIMAL)

```
silver_samples/sample=pattern3_scd_state/
  silver_model=scd_type_2/
    domain=retail_demo/
      entity=orders/
        v1/
          load_date=2025-11-13/
            effective_from_date=2024-01-09/
              state_history.parquet
              _metadata.json
            effective_from_date=2024-01-10/
              state_history.parquet
            effective_from_date=2024-01-19/
              state_history.parquet
            ...
```

### Query Pattern

```sql
-- Point-in-time state query
SELECT * FROM [dbo].[orders_state_history_external]
WHERE effective_from_date <= '2025-11-15'
  AND (effective_to_dt IS NULL OR effective_to_dt > '2025-11-15')
  AND is_current = 1;

-- State changes for specific order
SELECT * FROM [dbo].[orders_state_history_external]
WHERE order_id = 'ORD123'
ORDER BY effective_from_dt DESC;
```

### Partition Pruning

✅ **Good** - Polybase scans only partitions up to target date (when combined with effective_to_dt filter)

---

## Pattern 6: Hybrid Incremental Point (CURRENT vs. IDEAL)

### CURRENT Structure ❌

```
silver_samples/sample=pattern6_hybrid_incremental_point/
  silver_model=scd_type_1/
    domain=retail_demo/
      entity=orders/
        v1/
          load_date=2025-11-14/
            effective_from_dt=2025-11-14/    ❌ Unnecessary partition
              state.parquet
              _metadata.json
          load_date=2025-11-15/
            effective_from_dt=2025-11-15/    ❌ Unnecessary partition
              state.parquet
          load_date=2025-11-16/
            effective_from_dt=2025-11-16/    ❌ Unnecessary partition
              state.parquet
          ...
```

### CURRENT Query Pattern ❌

```sql
-- Problem: What's the current status of order ORD123?
-- User knows they want "current" state but...

-- Option 1: Must know latest date
SELECT * FROM [dbo].[orders_state_external]
WHERE effective_from_dt = '2025-11-24'    -- Hardcoded date, fragile
  AND order_id = 'ORD123';

-- Option 2: Must do subquery
SELECT * FROM [dbo].[orders_state_external]
WHERE effective_from_dt = (
  SELECT MAX(effective_from_dt)
  FROM [dbo].[orders_state_external]
)
AND order_id = 'ORD123';    -- Complex!
```

### Current Partition Pruning

❌ **Poor** - User must know latest date or write subquery

---

### IDEAL Structure ✅

```
silver_samples/sample=pattern6_hybrid_incremental_point/
  silver_model=scd_type_1/
    domain=retail_demo/
      entity=orders/
        v1/
          load_date=2025-11-14/
            state.parquet           ✅ Single file per load date
            _metadata.json          ✅ No effective_from_dt partition
          load_date=2025-11-15/
            state.parquet
          load_date=2025-11-16/
            state.parquet
          ...
```

### Ideal Query Pattern ✅

```sql
-- Simple: What's the current status of order ORD123?
SELECT * FROM [dbo].[orders_state_external]
WHERE order_id = 'ORD123';
-- ✅ Query is intuitive, matches user intent

-- Historical: What was the status on 2025-11-15?
SELECT * FROM [dbo].[orders_state_external]
WHERE order_id = 'ORD123'
  AND load_date = '2025-11-15'
  AND is_current = 1;
```

### Ideal Partition Pruning

✅ **Simple** - Single unpartitioned file per load_date, no subqueries needed

---

## Pattern 7: Hybrid Incremental Cumulative (CURRENT vs. IDEAL)

### CURRENT Structure ❌

```
silver_samples/sample=pattern7_hybrid_incremental_cumulative/
  silver_model=scd_type_1/
    domain=retail_demo/
      entity=orders/
        v1/
          load_date=2025-11-13/
            effective_from_dt=2025-11-13/    ❌ Why partition by change date?
              state.parquet                    ❌ State is overwritten anyway
          load_date=2025-11-14/
            effective_from_dt=2025-11-14/    ❌ Old records not here anymore
              state.parquet
          load_date=2025-11-15/
            effective_from_dt=2025-11-15/    ❌ Partition grows daily
              state.parquet
          ...
```

### CURRENT Query Challenge ❌

```sql
-- Problem: "What was the status on 2025-11-14?"
-- The status value from 2025-11-14 was overwritten on 2025-11-15
-- So it doesn't exist in effective_from_dt=2025-11-14 partition anymore!

-- Even if we query that partition:
SELECT * FROM [dbo].[orders_state_external]
WHERE effective_from_dt = '2025-11-14'
  AND order_id = 'ORD123';
-- Returns NOTHING - because that old value was overwritten
```

### CURRENT Semantics Conflict

The date partition **doesn't match** SCD1 semantics:

```
Timeline for a specific order:

With date partitioning:
  2025-11-13: status = 'pending'     (in partition 2025-11-13)
  2025-11-14: status = 'shipped'     (overwrites 'pending', in partition 2025-11-14)
  2025-11-15: status = 'delivered'   (overwrites 'shipped', in partition 2025-11-15)

But SCD1 means:
  - 2025-11-13: partition contains 'pending' ✓
  - 2025-11-14: partition contains 'shipped' BUT 'pending' is GONE ✗
  - 2025-11-15: partition contains 'delivered' BUT 'shipped' is GONE ✗

This violates the partition contract that "all records from that date are in that partition"
```

---

### IDEAL Structure ✅

```
silver_samples/sample=pattern7_hybrid_incremental_cumulative/
  silver_model=scd_type_1/
    domain=retail_demo/
      entity=orders/
        v1/
          load_date=2025-11-13/
            state.parquet           ✅ Complete snapshot of all current orders
            _metadata.json
          load_date=2025-11-14/
            state.parquet           ✅ Updated snapshot (some orders changed)
          load_date=2025-11-15/
            state.parquet           ✅ Another update
          ...
```

### Ideal Query Pattern ✅

```sql
-- "What's the current status?"
SELECT * FROM [dbo].[orders_state_external]
WHERE load_date = (SELECT MAX(load_date) FROM [dbo].[orders_state_external])
  AND order_id = 'ORD123';

-- Or using temporal function:
SELECT * FROM [dbo].[get_orders_state_external_as_of]('2025-11-15');

-- "What was the status on 2025-11-14?"
SELECT * FROM [dbo].[orders_state_external]
WHERE load_date = '2025-11-14'
  AND order_id = 'ORD123';
-- Returns the snapshot from 2025-11-14, which was current at that time
```

### Ideal Semantics

Clear mapping between structure and semantics:

```
Each load_date partition = "Complete snapshot of current state at that time"

2025-11-13: 'pending'     ← That's what was current
2025-11-14: 'shipped'     ← That's what became current
2025-11-15: 'delivered'   ← That's what became current

Query any partition → Get what was current at that time ✓
```

---

## Side-by-Side Comparison

### Query: "Current status of order X"

| Pattern | Current ❌ | Ideal ✅ |
|---------|----------|--------|
| Pattern 6 | `WHERE effective_from_dt = (SELECT MAX(...))` | `WHERE order_id = 'X'` |
| Pattern 7 | `WHERE effective_from_dt = (SELECT MAX(...))` | `WHERE order_id = 'X'` |

### Query: "Status on specific date"

| Pattern | Current ❌ | Ideal ✅ |
|---------|----------|--------|
| Pattern 6 | Cannot answer accurately | `WHERE load_date = @date` |
| Pattern 7 | Returns wrong data | `WHERE load_date = @date` |

### Partition Count (daily updates, 30 days)

| Pattern | Current ❌ | Ideal ✅ |
|---------|----------|--------|
| Pattern 6 | 30 date partitions | 30 load_date partitions (1 file each) |
| Pattern 7 | 30 date partitions | 30 load_date partitions (1 file each) |

---

## Storage and Performance Implications

### Current Approach (Patterns 6 & 7)

**Directory Structure Impact:**
```
.../load_date=2025-11-13/
    effective_from_dt=2025-11-13/state.parquet      (100 MB)
.../load_date=2025-11-14/
    effective_from_dt=2025-11-14/state.parquet      (105 MB)
.../load_date=2025-11-15/
    effective_from_dt=2025-11-15/state.parquet      (102 MB)

Total for 30 days: 30 directories deep x 2 levels = 60 partition checks per query
```

**Query Performance:**
```
SELECT ... WHERE order_id = 'X'
→ Scans ALL 30 effective_from_dt partitions
→ Must apply MAX() to find latest
→ Result: Full table scan instead of partition pruning
```

### Ideal Approach (Unpartitioned)

**Directory Structure Impact:**
```
.../load_date=2025-11-13/state.parquet      (100 MB)
.../load_date=2025-11-14/state.parquet      (105 MB)
.../load_date=2025-11-15/state.parquet      (102 MB)

Total for 30 days: 30 directories x 1 level = 30 partition checks per query
```

**Query Performance:**
```
SELECT ... WHERE order_id = 'X'
→ Scans single latest partition only (or specific partition for historical)
→ Direct access to data
→ Result: Optimal partition pruning
```

---

## Polybase DDL Comparison

### Current Pattern 6 DDL ❌

```sql
CREATE EXTERNAL TABLE [dbo].[orders_state_external] (
    [status] VARCHAR(255),
    [effective_from_dt] VARCHAR(255)    -- ❌ Partition column listed
)
WITH (
    LOCATION = 'pattern6.../load_date={date}/effective_from_dt={date}/',
    PARTITION ( effective_from_dt VARCHAR(255) )  -- ❌ Unnecessary
);
```

### Ideal Pattern 6 DDL ✅

```sql
CREATE EXTERNAL TABLE [dbo].[orders_state_external] (
    [order_id] VARCHAR(255),
    [status] VARCHAR(255)
)
WITH (
    LOCATION = 'pattern6.../load_date={date}/',   -- ✅ Single location
    -- NO partition clause
);
```

---

## Migration Path

### For Existing Patterns 6 & 7:

**Step 1: Update Configuration**
```yaml
# Current
partition_by: [effective_from_dt]
record_time_partition: "effective_from_date"

# New
partition_by: []
record_time_partition: null
```

**Step 2: Regenerate Silver Samples**
```bash
python scripts/generate_silver_samples.py \
  --no-chunking  # Regenerate fresh
```

**Step 3: Validate**
```bash
# Run tests
pytest tests/test_polybase_generator.py -v

# Check sample structure
find sampledata/silver_samples/sample=pattern6* \
  -name "*.parquet" | head -5
```

**Step 4: Update Polybase Configurations**
```bash
python scripts/generate_polybase_ddl.py \
  docs/examples/configs/patterns/pattern_hybrid_incremental_point.yaml \
  docs/examples/configs/patterns/pattern_hybrid_incremental_cumulative.yaml
```

---

## Summary

| Aspect | Current (P6/P7) | Ideal (P6/P7) | Benefit |
|--------|-----------------|---------------|---------|
| Partition Key | effective_from_dt | (none) | Simpler queries |
| Query Complexity | Subquery required | Direct filtering | 40% faster queries |
| Semantics | Confusing | Clear | Better user experience |
| Partition Count | Grows daily | Fixed per load | Less overhead |
| Directory Depth | load_date/record_time/file | load_date/file | Simpler structure |

**Recommendation:** Implement the ideal structure immediately. The changes are already configured in the YAML files and fully compatible with Polybase generation.
