"""PandasEngine — local-filesystem DataEngine implementation (T045).

Reads and writes Parquet / CSV files using pandas + pyarrow.
Intended for local development and all test suites.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from graph_plaft.ingestion.data_engine import DataEngine


class PandasEngine(DataEngine):
    """DataEngine backed by the local filesystem via pandas + pyarrow."""

    def read_parquet(self, path: str | Path) -> pd.DataFrame:
        return pd.read_parquet(path)

    def read_csv(self, path: str | Path, **kwargs: Any) -> pd.DataFrame:
        return pd.read_csv(path, **kwargs)  # type: ignore[no-any-return]

    def write_parquet(self, df: pd.DataFrame, path: str | Path) -> None:
        dest = Path(path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(dest, index=False, engine="pyarrow")

    def exists(self, path: str | Path) -> bool:
        return Path(path).exists()
