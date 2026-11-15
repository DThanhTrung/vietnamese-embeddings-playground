from collections.abc import Sequence

import numpy as np
from sentence_transformers import SentenceTransformer

from .base import EmbeddingModelAdapter


class SentenceTransformersAdapter(EmbeddingModelAdapter):
    """Adapter for models supported by sentence-transformers."""

    def load(self) -> None:

        self._model = SentenceTransformer(
            self.config.model_name,
            device=self.config.device,
        )


    @property
    def dimension(self) -> int:
        self.ensure_loaded()
        return int(self._model.get_sentence_embedding_dimension())

    def encode(self, sentences: Sequence[str]) -> np.ndarray:
        self.ensure_loaded()
        if not sentences:
            return np.empty((0, self.dimension), dtype=np.float32)

        prepared_sentences = self.prepare_sentences(sentences)

        encode_kwargs = {
            "batch_size": self.config.batch_size,
            "show_progress_bar": self.config.show_progress_bar,
            "normalize_embeddings": self.config.normalize_embeddings,
            "convert_to_numpy": True,
            **self.config.encode_kwargs,
        }

        vectors = self._model.encode(prepared_sentences, **encode_kwargs)
        return np.asarray(vectors, dtype=np.float32)
