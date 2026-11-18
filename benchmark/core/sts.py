"""Semantic Textual Similarity benchmark implementation."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from module.embedding import EmbeddingService

from .benchmark import Benchmark
from ..loader.dataset import DatasetSource
from ..metrics.metrics import SpearmanMetric


@dataclass(frozen=True)
class STSBenchmarkConfig:
    """Column mapping and name for one STS dataset."""

    name: str = 'uit-vihsd'
    text_a_column: str = 'sentence1'
    text_b_column: str = 'sentence2'
    score_column: str = 'score'


class STSBenchmark(Benchmark):
    """Run cosine-similarity based STS evaluation on a dataset source."""

    task_name = "sts"

    def __init__(
        self,
        train_source: DatasetSource | None = None,
        dev_source: DatasetSource | None = None,
        test_source: DatasetSource | None = None,
        config: STSBenchmarkConfig | None = None,
        metric: SpearmanMetric | None = None,
    ) -> None:
        super().__init__(
            config or STSBenchmarkConfig(),
            metric or SpearmanMetric(),
            train_source=train_source,
            dev_source=dev_source,
            test_source=test_source,
        )

    def _evaluate(
        self, 
        service: EmbeddingService,
        subset: str = 'val',
        *args: object,
        **kwargs: object,
    ) -> float:
        if args:
            raise TypeError("STS accepts only one positional evaluation option: subset")
        if kwargs:
            unexpected = ", ".join(sorted(kwargs))
            raise TypeError(f"Unexpected evaluation options: {unexpected}")

        if 'train' == subset :
            data = self.load_train()
        elif 'val' == subset :
            data = self.load_val()
        else :
            data = self.load_test()

        self._validate_columns(
            data,
            {
                self.config.text_a_column,
                self.config.text_b_column,
                self.config.score_column,
            },
            self.config.name,
        )

        sentences_a = data[self.config.text_a_column].astype(str).tolist()
        sentences_b = data[self.config.text_b_column].astype(str).tolist()
        gold_scores = data[self.config.score_column].astype(float).to_numpy()

        embeddings_a = self._embed(service, sentences_a)
        embeddings_b = self._embed(service, sentences_b)
        predicted_scores = self._cosine_similarity(embeddings_a, embeddings_b)
        return self.metric.compute(predicted_scores, gold_scores)

    @staticmethod
    def _cosine_similarity(
        embeddings_a: np.ndarray,
        embeddings_b: np.ndarray,
    ) -> np.ndarray:
        if embeddings_a.shape != embeddings_b.shape:
            raise ValueError("Both sentence columns must produce matching embeddings")
        norms_a = np.linalg.norm(embeddings_a, axis=1)
        norms_b = np.linalg.norm(embeddings_b, axis=1)
        denominator = np.maximum(norms_a * norms_b, 1e-12)
        return np.sum(embeddings_a * embeddings_b, axis=1) / denominator