"""Generate Silver artifacts for every Bronze sample partition."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
BRONZE_SAMPLE_ROOT = REPO_ROOT / "sampledata" / "bronze_samples"
# Silver artifacts now land under sampledata/silver_samples for easy reuse
SILVER_SAMPLE_ROOT = REPO_ROOT / "sampledata" / "silver_samples"
CONFIGS_DIR = REPO_ROOT / "docs" / "examples" / "configs" / "patterns"

SILVER_MODELS = [
    "scd_type_1",
    "scd_type_2",
    "incremental_merge",
    "full_merge_dedupe",
    "periodic_snapshot",
]
PATTERN_CONFIG = {
    "pattern1_full_events": "pattern_full.yaml",
    "pattern2_cdc_events": "pattern_cdc.yaml",
    "pattern3_scd_state": "pattern_current_history.yaml",
    "pattern4_hybrid_cdc_point": "pattern_hybrid_cdc_point.yaml",
    "pattern5_hybrid_cdc_cumulative": "pattern_hybrid_cdc_cumulative.yaml",
    "pattern6_hybrid_incremental_point": "pattern_hybrid_incremental_point.yaml",
    "pattern7_hybrid_incremental_cumulative": "pattern_hybrid_incremental_cumulative.yaml",
}


# Ensure project root on sys.path when executed as standalone script
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _find_brone_partitions() -> Iterable[Dict[str, object]]:
    seen: set[str] = set()
    # Accept any partition directory containing at least one CSV even if metadata file absent
    for dir_path in BRONZE_SAMPLE_ROOT.rglob("dt=*"):
        if not dir_path.is_dir():
            continue
        csv_files = sorted(dir_path.rglob("*.csv"))
        if not csv_files:
            continue
        rel_parts = dir_path.relative_to(BRONZE_SAMPLE_ROOT).parts
        pattern_part = next((p for p in rel_parts if p.startswith("pattern=")), None)
        dt_part = next((p for p in rel_parts if p.startswith("dt=")), None)
        if not pattern_part or not dt_part:
            continue
        pattern = pattern_part.split("=", 1)[1]
        run_date = dt_part.split("=", 1)[1]
        suffix_parts = []
        for part in rel_parts:
            if part in (pattern_part, dt_part):
                continue
            if part.startswith("system=") or part.startswith("table="):
                continue
            suffix_parts.append(part.replace("=", "-"))
        chunk_dir = csv_files[0].parent
        extra_parts = chunk_dir.relative_to(dir_path).parts
        for part in extra_parts:
            suffix_parts.append(part.replace("=", "-"))
        suffix = "_".join(suffix_parts)
        label = f"{pattern}_{run_date}"
        if suffix:
            label = f"{label}_{suffix}"
        key = f"{pattern}|{run_date}|{chunk_dir}"
        if key in seen:
            continue
        seen.add(key)
        sample = {
            "pattern": pattern,
            "run_date": run_date,
            "label": label,
            "dir": chunk_dir,
            "file": csv_files[0],
        }
        yield sample


def _silver_label_from_partition(partition: Dict[str, object]) -> str:
    label_parts = [partition["pattern"], partition["run_date"]]
    dir_name = partition["dir"].name
    dt_label = f"dt={partition['run_date']}"
    if dir_name and dir_name != dt_label:
        label_parts.append(dir_name)
    return "_".join(label_parts)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Silver samples derived from the Bronze fixtures"
    )
    parser.add_argument(
        "--formats",
        choices=["parquet", "csv", "both"],
        default="both",
        help="Which Silver artifact formats to write",
    )
    return parser.parse_args()


def _run_cli(cmd: list[str]) -> None:
    subprocess.run([sys.executable, *cmd], check=True, cwd=REPO_ROOT)


def _generate_for_partition(
    partition: Dict[str, object], enable_parquet: bool, enable_csv: bool
) -> None:
    pattern = partition["pattern"]
    config_name = PATTERN_CONFIG.get(pattern)
    if not config_name:
        raise ValueError(f"No config mapping for pattern '{pattern}'")
    template = CONFIGS_DIR / config_name
    if not template.exists():
        raise FileNotFoundError(f"Pattern config '{template}' not found")
    silver_label = _silver_label_from_partition(partition)
    for silver_model in SILVER_MODELS:
        silver_base = SILVER_SAMPLE_ROOT / silver_label / silver_model
        silver_base.mkdir(parents=True, exist_ok=True)
        cmd = [
            "silver_extract.py",
            "--config",
            str(template),
            "--bronze-path",
            str(partition["dir"]),
            "--date",
            partition["run_date"],
            "--silver-model",
            silver_model,
            "--silver-base",
            str(silver_base),
        ]
        if enable_parquet:
            cmd.append("--write-parquet")
        else:
            cmd.append("--no-write-parquet")
        if enable_csv:
            cmd.append("--write-csv")
        else:
            cmd.append("--no-write-csv")
        _run_cli(cmd)


def _synthesize_sample_readmes(root_dir: Path) -> None:
    for label_dir in root_dir.iterdir():
        if not label_dir.is_dir():
            continue
        for model_dir in label_dir.iterdir():
            if not model_dir.is_dir():
                continue
            readme_path = model_dir / "README.md"
            model_name = model_dir.name.replace("_", " ")
            content = f"""# Silver samples ({model_name})

Derived from Bronze partition `{label_dir.name}` using Silver model `{model_dir.name}`.
"""
            readme_path.write_text(content, encoding="utf-8")


def main() -> None:
    args = parse_args()
    enable_parquet = args.formats in {"parquet", "both"}
    enable_csv = args.formats in {"csv", "both"}

    partitions = list(_find_brone_partitions())
    if not partitions:
        raise RuntimeError("No Bronze partitions found; generate Bronze samples first.")

    if SILVER_SAMPLE_ROOT.exists():
        shutil.rmtree(SILVER_SAMPLE_ROOT)
    SILVER_SAMPLE_ROOT.mkdir(parents=True, exist_ok=True)
    for partition in partitions:
        _generate_for_partition(partition, enable_parquet, enable_csv)

    _synthesize_sample_readmes(SILVER_SAMPLE_ROOT)
    print(f"Silver samples materialized under {SILVER_SAMPLE_ROOT}")


if __name__ == "__main__":
    main()
