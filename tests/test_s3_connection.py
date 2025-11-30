"""Deprecated wrapper — please use `scripts/check_s3_connection.py` instead.

To run the S3 connection check interactively, invoke the script directly:
```
python scripts/check_s3_connection.py
```
"""

if __name__ == "__main__":
    # Run the new script to avoid pytest collecting this file as test code.
    from scripts.check_s3_connection import main
    import sys

    sys.exit(main())
