from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class EmbeddingConfig:
    """Runtime settings shared by all embedding model adapters."""

    model_name: str
    adapter_name: str = "sentence-transformers"
    device: str | None = None
    batch_size: int = 16
    normalize_embeddings: bool = True
    show_progress_bar: bool = False
    encode_kwargs: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.model_name.strip():
            raise ValueError("model_name must not be empty")
        if self.batch_size < 1:
            raise ValueError("batch_size must be greater than zero")
