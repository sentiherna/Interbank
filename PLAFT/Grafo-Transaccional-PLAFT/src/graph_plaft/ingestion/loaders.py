"""Dataset loader with source registration and checksum tracking (T047).

``load_dataset`` is the single entry-point for every pipeline component that
needs raw data.  It resolves the physical path from the project config,
delegates I/O to the provided ``DataEngine``, and returns both the DataFrame
and immutable ``DatasetMetadata`` for audit traceability.
"""

from __future__ import annotations

import hashlib
import io
import logging
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from graph_plaft.config.settings import Settings
from graph_plaft.ingestion.data_engine import DataEngine
from graph_plaft.observability.errors import IngestionError

_LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class DatasetMetadata:
    """Immutable record of a loaded dataset for audit purposes."""

    source_name: str
    path: str
    row_count: int
    checksum: str   # SHA-256 of the serialised DataFrame bytes
    execution_id: str


def load_dataset(
    source_name: str,
    engine: DataEngine,
    config: Settings,
    execution_id: str,
) -> tuple[pd.DataFrame, DatasetMetadata]:
    """Load a dataset from storage and return it with tracking metadata.

    The physical path is resolved from ``config.storage.base_path`` and the
    configured ``format`` (``parquet`` or ``csv``).

    Args:
        source_name: Logical name of the source (e.g. ``"transferencias"``).
        engine: ``DataEngine`` instance to perform the actual I/O.
        config: Project settings that determine the storage path and format.
        execution_id: Run identifier for correlation.

    Returns:
        ``(DataFrame, DatasetMetadata)`` tuple.

    Raises:
        IngestionError: If the source file is not found or cannot be read.
    """
    path = _resolve_path(source_name, config)
    if not engine.exists(path):
        raise IngestionError(
            f"Dataset '{source_name}' not found at '{path}'. "
            "Generate synthetic data first or verify config.storage.base_path."
        )

    try:
        fmt = config.storage.format.lower()
        if fmt == "csv":
            df = engine.read_csv(path)
        else:
            df = engine.read_parquet(path)
    except Exception as exc:
        raise IngestionError(
            f"Failed to read dataset '{source_name}' from '{path}': {exc}"
        ) from exc

    checksum = _df_checksum(df)
    meta = DatasetMetadata(
        source_name=source_name,
        path=str(path),
        row_count=len(df),
        checksum=checksum,
        execution_id=execution_id,
    )
    _LOG.info(
        "Loaded dataset: source=%s rows=%d checksum=%.8s",
        source_name,
        len(df),
        checksum,
    )
    return df, meta


def _resolve_path(source_name: str, config: Settings) -> str:
    """Build the physical path for *source_name* from the storage config."""
    base = config.storage.base_path.rstrip("/")
    ext = "csv" if config.storage.format.lower() == "csv" else "parquet"
    return f"{base}/{source_name}.{ext}"


def _df_checksum(df: pd.DataFrame) -> str:
    """Compute a SHA-256 checksum of *df* by serialising it to Parquet bytes."""
    buf = io.BytesIO()
    df.to_parquet(buf, index=False, engine="pyarrow")
    return hashlib.sha256(buf.getvalue()).hexdigest()


def resolve_synthetic_path(source_name: str, synthetic_dir: Path) -> Path:
    """Return the path of a synthetic Parquet file for use in tests."""
    return synthetic_dir / f"{source_name}.parquet"
