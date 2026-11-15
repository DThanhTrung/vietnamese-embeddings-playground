"""Metrics shared by benchmark tasks."""

from collections.abc import Sequence

import numpy as np
from scipy.stats import spearmanr


class SpearmanMetric:
    """Compute Spearman rank correlation for predicted and gold scores."""

    name = "spearman"

    def compute(
        self,
        predicted_scores: Sequence[float],
        gold_scores: Sequence[float],
    ) -> float:
        predicted = np.asarray(predicted_scores, dtype=float)
        gold = np.asarray(gold_scores, dtype=float)

        if predicted.shape != gold.shape:
            raise ValueError("Predicted and gold scores must have the same shape")

        if predicted.ndim != 1:
            raise ValueError("Scores must be one-dimensional")

        if predicted.size < 2:
            raise ValueError("At least two examples are required")

        if not np.isfinite(predicted).all() or not np.isfinite(gold).all():
            raise ValueError("Scores must contain only finite values")

        result = spearmanr(predicted, gold)
        if not np.isfinite(result.statistic):
            raise ValueError("Spearman correlation is undefined for these scores")
        return float(result.statistic)