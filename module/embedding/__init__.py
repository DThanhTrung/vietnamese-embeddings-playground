"""Object-oriented embedding API."""

from .config import EmbeddingConfig
from .factory import EmbeddingModelFactory
from .service import EmbeddingService

__all__ = [
    "EmbeddingConfig", 
    "EmbeddingModelFactory", 
    "EmbeddingService"
]