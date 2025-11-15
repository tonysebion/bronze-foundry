# Bronze + Silver Guidance

This guide highlights when to run each Bronze extraction pattern and which Silver asset model makes sense for the downstream workload. Bronze and Silver have overlapping requirements (they both care about load patterns, latency, and integrity) but they also optimize for different things, so configure them independently when appropriate.

## Bronze extraction patterns (input)

| Pattern | When to use | Key trade-offs |
| --- | --- | --- |
| `full` | Periodic refreshes (daily/weekly) when the entire dataset is small enough to rewrite, or you need a clean snapshot for archives. | Simple to reason about and easy to validate, but becomes expensive as data grows; downstream Silver and Gold consumers read the latest snapshot. |
| `cdc` | High-volume feeds where only deltas change (inserts/updates/deletes) such as transaction tables. | Bronze stores smaller files, and metadata indicates the change set. Bronze must still preserve ordering and dedupe as needed. |
| `current_history` | SCD Type 2–style histories that split current + historical rows for every business key. | Bronze retains both sides of the business key; Silver can build the current view while keeping the rest of the history. Requires primary keys + order column. |

### Factors to weigh for Bronze config

- **Data volume**: Full snapshots scale linearly—choose CDC when throughput or file counts become unwieldy.
- **Change rate**: If only a few rows change between runs, incremental/CDC drastically reduces storage and processing time.
- **Schema stability**: When columns shift frequently, full snapshots keep Silver simple; CDC/current_history must gracefully handle new columns via Silver schema options.
- **Run latency**: Streaming chunking, parallel workers, and smaller bronze chunks help keep Bronze runtime bounded.
- **Failure tolerance**: Bronze already writes `_checksums.json`; Silver can opt into `require_checksum` to skip promotions when Bronze integrity fails.

## Silver promotion assets (output)

The Silver stage works with the Bronze artifacts and lets you select **five curated models** regardless of the Bronze pattern:

| Silver model | Description | Suggested scenario |
| --- | --- | --- |
| `periodic_snapshot` | Mirror the Bronze snapshot (full dataset). | Use when downstream teams expect a one-to-one dump of the Bronze partition (e.g., nightly refresh trading off duplication for simplicity). Merits small Bronze (full) datasets. |
| `incremental_merge` | Emit the raw CDC/timestamp chunk so merge targets can apply it. | Ideal when Bronze uses CDC or timestamped deltas and downstream needs to apply only the change set (e.g., merge into a central table). |
| `full_merge_dedupe` | Deduplicate using configured PKs/order column; produce a clean snapshot for full-merge processes. | Handy when Silver itself drives `MERGE` statements or analytical joins but you still prefer periodic snapshots. Works with both full and CDC Bronze sources. |
| `scd_type_1` | Keep only the latest row for each business key (SCD Type 1). | When consumers only want the current representation (e.g., query tables) and you can tolerate dropped history. Requires PK+order column. |
| `scd_type_2` | Build both the current view and the historical timeline, annotating an `is_current` flag. | Use when you must audit changes over time (current + history split). Works best behind Bronze `current_history` so the history artifacts already include past/active rows. |

### Silver factors

- **Data size**: Writing full snapshots of large Bronze partitions can be heavy; consider `scd_type_2` or `incremental_merge` to keep downstream materializations tight and partitioned.
- **Change footprint**: For small changes over huge bases (e.g., customer tables), `scd_type_1`/`scd_type_2` with inference via `order_column` prevents reprocessing everything.
- **Consumption latency**: Streaming mode (via `--stream`) and chunked writes keep memory bounded when Silver needs to keep up with very large Bronze partitions.
- **Output formats**: Choose Parquet for analytics; enable CSV when errors must be human-readable or Silver artifacts feed legacy tooling. The new `scripts/generate_silver_samples.py --formats both` helps you exercise both writers.
- **Error handling**: Tune `silver.error_handling` (enabled/max_bad_records/max_bad_percent) when data has nullable keys or occasional corrupt rows to avoid electing total job failure.
- **Partitioning differences**: Bronze typically partitions by `dt`/`pattern`; Silver can add business-level partitions (e.g., `status`, `region`) even when Bronze stays coarse.