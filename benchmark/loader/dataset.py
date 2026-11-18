"""Dataset sources used by benchmarks.

The source is deliberately independent from a benchmark task. A future
Hugging Face source can implement the same ``load`` method without changing
the STS implementation.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from datasets import load_dataset

class DatasetSource(ABC):
    """Load a dataset from one particular kind of source."""

    @abstractmethod
    def load(self) -> pd.DataFrame:
        """Return the dataset as a tabular dataframe."""


@dataclass(frozen=True)
class LocalFileDatasetConfig:
    """Configuration for a local CSV, TSV, or JSON Lines dataset."""

    path: str
    file_format: str = "tsv"
    delimiter: str = "\t"
    encoding: str = "utf-8"
    split_column: str | None = None
    split_value: str | None = None

    def __post_init__(self) -> None:
        if not self.path.strip():
            raise ValueError("Dataset path must not be empty")
        if self.file_format.lower() not in {"csv", "tsv", "jsonl"}:
            raise ValueError("file_format must be one of: csv, tsv, jsonl")
        if self.split_column is None and self.split_value is not None:
            raise ValueError("split_column is required when split_value is set")


class LocalFileDatasetSource(DatasetSource):
    """Load a tabular dataset that is already present on the local machine."""

    def __init__(self, config: LocalFileDatasetConfig) -> None:
        self.config = config

    def load(self) -> pd.DataFrame:
        path = Path(self.config.path)
        if not path.is_file():
            raise FileNotFoundError(f"Dataset file does not exist: {path}")

        file_format = self.config.file_format.lower()
        if file_format == "jsonl":
            data = pd.read_json(path, lines=True, encoding=self.config.encoding)
        else:
            delimiter = "," if file_format == "csv" else self.config.delimiter
            data = pd.read_csv(
                path,
                sep=delimiter,
                encoding=self.config.encoding,
            )

        if self.config.split_column is not None:
            if self.config.split_column not in data.columns:
                raise ValueError(
                    f"Missing split column '{self.config.split_column}' in {path}"
                )
            data = data[data[self.config.split_column] == self.config.split_value]

        return data.reset_index(drop=True)


@dataclass(frozen=True)
class HuggingFaceDatasetConfig:
    """Configuration for one split of a Hugging Face dataset."""

    dataset_name: str
    split: str
    config_name: str = "default"

    def __post_init__(self) -> None:
        if not self.dataset_name.strip():
            raise ValueError("dataset_name must not be empty")
        if not self.split.strip():
            raise ValueError("split must not be empty")


class HuggingFaceDatasetSource(DatasetSource):
    """Load a dataset split from the Hugging Face Hub as a dataframe."""

    def __init__(self, config: HuggingFaceDatasetConfig) -> None:
        self.config = config
        self._cache: pd.DataFrame | None = None

    def load(self) -> pd.DataFrame:
        if self._cache is None:
            dataset = load_dataset(
                self.config.dataset_name,
                name=self.config.config_name,
                split=self.config.split,
            )
            self._cache = dataset.to_pandas().dropna().reset_index(drop=True)

        return self._cache.copy()


class SubsetDatasetSource(DatasetSource):
    """Load a contiguous row subset from another dataset source."""

    def __init__(
        self,
        source: DatasetSource,
        start: int = 0,
        end: int | None = None,
    ) -> None:
        if start < 0:
            raise ValueError("Subset start index must be non-negative")
        if end is not None and end < start:
            raise ValueError("Subset end index must be greater than or equal to start")
        self.source = source
        self.start = start
        self.end = end
        self._cache: pd.DataFrame | None = None

    def load(self) -> pd.DataFrame:
        if self._cache is None:
            data = self.source.load()
            self._cache = data.iloc[self.start:self.end].reset_index(drop=True)
        return self._cache.copy()


def build_local_source(config: dict[str, Any]) -> LocalFileDatasetSource:
    """Build a local source from a configuration mapping."""

    return LocalFileDatasetSource(LocalFileDatasetConfig(**config))