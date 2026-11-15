from collections.abc import Iterable

import numpy as np

from .adapters import EmbeddingModelAdapter
from .config import EmbeddingConfig
from .factory import EmbeddingModelFactory


class EmbeddingService:
    """Public API for loading a model and embedding a list of sentences."""

    def __init__(
        self,
        config: EmbeddingConfig,
        adapter: EmbeddingModelAdapter | None = None,
    ) -> None:
        self.config = config
        self.adapter = adapter or EmbeddingModelFactory.create(config)

    def load(self) -> "EmbeddingService":
        self.adapter.load()
        return self

    def embed(self, sentences: Iterable[str]) -> np.ndarray:
        sentence_list = list(sentences)
        if any(not isinstance(sentence, str) for sentence in sentence_list):
            raise TypeError("sentences must contain only strings")
        return self.adapter.encode(sentence_list)

    @property
    def dimension(self) -> int:
        return self.adapter.dimension
