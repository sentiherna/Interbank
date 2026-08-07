"""Abstract DataEngine interface for dataset I/O (ADR-006, T044).

Concrete implementations:
- ``PandasEngine``: local filesystem, development and tests.
- ``SparkEngine``: Amazon S3 via PySpark, production on SageMaker.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import pandas as pd


class DataEngine(ABC):
    """Abstraction layer for reading and writing datasets.

    All pipeline components receive a ``DataEngine`` instance and call these
    methods, remaining agnostic of whether the data lives locally or on S3.
    """

    @abstractmethod
    def read_parquet(self, path: str | Path) -> pd.DataFrame:
        """Read a Parquet file and return a pandas DataFrame."""

    @abstractmethod
    def read_csv(self, path: str | Path, **kwargs: Any) -> pd.DataFrame:
        """Read a delimited text file and return a pandas DataFrame."""

    @abstractmethod
    def write_parquet(self, df: pd.DataFrame, path: str | Path) -> None:
        """Persist a pandas DataFrame as a Parquet file."""

    @abstractmethod
    def exists(self, path: str | Path) -> bool:
        """Return True if *path* exists in the underlying storage."""
