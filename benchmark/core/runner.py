"""Generic benchmark runner and result model."""

from dataclasses import dataclass

from module.embedding import EmbeddingService

from .sts import STSBenchmark


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

    def run_sts(
        self,
        service: EmbeddingService,
        benchmark: STSBenchmark,
    ) -> BenchmarkResult:
        score = benchmark.evaluate(service)
        return BenchmarkResult(
            model_name=service.config.model_name,
            benchmark_name=benchmark.config.name,
            task_name=benchmark.task_name,
            metric_name=benchmark.metric.name,
            score=score,
        )