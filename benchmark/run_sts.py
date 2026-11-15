"""Entry point for one local-file STS benchmark.

The benchmark configuration is read from ``configs/sick_r_sts.yaml``. Change
``CONFIG_PATH`` below when running another YAML configuration.
"""

import json
from pathlib import Path
from typing import Any

import yaml

from module.embedding import EmbeddingConfig, EmbeddingService

from .core import (
    BenchmarkRunner,
    LocalFileDatasetConfig,
    LocalFileDatasetSource,
    STSBenchmark,
    STSBenchmarkConfig,
)

CONFIG_PATH = Path(__file__).resolve().parent.parent / "configs" / "sick_r_sts.yaml"


def load_config(path: Path) -> dict[str, Any]:
    """Read and validate the top-level YAML configuration."""

    with path.open(encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)

    if not isinstance(config, dict):
        raise ValueError("Benchmark configuration must contain a YAML mapping")

    for section in ("dataset", "benchmark", "model"):
        if not isinstance(config.get(section), dict):
            raise ValueError(f"Configuration section '{section}' must be a mapping")

    return config


def build_benchmark(config: dict[str, Any]) -> STSBenchmark:
    """Build the local source and STS task from YAML sections."""

    dataset_config = dict(config["dataset"])

    dataset_path = Path(dataset_config["path"])
    if not dataset_path.is_absolute() and not dataset_path.is_file():
        repository_root = Path(__file__).resolve().parent.parent
        dataset_config["path"] = str(repository_root / dataset_path)

    source = LocalFileDatasetSource(LocalFileDatasetConfig(**dataset_config))
    return STSBenchmark(
        source=source,
        config=STSBenchmarkConfig(**config["benchmark"]),
    )


def build_service(config: dict[str, Any]) -> EmbeddingService:
    """Build and load the configured embedding model."""

    return EmbeddingService(
        EmbeddingConfig(**config["model"])
    ).load()


def pipeline(
    config_path: Path | str = CONFIG_PATH
) -> None:
    config = load_config(config_path)

    service = build_service(config)

    benchmark = build_benchmark(config)

    result = BenchmarkRunner().run_sts(service, benchmark)
    print(json.dumps(result.__dict__, ensure_ascii=False, indent=2))