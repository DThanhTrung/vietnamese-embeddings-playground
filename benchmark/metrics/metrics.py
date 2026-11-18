"""Metrics shared by benchmark tasks."""

from collections.abc import Sequence

import numpy as np
from sklearn.linear_model import LogisticRegression
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


class LogisticReg:
    """Train logistic regression and return dev-set classification accuracy."""

    name = "log_reg"

    def compute(
        self,
        train_vectors: list[list[float]],
        train_labels: list[int],
        dev_vectors: list[list[float]],
        dev_labels: list[int],
    ) -> float:
        train_features = np.asarray(train_vectors, dtype=float)
        train_targets = np.asarray(train_labels)

        dev_features = np.asarray(dev_vectors, dtype=float)
        dev_targets = np.asarray(dev_labels)

        if train_features.ndim != 2 or dev_features.ndim != 2:
            raise ValueError("Vectors must be two-dimensional")
        if train_features.shape[0] != train_targets.size:
            raise ValueError("Training vectors and labels must have the same length")
        if dev_features.shape[0] != dev_targets.size:
            raise ValueError("Dev vectors and labels must have the same length")
        if train_features.shape[1] != dev_features.shape[1]:
            raise ValueError("Training and dev vectors must have the same dimension")
        if train_features.shape[0] == 0 or dev_features.shape[0] == 0:
            raise ValueError("Training and dev sets must not be empty")
        if not np.isfinite(train_features).all() or not np.isfinite(dev_features).all():
            raise ValueError("Vectors must contain only finite values")

        model = LogisticRegression(max_iter=512)
        model.fit(train_features, train_targets)

        class_scores = model.predict_proba(dev_features)
        predicted_labels = model.classes_[np.argmax(class_scores, axis=1)]
        return float(np.mean(predicted_labels == dev_targets))