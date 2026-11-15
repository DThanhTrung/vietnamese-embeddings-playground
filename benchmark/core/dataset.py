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


def build_local_source(config: dict[str, Any]) -> LocalFileDatasetSource:
    """Build a local source from a configuration mapping."""

    return LocalFileDatasetSource(LocalFileDatasetConfig(**config))