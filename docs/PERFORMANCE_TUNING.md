# Performance Tuning Guide

This guide provides recommended settings for optimal Bronze/Silver performance based on data characteristics.

## Silver Streaming Chunk Sizes

**Rule of thumb:** Target 10-50 MB uncompressed per chunk for balanced memory/throughput.

| Bronze Partition Size | Recommended `--streaming-chunk-size` | Notes |
|-----------------------|--------------------------------------|-------|
| < 100 MB              | `0` (batch mode)                     | Entire partition fits in memory; streaming overhead not justified |
| 100 MB - 1 GB         | `10000` rows                         | Good balance for typical record sizes (~1-10 KB/row) |
| 1 GB - 10 GB          | `50000` rows                         | Larger chunks amortize I/O; watch memory usage |
| > 10 GB               | `100000` rows + `--streaming-prefetch 2` | Use prefetch to overlap I/O |

**CSV vs Parquet:**
- CSV chunk size is row-based; Parquet reads entire files (controlled by splitting files in Bronze)
- For large Parquet files, set smaller Bronze `max_rows_per_file` to enable finer-grained streaming

## API Extraction Performance

**Async vs Sync:**
- Enable async (`source.api.async: true`) when:
  - Pagination depth > 10 pages
  - Network latency > 50ms
  - RPS limits allow concurrent requests
- Async prefetch improves page-based pagination by ~30-50% (overlaps next page fetch)

**Rate Limiting:**
- Set `source.api.rate_limit.rps` to 80% of upstream API limit to leave headroom for retries
- Example: If API allows 100 RPS, configure `rps: 80`
- Lower RPS when circuit breaker opens frequently (indicates upstream pressure)

**Retry/Circuit Breaker Tuning:**
- Default retry: 5 attempts, exponential backoff (0.5s → 8s max)
- Circuit breaker: opens after 5 failures, cools down for 30s
- Adjust via `source.run` config:
  ```yaml
  run:
    max_retry_attempts: 3  # fewer retries if API is unstable
    retry_base_delay: 1.0  # longer initial delay for slow APIs
  ```

## Parallelism

**Bronze Extraction:**
- `--parallel-workers N`: Runs N configs concurrently
  - Set to # of CPU cores for CPU-bound transforms
  - Set to 2-4x cores for I/O-bound API/DB extracts (overlaps network waits)

**Silver Streaming Transforms:**
- `--transform-processes N`: Multiprocessing for schema/normalization
  - Only beneficial for large chunks (>50k rows) with complex transforms
  - Adds overhead; benchmark before enabling

## Memory Profiling

Run benchmark to identify optimal chunk size:

```powershell
python -m scripts.benchmark --scenario silver_streaming
```

Expected throughput:
- 1,000 rows/chunk: ~5,000-10,000 records/sec
- 10,000 rows/chunk: ~20,000-50,000 records/sec
- 100,000 rows/chunk: ~50,000-100,000 records/sec (memory permitting)

Monitor with:
```powershell
# Windows Task Manager: Watch "Working Set" for Python process
# Or use memory_profiler:
python -m memory_profiler silver_extract.py --stream --config myconfig.yaml
```

## Storage Backend Optimization

**S3:**
- Enable multipart upload for files > 100 MB (automatic in boto3)
- Use same region as compute to minimize latency

**Azure:**
- Use Blob Storage (not ADLS Gen2) if append operations aren't needed
- Configure `max_concurrency` in SDK for parallel block uploads

**Local:**
- Use SSD for Bronze/Silver partitions when streaming
- Pre-create output directories to avoid mkdir overhead per chunk

## Observability

**Tracing:**
- Enable `BRONZE_TRACING=1` to measure time in API requests, transforms, writes
- Use OTLP collector to visualize span waterfall in Jaeger/Zipkin

**Metrics:**
- Track: API response time (p50/p95), chunk processing rate, circuit breaker state
- Alert on: retry exhaustion, circuit open > 5 min, streaming throughput < baseline

## Quick Wins

1. **Enable async for paginated APIs:** Add `api.async: true`
2. **Set chunk size for large Bronze:** Start with `--streaming-chunk-size 10000`
3. **Rate limit to avoid 429s:** Configure `api.rate_limit.rps` at 80% of API limit
4. **Use resume on failures:** `--resume` to skip already-written chunks
5. **Benchmark first:** Run `scripts/benchmark.py` to establish baselines before tuning
