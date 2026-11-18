import json
from pathlib import Path
from typing import Any

import yaml

from module.embedding import EmbeddingConfig, EmbeddingService

from .core import (
    ViHSDBenchmark,
    ViHSDBenchmarkConfig,
    STSBenchmark,
    STSBenchmarkConfig
)

from .loader import (
    HuggingFaceDatasetSource,
    HuggingFaceDatasetConfig,
    SubsetDatasetSource 
)

from .core import Benchmark

from .runner import BenchmarkRunner

class BenchmarkPipeline :
    CONFIG_PATH = {
        'sts': Path(__file__).resolve().parent.parent / "configs" / "sickr_sts_vn.yaml",
        'vihsd': Path(__file__).resolve().parent.parent / "configs" / "vihsd.yaml"
    }

    def __init__(
        self,
        benchmark_name: str
    ):
        self.config_path = self.CONFIG_PATH[benchmark_name]
        self.config = None

        with Path(self.config_path).open(encoding="utf-8") as config_file:
            self.config = yaml.safe_load(config_file)

        self._check_config()

        self.benchmark_name = benchmark_name


    def _check_config(self) -> dict[str, Any]:
        if not isinstance(self.config, dict):
            raise ValueError("Benchmark configuration must contain a YAML mapping")

        for section in ("dataset", "benchmark", "model"):
            if not isinstance(self.config.get(section), dict):
                raise ValueError(f"Configuration section '{section}' must be a mapping")

        return True


    def build_benchmark(self) -> Benchmark :
        raise NotImplementedError


    def build_service(self) -> EmbeddingService:
        """Build and load the configured embedding model."""
        return EmbeddingService(EmbeddingConfig(**self.config["model"])).load()


    def run_pipeline(self) -> None:
        service = self.build_service()

        benchmark = self.build_benchmark()

        result = BenchmarkRunner().run_sts(service, benchmark)
        print(json.dumps(result.__dict__, ensure_ascii=False, indent=2))



class STSBenchmarkPipeline(BenchmarkPipeline) :
    def build_benchmark(self) -> Benchmark :
        """Build the local source and STS task from YAML sections."""

        dataset_config = dict(self.config["dataset"])

        source = HuggingFaceDatasetSource(
            config=HuggingFaceDatasetConfig(
                dataset_name=dataset_config["name"],
                split=dataset_config["train_split"],
            )
        )

        return STSBenchmark(
            train_source=SubsetDatasetSource(source, start=0, end=4500),
            dev_source=SubsetDatasetSource(source, start=4500, end=5000),
            test_source=SubsetDatasetSource(source, start=5000),
            config=STSBenchmarkConfig(self.config["benchmark"]),
        )



class VIHSDBenchmarkPipeline(BenchmarkPipeline) :
    def build_benchmark(self) -> Benchmark :
        dataset_config = self.config["dataset"]
        train_source = HuggingFaceDatasetSource(
            HuggingFaceDatasetConfig(
                dataset_name=dataset_config["name"],
                config_name=dataset_config.get("config_name", "default"),
                split=dataset_config["train_split"],
            )
        )

        dev_source = HuggingFaceDatasetSource(
            HuggingFaceDatasetConfig(
                dataset_name=dataset_config["name"],
                config_name=dataset_config.get("config_name", "default"),
                split=dataset_config["dev_split"],
            )
        )

        return ViHSDBenchmark(
            train_source=train_source,
            dev_source=dev_source,
            test_source=None,
            config=ViHSDBenchmarkConfig(self.config["benchmark"]),
        )