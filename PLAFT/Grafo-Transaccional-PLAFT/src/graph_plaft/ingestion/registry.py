"""DatasetRegistry — per-execution dataset provenance tracker (T048).

``DatasetRegistry`` accumulates ``DatasetMetadata`` entries as datasets are
loaded throughout a pipeline run.  It can be serialised to a DataFrame for
inclusion in the ``RunManifest``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

import pandas as pd

from graph_plaft.ingestion.loaders import DatasetMetadata


@dataclass
class DatasetEntry:
    """A single dataset provenance record."""

    source_name: str
    path: str
    row_count: int
    checksum: str
    execution_id: str
    registered_at: str   # ISO-8601 UTC timestamp


class DatasetRegistry:
    """Accumulates dataset provenance records for one pipeline execution."""

    def __init__(self) -> None:
        self._entries: dict[str, DatasetEntry] = {}

    def register(self, metadata: DatasetMetadata) -> None:
        """Record *metadata* under its ``source_name``.

        Registering the same source twice overwrites the previous entry
        (last-write-wins; this happens when a source is reloaded).
        """
        entry = DatasetEntry(
            source_name=metadata.source_name,
            path=metadata.path,
            row_count=metadata.row_count,
            checksum=metadata.checksum,
            execution_id=metadata.execution_id,
            registered_at=datetime.now(UTC).isoformat(),
        )
        self._entries[metadata.source_name] = entry

    def get(self, source_name: str) -> DatasetEntry | None:
        """Return the entry for *source_name*, or ``None`` if not registered."""
        return self._entries.get(source_name)

    def all_sources(self) -> list[str]:
        """Return the list of registered source names in insertion order."""
        return list(self._entries)

    def to_dataframe(self) -> pd.DataFrame:
        """Serialise all entries to a pandas DataFrame."""
        rows: list[dict[str, Any]] = [asdict(e) for e in self._entries.values()]
        return pd.DataFrame(rows) if rows else pd.DataFrame(
            columns=[
                "source_name",
                "path",
                "row_count",
                "checksum",
                "execution_id",
                "registered_at",
            ]
        )

    def to_dict(self) -> dict[str, dict[str, Any]]:
        """Return a plain-dict representation for JSON serialisation."""
        return {k: asdict(v) for k, v in self._entries.items()}

    def __len__(self) -> int:
        return len(self._entries)
