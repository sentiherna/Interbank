"""Base class and shared constants for all synthetic data generators (T034).

All generators use a seeded numpy RNG to guarantee that two calls with the
same ``seed`` produce bit-identical Parquet files.
"""

from __future__ import annotations

from typing import ClassVar, Final

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Shared temporal constants
# ---------------------------------------------------------------------------

# All records with dates must fall on or before this date (except post-cutoff
# transactions that are deliberately injected to test filtering).
FECHA_CORTE: Final[pd.Timestamp] = pd.Timestamp("2026-06-30")

# Fixed graph/run identifiers used for traceability columns in the node/edge layer.
GRAPH_VERSION: Final[str] = "v-test-00000000"
RUN_ID: Final[str] = "run-synthetic-seed42"

# ---------------------------------------------------------------------------
# Stable entity IDs referenced by multiple generators
# ---------------------------------------------------------------------------

# 10 clients: CLI-001..CLI-006 are "objetivo", CLI-007..CLI-010 are "contraparte"
CLIENT_IDS: Final[list[str]] = [f"CLI-{i:03d}" for i in range(1, 11)]
OBJETIVO_IDS: Final[list[str]] = CLIENT_IDS[:6]
CONTRAPARTE_IDS: Final[list[str]] = CLIENT_IDS[6:]

# Account → primary client mapping (CTA-009 is shared: CLI-007 + CLI-008)
ACCOUNT_TO_CLIENT: Final[dict[str, str]] = {
    "CTA-001": "CLI-001",
    "CTA-002": "CLI-001",
    "CTA-003": "CLI-002",
    "CTA-004": "CLI-003",
    "CTA-005": "CLI-004",
    "CTA-006": "CLI-005",
    "CTA-007": "CLI-006",
    "CTA-008": "CLI-007",
    "CTA-009": "CLI-007",  # shared with CLI-008 (Cotitular)
    "CTA-010": "CLI-009",
    "CTA-011": "CLI-010",
}

# Account IDs sorted for iteration
ALL_ACCOUNT_IDS: Final[list[str]] = sorted(ACCOUNT_TO_CLIENT)


# ---------------------------------------------------------------------------
# Base generator
# ---------------------------------------------------------------------------


class SyntheticDataGenerator:
    """Base class providing a seeded RNG and a standard generate_all() contract.

    Subclasses override ``generate_all()`` and return a mapping of
    ``{dataset_name: pd.DataFrame}``.  Each entry is saved as a Parquet file
    by ``scripts/generate_synthetic.py``.
    """

    SOURCE_NAME: ClassVar[str] = "base"

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        self.rng: np.random.Generator = np.random.default_rng(seed)

    def generate_all(self) -> dict[str, pd.DataFrame]:
        """Return all DataFrames produced by this generator."""
        raise NotImplementedError
