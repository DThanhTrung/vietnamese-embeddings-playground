"""UIT-ViHSD text classification benchmark."""

from dataclasses import dataclass
from typing import Sequence

from module.embedding import EmbeddingService

from .benchmark import Benchmark
from ..loader import DatasetSource
from ..metrics import LogisticReg


@dataclass(frozen=True)
class ViHSDBenchmarkConfig:
	"""Column mapping and name for one UIT-ViHSD evaluation."""

	name: str = "uit-vihsd"
	text_column: str = "free_text"
	label_column: str = "label_id"


class ViHSDBenchmark(Benchmark):
	"""Evaluate sentence latent representations with logistic regression."""

	task_name = "text-classification"

	def __init__(
		self,
		train_source: DatasetSource | None = None,
		dev_source: DatasetSource | None = None,
		test_source: DatasetSource | None = None,
		config: ViHSDBenchmarkConfig | None = None,
		metric: LogisticReg | None = None,
	) -> None:
		super().__init__(
			config or ViHSDBenchmarkConfig(),
			metric or LogisticReg(),
			train_source=train_source,
			dev_source=dev_source,
			test_source=test_source,
		)

	def _evaluate(
		self,
		service: EmbeddingService,
		*args: object,
		**kwargs: object,
	) -> float:
		"""Embed train/dev sentences and return logistic-regression accuracy."""
		if args:
			raise TypeError("ViHSD does not accept positional evaluation options")
		if kwargs:
			unexpected = ", ".join(sorted(kwargs))
			raise TypeError(f"Unexpected evaluation options: {unexpected}")

		train_data = self.load_train()
		dev_data = self.load_dev()

		required_columns = {self.config.text_column, self.config.label_column}
		self._validate_columns(train_data, required_columns, self.config.name, "train")
		self._validate_columns(dev_data, required_columns, self.config.name, "dev")

		train_texts = train_data[self.config.text_column].astype(str).tolist()
		dev_texts = dev_data[self.config.text_column].astype(str).tolist()
		train_vectors = self._embed(service, train_texts)
		dev_vectors = self._embed(service, dev_texts)

		return self.evaluate_vectors(
			train_vectors,
			train_data[self.config.label_column].tolist(),
			dev_vectors,
			dev_data[self.config.label_column].tolist(),
		)

	def evaluate_vectors(
		self,
		train_vectors: Sequence[Sequence[float]],
		train_labels: Sequence[int],
		dev_vectors: Sequence[Sequence[float]],
		dev_labels: Sequence[int],
	) -> float:
		"""Evaluate latent vectors that have already been produced by a model."""

		return self.metric.compute(
			[list(vector) for vector in train_vectors],
			list(train_labels),
			[list(vector) for vector in dev_vectors],
			list(dev_labels),
		)