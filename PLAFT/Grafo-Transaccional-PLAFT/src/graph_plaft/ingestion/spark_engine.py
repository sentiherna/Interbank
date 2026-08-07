"""SparkEngine — PySpark / S3 DataEngine implementation (T046).

PySpark is an *optional* dependency (``pip install -e '.[spark]'``).
This module is safely importable without PySpark installed; the
``IngestionError`` is raised only when ``SparkEngine`` is *instantiated*.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any, cast

import pandas as pd

from graph_plaft.ingestion.data_engine import DataEngine
from graph_plaft.observability.errors import IngestionError

# Feature-detect PySpark without importing it at module level.
_PYSPARK_AVAILABLE: bool = importlib.util.find_spec("pyspark") is not None


class SparkEngine(DataEngine):
    """DataEngine backed by PySpark for reading from / writing to S3.

    Args:
        spark: Active ``pyspark.sql.SparkSession``.  Typed as ``Any`` to
               avoid a hard import in environments that lack PySpark.
    """

    def __init__(self, spark: Any) -> None:
        if not _PYSPARK_AVAILABLE:
            raise IngestionError(
                "PySpark is not available. "
                "Install the 'spark' extra: pip install -e '.[spark]'"
            )
        self._spark: Any = spark

    def read_parquet(self, path: str | Path) -> pd.DataFrame:
        sdf = self._spark.read.parquet(str(path))
        return cast(pd.DataFrame, sdf.toPandas())

    def read_csv(self, path: str | Path, **kwargs: Any) -> pd.DataFrame:
        sdf = self._spark.read.csv(
            str(path),
            header=kwargs.get("header", True),
            inferSchema=kwargs.get("inferSchema", True),
        )
        return cast(pd.DataFrame, sdf.toPandas())

    def write_parquet(self, df: pd.DataFrame, path: str | Path) -> None:
        sdf = self._spark.createDataFrame(df)
        sdf.write.mode("overwrite").parquet(str(path))

    def exists(self, path: str | Path) -> bool:
        try:
            jvm = self._spark._jvm
            hadoop_path = jvm.org.apache.hadoop.fs.Path(str(path))
            conf = self._spark._jsc.hadoopConfiguration()
            fs = jvm.org.apache.hadoop.fs.FileSystem.get(hadoop_path.toUri(), conf)
            return bool(fs.exists(hadoop_path))
        except Exception:  # noqa: BLE001
            return False
