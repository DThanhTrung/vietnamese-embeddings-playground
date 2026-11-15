from collections.abc import Callable

from .adapters import (
    EmbeddingModelAdapter,
    SentenceTransformersAdapter,
    TransformersAdapter,
)
from .config import EmbeddingConfig


class EmbeddingModelFactory:
    """Create adapters by a stable name instead of scattering model checks."""

    _adapters: dict[str, Callable[[EmbeddingConfig], EmbeddingModelAdapter]] = {
        "sentence-transformers": SentenceTransformersAdapter,
        "transformers": TransformersAdapter,
    }

    @classmethod
    def create(cls, config: EmbeddingConfig) -> EmbeddingModelAdapter:
        try:
            adapter_class = cls._adapters[config.adapter_name.lower()]
        except KeyError as error:
            supported = ", ".join(sorted(cls._adapters))
            raise ValueError(
                f"Unknown adapter '{config.adapter_name}'. Supported: {supported}"
            ) from error
        return adapter_class(config)

    @classmethod
    def register(
        cls,
        name: str,
        adapter_class: Callable[[EmbeddingConfig], EmbeddingModelAdapter],
    ) -> None:
        normalized_name = name.strip().lower()
        if not normalized_name:
            raise ValueError("Adapter name must not be empty")
        cls._adapters[normalized_name] = adapter_class
