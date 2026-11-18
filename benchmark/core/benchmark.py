"""Common abstractions for embedding benchmarks."""

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd

from module.embedding import EmbeddingService


class Benchmark(ABC):
    """Base class shared by task-specific embedding benchmarks."""

    task_name: str

    def __init__(
        self,
        config: Any,
        metric: Any,
        train_source: Any | None = None,
        dev_source: Any | None = None,
        test_source: Any | None = None,
    ) -> None:
        self.config = config
        self.metric = metric
        self.train_source = train_source
        self.dev_source = dev_source
        self.test_source = test_source

    def load_train(self) -> pd.DataFrame:
        """Load the training split, or return an empty frame when unavailable."""
        return self.train_source.load() if self.train_source is not None else pd.DataFrame()

    def load_dev(self) -> pd.DataFrame:
        """Load the development/validation split, or return an empty frame when unavailable."""
        return self.dev_source.load() if self.dev_source is not None else pd.DataFrame()

    def load_val(self) -> pd.DataFrame:
        """Alias for the development/validation split."""
        return self.load_dev()

    def load_test(self) -> pd.DataFrame:
        """Load the test split, or return an empty frame when unavailable."""
        return self.test_source.load() if self.test_source is not None else pd.DataFrame()

    def evaluate(
        self,
        service: EmbeddingService,
        *args: Any,
        **kwargs: Any,
    ) -> float:
        """Evaluate this benchmark using latent representations from a model."""

        return self._evaluate(service, *args, **kwargs)

    @abstractmethod
    def _evaluate(
        self,
        service: EmbeddingService,
        *args: Any,
        **kwargs: Any,
    ) -> float:
        """Prepare task inputs and delegate scoring to the configured metric."""

    @staticmethod
    def _validate_columns(
        data: pd.DataFrame,
        required_columns: set[str],
        benchmark_name: str,
        split_name: str | None = None,
    ) -> None:
        missing = sorted(required_columns.difference(data.columns))
        context = f"{benchmark_name} {split_name}" if split_name else benchmark_name
        if missing:
            raise ValueError(
                f"Benchmark '{context}' is missing columns: {', '.join(missing)}"
            )
        if data.empty:
            raise ValueError(f"Benchmark '{context}' contains no examples")

    @staticmethod
    def _embed(
        service: EmbeddingService,
        texts: list[str],
    ) -> Any:
        return service.embed(texts)