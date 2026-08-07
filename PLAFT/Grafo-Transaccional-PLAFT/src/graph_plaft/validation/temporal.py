"""Temporal cutoff filter for DataFrames (T055).

``apply_date_cutoff`` removes rows whose *date_col* falls strictly after the
given ``date_cutoff``.  Records on the cutoff date itself are **kept**.
Rows with null dates are also kept (missing date ≠ future date).
"""

from __future__ import annotations

import logging

import pandas as pd

_LOG = logging.getLogger(__name__)


def apply_date_cutoff(
    df: pd.DataFrame,
    date_col: str,
    date_cutoff: pd.Timestamp,
) -> tuple[pd.DataFrame, int]:
    """Filter *df* to rows where *date_col* ≤ *date_cutoff*.

    Args:
        df: Source DataFrame (not modified in-place).
        date_col: Name of the date or timestamp column to evaluate.
        date_cutoff: Upper boundary (inclusive).  Rows after this date
                     are dropped.

    Returns:
        ``(filtered_df, n_rejected)`` where *n_rejected* is the count of
        dropped rows.
    """
    if date_col not in df.columns:
        return df, 0

    dates = pd.to_datetime(df[date_col], errors="coerce", utc=False)

    # Normalise timezone: strip tz so we can compare with a naive Timestamp.
    if dates.dt.tz is not None:
        dates = dates.dt.tz_localize(None)

    cutoff = pd.Timestamp(date_cutoff)
    if cutoff.tzinfo is not None:
        cutoff = cutoff.tz_localize(None)

    # Keep rows that are on or before the cutoff, plus rows with null dates.
    mask = (dates <= cutoff) | dates.isna()
    n_rejected = int((~mask).sum())

    if n_rejected:
        _LOG.warning(
            "Temporal cutoff: %d rows rejected (col='%s', cutoff=%s)",
            n_rejected,
            date_col,
            date_cutoff.date(),
        )

    return df[mask].reset_index(drop=True), n_rejected
