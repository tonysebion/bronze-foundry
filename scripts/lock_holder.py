import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _get_file_lock():
    from core.storage.locks import file_lock

    return file_lock


def main() -> None:
    silver_partition = Path(sys.argv[1])
    name = sys.argv[2] if len(sys.argv) > 2 else "holder"
    file_lock = _get_file_lock()
    with file_lock(silver_partition, timeout=10):
        print(f"{name} acquired lock")
        time.sleep(5)
        print(f"{name} releasing lock")


if __name__ == "__main__":
    main()
