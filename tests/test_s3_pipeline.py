"""Deprecated wrapper — please use `scripts/check_s3_pipeline.py` instead.

To run the S3 pipeline check interactively, invoke the new script:
```
python scripts/check_s3_pipeline.py
```
"""

if __name__ == "__main__":
    # Run the new CLI script instead (it performs the same checks).
    from scripts.check_s3_pipeline import main
    import sys

    sys.exit(main())
