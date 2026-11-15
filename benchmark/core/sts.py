"""Semantic Textual Similarity benchmark implementation."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from module.embedding import EmbeddingService

from .dataset import DatasetSource
from .metrics import SpearmanMetric


@dataclass(frozen=True)
class STSBenchmarkConfig:
    """Column mapping and name for one STS dataset."""

    name: str
    text_a_column: str
    text_b_column: str
    score_column: str


class STSBenchmark:
    """Run cosine-similarity based STS evaluation on a dataset source."""

    task_name = "sts"

    def __init__(
        self,
        source: DatasetSource,
        config: STSBenchmarkConfig,
        metric: SpearmanMetric | None = None,
    ) -> None:
        self.source = source
        self.config = config
        self.metric = metric or SpearmanMetric()

    def _get_train_subset(
        self
    ) -> pd.DataFrame :
        return self.source.load().head(4500)


    def _get_val_subset(
        self
    ) -> pd.DataFrame :
        return self.source.load().head(5000).tail(500)


    def _get_test_subset(
        self
    ) -> pd.DataFrame :
        return self.source.load().tail(5000)


    def evaluate(
        self, 
        service: EmbeddingService,
        subset: str = 'val'
    ) -> float:
        if 'train' == subset :
            data = self._get_train_subset()
        elif 'val' == subset :
            data = self._get_val_subset()
        else :
            data = self._get_test_subset()

        self._validate_columns(data)

        sentences_a = data[self.config.text_a_column].astype(str).tolist()
        sentences_b = data[self.config.text_b_column].astype(str).tolist()
        gold_scores = data[self.config.score_column].astype(float).to_numpy()

        embeddings_a = service.embed(sentences_a)
        embeddings_b = service.embed(sentences_b)
        predicted_scores = self._cosine_similarity(embeddings_a, embeddings_b)
        return self.metric.compute(predicted_scores, gold_scores)

    def _validate_columns(self, data: pd.DataFrame) -> None:
        required = {
            self.config.text_a_column,
            self.config.text_b_column,
            self.config.score_column,
        }
        missing = sorted(required.difference(data.columns))
        if missing:
            raise ValueError(
                f"Benchmark '{self.config.name}' is missing columns: {', '.join(missing)}"
            )
        if data.empty:
            raise ValueError(f"Benchmark '{self.config.name}' contains no examples")

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