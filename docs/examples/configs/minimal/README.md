# Minimal Configuration Examples

These minimal examples are the simplest possible Bronze-only configs to help you get started quickly.

## What's Included

- `minimal_api_example.yaml` - REST API extraction (7 config lines)
- `minimal_db_example.yaml` - Database extraction (7 config lines)  
- `minimal_file_example.yaml` - CSV/file extraction (7 config lines)

## When to Use These

- **First time learning the framework** – Start here to understand the core concepts
- **Prototyping quickly** – Get data moving before adding advanced features
- **Troubleshooting config syntax** – Minimal examples make it easier to debug

## Next Steps

Once you have these working:
1. Enable `silver:` section to create curated datasets
2. Add partitioning with `intraday_partitions` or `partition_columns`
3. Add error handling and quality rules
4. Migrate to cloud storage (S3/Azure)

See `../examples/` for **full-featured examples** with Silver, partitioning, and advanced options.
