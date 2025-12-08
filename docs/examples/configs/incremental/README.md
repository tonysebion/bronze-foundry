# Incremental Extraction Examples

This directory contains example configurations for incremental data extraction patterns.

## Overview

Incremental extraction allows you to extract only new or changed data since the last run, using watermarks to track progress.

## Examples

| File | Source Type | Pattern | Description |
|------|-------------|---------|-------------|
| `incremental_api_example.yaml` | API | `incremental_append` | Salesforce API with timestamp watermark |
| `incremental_db_example.yaml` | Database | `incremental_merge` | PostgreSQL with upsert by primary key |
| `incremental_file_example.yaml` | File | `incremental_append` | S3 parquet files with partition watermark |

## Key Concepts

### Watermark Types

- **timestamp**: ISO 8601 timestamps (e.g., `2025-01-15T10:30:00Z`)
- **date**: Date only (e.g., `2025-01-15`)
- **integer**: Sequence numbers (e.g., `1000000`)
- **string**: Lexicographic comparison

### Reference Modes

- **reference**: Always full extraction
- **delta**: Always incremental
- **auto**: Alternate based on `cadence_days`

### Watermark Storage

Watermarks are stored in:
- Local: `.state/{system}_{table}_watermark.json`
- S3: `s3://{bucket}/{prefix}/_watermarks/{system}_{table}_watermark.json`

## Usage

```bash
# Run API extraction
python bronze_extract.py \
    --config docs/examples/configs/incremental/incremental_api_example.yaml \
    --date 2025-01-15

# Run database extraction
python bronze_extract.py \
    --config docs/examples/configs/incremental/incremental_db_example.yaml \
    --date 2025-01-15

# Run file extraction
python bronze_extract.py \
    --config docs/examples/configs/incremental/incremental_file_example.yaml \
    --date 2025-01-15

# Dry run to preview without extracting
python bronze_extract.py \
    --config docs/examples/configs/incremental/incremental_db_example.yaml \
    --date 2025-01-15 \
    --dry-run
```

## Prerequisites

Set required environment variables before running:

```bash
# For API example
export SALESFORCE_INSTANCE_URL=https://your-instance.salesforce.com
export SALESFORCE_TOKEN_URL=https://login.salesforce.com/services/oauth2/token
export SALESFORCE_CLIENT_ID=your_client_id
export SALESFORCE_CLIENT_SECRET=your_client_secret

# For DB example
export POSTGRES_CONNECTION_STRING=postgresql://user:pass@host:5432/db

# For S3 examples
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-1
```

## Related Documentation

- [Incremental Extraction Guide](../../guides/incremental_extraction.md)
- [Load Patterns Guide](../../guides/load_patterns.md)
- [Error Handling Guide](../../guides/error_handling.md)
