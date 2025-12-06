from core.infrastructure.config.dataset import DatasetConfig, dataset_to_runtime_config


def _base_dataset_dict(reference_mode=None):
    bronze_options = {}
    if reference_mode is not None:
        bronze_options["reference_mode"] = reference_mode
    return {
        "system": "payments",
        "entity": "transactions",
        "bronze": {
            "source_type": "file",
            "path_pattern": "./sampledata/source.csv",
            "options": bronze_options,
        },
        "silver": {
            "entity_kind": "event",
            "natural_keys": ["tx_id"],
            "event_ts_column": "processed_at",
            "attributes": ["tx_id", "amount"],
            "partition_by": [],
        },
    }


def test_dataset_runtime_config_merges_reference_mode():
    reference_config = {"role": "reference", "cadence_days": 7}
    dataset_dict = _base_dataset_dict(reference_config)
    dataset = DatasetConfig.from_dict(dataset_dict)

    runtime = dataset_to_runtime_config(dataset)
    assert runtime["source"]["run"]["reference_mode"] == reference_config


def test_dataset_runtime_config_omits_reference_mode_when_unset():
    dataset_dict = _base_dataset_dict()
    dataset = DatasetConfig.from_dict(dataset_dict)

    runtime = dataset_to_runtime_config(dataset)
    assert "reference_mode" not in runtime["source"]["run"]
