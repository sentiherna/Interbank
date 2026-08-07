"""PK-based deduplication with warning logging (T056).

``deduplicate_by_pk`` retains the *first* occurrence of each primary-key
combination and returns both the cleaned DataFrame and the duplicate count.
Duplicates are never silently dropped: the count is always returned to the
caller so it can be recorded in the quality report.
"""

from __future__ import annotations

import logging

import pandas as pd

_LOG = logging.getLogger(__name__)


def deduplicate_by_pk(
    df: pd.DataFrame,
    pk_columns: list[str] | tuple[str, ...],
    source_name: str,
) -> tuple[pd.DataFrame, int]:
    """Remove duplicate rows by primary-key and return the cleaned DataFrame.

    Args:
        df: Input DataFrame (not modified in-place).
        pk_columns: Column(s) that form the primary key.
        source_name: Source label used in the warning message.

    Returns:
        ``(deduped_df, n_duplicates)`` where *n_duplicates* is the number of
        dropped rows (0 if the DataFrame was already clean).
    """
    pk = list(pk_columns)
    before = len(df)
    deduped = df.drop_duplicates(subset=pk, keep="first").reset_index(drop=True)
    n_dupes = before - len(deduped)

    if n_dupes:
        _LOG.warning(
            "Duplicates detected and removed: source=%s pk=%s count=%d",
            source_name,
            pk,
            n_dupes,
        )

    return deduped, n_dupes
