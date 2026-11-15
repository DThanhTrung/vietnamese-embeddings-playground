from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any

import numpy as np

from ..config import EmbeddingConfig


class EmbeddingModelAdapter(ABC):
    """Contract implemented by each model family."""

    def __init__(self, config: EmbeddingConfig) -> None:
        self.config = config
        self._model: Any = None

    @abstractmethod
    def load(self) -> None:
        """Load model resources into memory."""

    @abstractmethod
    def encode(self, sentences: Sequence[str]) -> np.ndarray:
        """Encode sentences and return one vector per sentence."""

    def prepare_sentences(self, sentences: Sequence[str]) -> list[str]:
        """Prepare text before encoding; override for model-specific tokenization."""
        return list(sentences)

    def ensure_loaded(self) -> None:
        if self._model is None:
            self.load()

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the vector dimension without encoding a user sentence."""
