from collections.abc import Callable, Sequence

from ..config import EmbeddingConfig
from .sentence_transformers import SentenceTransformersAdapter


class PreprocessedSentenceTransformersAdapter(SentenceTransformersAdapter):
    """Apply model-specific text preprocessing before SentenceTransformers."""

    def __init__(
        self,
        config: EmbeddingConfig,
        preprocess: Callable[[str], str],
    ) -> None:
        super().__init__(config)
        self._preprocess = preprocess

    def prepare_sentences(self, sentences: Sequence[str]) -> list[str]:
        return [self._preprocess(sentence) for sentence in sentences]
