from collections.abc import Sequence

import numpy as np
import torch

from .base import EmbeddingModelAdapter


class TransformersAdapter(EmbeddingModelAdapter):
    """Adapter for Hugging Face models requiring custom pooling."""

    def load(self) -> None:
        from transformers import AutoModel, AutoTokenizer

        device = self.config.device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._device = torch.device(device)
        self._tokenizer = AutoTokenizer.from_pretrained(self.config.model_name)
        self._model = AutoModel.from_pretrained(self.config.model_name).to(self._device)
        self._model.eval()

    @property
    def dimension(self) -> int:
        self.ensure_loaded()
        return int(self._model.config.hidden_size)

    def encode(self, sentences: Sequence[str]) -> np.ndarray:
        self.ensure_loaded()
        if not sentences:
            return np.empty((0, self.dimension), dtype=np.float32)

        vectors: list[np.ndarray] = []
        with torch.inference_mode():
            for start in range(0, len(sentences), self.config.batch_size):
                batch = list(sentences[start : start + self.config.batch_size])
                tokens = self._tokenizer(
                    batch,
                    padding=True,
                    truncation=True,
                    return_tensors="pt",
                    **self.config.encode_kwargs,
                )
                tokens = {name: value.to(self._device) for name, value in tokens.items()}
                output = self._model(**tokens)
                pooled = self._mean_pool(output.last_hidden_state, tokens["attention_mask"])
                if self.config.normalize_embeddings:
                    pooled = torch.nn.functional.normalize(pooled, p=2, dim=1)
                vectors.append(pooled.cpu().numpy())
        return np.concatenate(vectors, axis=0).astype(np.float32, copy=False)

    @staticmethod
    def _mean_pool(hidden_state: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        mask = attention_mask.unsqueeze(-1).expand(hidden_state.size()).float()
        return (hidden_state * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
