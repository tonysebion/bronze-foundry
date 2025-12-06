# Main Config Examples

These are the primary example configurations referenced in the documentation. They provide balanced examples that work out-of-the-box with the sample data and demonstrate typical use cases.

## Quick Start: Minimal vs Full Examples

**New to medallion-foundry?** Start with the minimal examples in `../minimal/`:
- `minimal_api_example.yaml` - Simplest API config (7 lines)
- `minimal_db_example.yaml` - Simplest database config (7 lines)
- `minimal_file_example.yaml` - Simplest file config (7 lines)

These examples are Bronze-only, easy to understand, and great for learning.

**Ready for production?** Use the full examples here in `../examples/`:

## Files

- `api_example.yaml` - REST API extraction example with Bronze and Silver
- `db_example.yaml` - Database extraction example with Bronze and Silver
- `file_example.yaml` - File extraction example (used in quickstart)
- `custom_example.yaml` - Custom extractor example
- `s3_example.yaml` - Cloud storage (S3) example

## Purpose

These configs serve as:
- Reference implementations for advanced scenarios
- Working demonstrations with sample data
- Templates for production pipelines
- Full-featured examples with Silver curated datasets

## Usage

These configs include both `bronze:` and `silver:` sections for complete medallion workflows. They work with the bundled sample data and can be run immediately for testing.

