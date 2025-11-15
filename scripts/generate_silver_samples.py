"""Create Golden Silver assets from the Bronze sample data for documentation/testing."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
BRONZE_SAMPLE_ROOT = REPO_ROOT / "docs" / "examples" / "data" / "bronze_samples"
SILVER_SAMPLE_ROOT = REPO_ROOT / "docs" / "examples" / "data" / "silver_samples"
CONFIGS_DIR = REPO_ROOT / "docs" / "examples" / "configs"

CONFIG_FILES = [
    "file_example.yaml",
    "file_cdc_example.yaml",
    "file_current_history_example.yaml",
]
RUN_DATES = ["2025-11-13", "2025-11-14"]
SILVER_MODELS = [
    "scd_type_1",
    "scd_type_2",
    "incremental_merge",
    "full_merge_dedupe",
    "periodic_snapshot",
]


def _build_sample_path(cfg: dict, run_date: str) -> Path:
    pattern = cfg["source"]["run"].get("load_pattern", "full")
    system = cfg["source"]["system"]
    table = cfg["source"]["table"]
    filename = Path(cfg["source"]["file"]["path"]).name
    return (
        BRONZE_SAMPLE_ROOT
        / pattern
        / f"system={system}"
        / f"table={table}"
        / f"pattern={pattern}"
        / f"dt={run_date}"
        / filename
    )


def _rewrite_config(original: Path, run_date: str, temp_dir: Path) -> Path:
    cfg = yaml.safe_load(original.read_text())
    bronze_path = _build_sample_path(cfg, run_date)
    if not bronze_path.exists():
        raise FileNotFoundError(f"Missing Bronze sample {bronze_path}")

    bronze_out = temp_dir / f"bronze_out_{run_date}"
    bronze_out.mkdir(parents=True, exist_ok=True)
    cfg["source"]["file"]["path"] = str(bronze_path)
    cfg["source"]["run"]["local_output_dir"] = str(bronze_out.resolve())
    target = temp_dir / f"{original.stem}_bronze_{run_date}.yaml"
    target.write_text(yaml.safe_dump(cfg))
    return target


def _rewrite_silver_config(original: Path, run_date: str, temp_dir: Path, silver_model: str) -> Path:
    cfg = yaml.safe_load(original.read_text())
    bronze_path = _build_sample_path(cfg, run_date)
    bronze_out = temp_dir / f"bronze_out_{run_date}"
    bronze_out.mkdir(parents=True, exist_ok=True)
    cfg["source"]["file"]["path"] = str(bronze_path)
    cfg["source"]["run"]["local_output_dir"] = str(bronze_out.resolve())

    pattern = cfg["source"]["run"].get("load_pattern", "full")
    silver_base = (SILVER_SAMPLE_ROOT / pattern / silver_model).resolve()
    silver_base.mkdir(parents=True, exist_ok=True)
    cfg.setdefault("silver", {})
    cfg["silver"]["output_dir"] = str(silver_base)

    target = temp_dir / f"{original.stem}_{silver_model}_{run_date}.yaml"
    target.write_text(yaml.safe_dump(cfg))
    return target


def _run_cli(cmd: list[str]) -> None:
    subprocess.run([sys.executable, *cmd], check=True, cwd=REPO_ROOT)


def main() -> None:
    if SILVER_SAMPLE_ROOT.exists():
        shutil.rmtree(SILVER_SAMPLE_ROOT)
    SILVER_SAMPLE_ROOT.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="silver_samples_gen_") as tmp_dir:
        tmp_dir_path = Path(tmp_dir)
        for config_name in CONFIG_FILES:
            config_path = CONFIGS_DIR / config_name
            for run_date in RUN_DATES:
                bronze_cfg = _rewrite_config(config_path, run_date, tmp_dir_path)
                _run_cli(["bronze_extract.py", "--config", str(bronze_cfg), "--date", run_date])
                for silver_model in SILVER_MODELS:
                    silver_cfg = _rewrite_silver_config(config_path, run_date, tmp_dir_path, silver_model)
                    _run_cli(
                        [
                            "silver_extract.py",
                            "--config",
                            str(silver_cfg),
                            "--date",
                            run_date,
                            "--silver-model",
                            silver_model,
                        ]
                    )

    print(f"Silver samples materialized under {SILVER_SAMPLE_ROOT}")


if __name__ == "__main__":
    main()
