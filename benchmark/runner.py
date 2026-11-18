"""Generic benchmark runner and result model."""

from dataclasses import dataclass

from module.embedding import EmbeddingService

from .core import Benchmark
from .core import STSBenchmark
from .core import ViHSDBenchmark


@dataclass(frozen=True)
class BenchmarkResult:
    """Serializable result for one model and one benchmark."""

    model_name: str
    benchmark_name: str
    task_name: str
    metric_name: str
    score: float


class BenchmarkRunner:
    """Connect an embedding service to a supported benchmark task."""

    def run(
        self,
        service: EmbeddingService,
        benchmark: Benchmark,
    ) -> BenchmarkResult:
        score = benchmark.evaluate(service)
        return BenchmarkResult(
            model_name=service.config.model_name,
            benchmark_name=benchmark.config.name,
            task_name=benchmark.task_name,
            metric_name=benchmark.metric.name,
            score=score,
        )

    def run_sts(
        self,
        service: EmbeddingService,
        benchmark: STSBenchmark,
    ) -> BenchmarkResult:
        return self.run(service, benchmark)

    def run_vihsd(
        self,
        service: EmbeddingService,
        benchmark: ViHSDBenchmark,
    ) -> BenchmarkResult:
        return self.run(service, benchmark)