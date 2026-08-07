"""Unit tests for the temporal cutoff filter (T059).

``apply_date_cutoff`` must:
- Accept records on or before the cutoff (inclusive boundary).
- Reject records strictly after the cutoff.
- Retain rows with null dates.
- Handle Timestamp and string date columns.
"""

from __future__ import annotations

import pandas as pd

from graph_plaft.validation.temporal import apply_date_cutoff

CUTOFF = pd.Timestamp("2026-06-30")


class TestApplyDateCutoff:
    def test_past_record_accepted(self) -> None:
        df = pd.DataFrame({"fecha": [pd.Timestamp("2026-01-01")]})
        result, rejected = apply_date_cutoff(df, "fecha", CUTOFF)
        assert rejected == 0
        assert len(result) == 1

    def test_record_on_cutoff_accepted(self) -> None:
        df = pd.DataFrame({"fecha": [CUTOFF]})
        result, rejected = apply_date_cutoff(df, "fecha", CUTOFF)
        assert rejected == 0
        assert len(result) == 1

    def test_record_after_cutoff_rejected(self) -> None:
        df = pd.DataFrame({"fecha": [pd.Timestamp("2026-07-01")]})
        result, rejected = apply_date_cutoff(df, "fecha", CUTOFF)
        assert rejected == 1
        assert len(result) == 0

    def test_mixed_records_only_future_removed(self) -> None:
        df = pd.DataFrame({
            "fecha": [
                pd.Timestamp("2026-05-01"),   # kept
                pd.Timestamp("2026-06-30"),   # kept (on cutoff)
                pd.Timestamp("2026-07-15"),   # rejected
            ]
        })
        result, rejected = apply_date_cutoff(df, "fecha", CUTOFF)
        assert rejected == 1
        assert len(result) == 2

    def test_null_dates_are_kept(self) -> None:
        df = pd.DataFrame({"fecha": [None, pd.Timestamp("2026-07-01")]})
        result, rejected = apply_date_cutoff(df, "fecha", CUTOFF)
        assert rejected == 1       # only the post-cutoff row is rejected
        assert len(result) == 1   # the null row survives

    def test_missing_column_returns_df_unchanged(self) -> None:
        df = pd.DataFrame({"other_col": [1, 2, 3]})
        result, rejected = apply_date_cutoff(df, "fecha", CUTOFF)
        assert rejected == 0
        assert len(result) == 3

    def test_string_dates_parsed_correctly(self) -> None:
        df = pd.DataFrame({"fecha": ["2026-06-30", "2026-07-01"]})
        result, rejected = apply_date_cutoff(df, "fecha", CUTOFF)
        assert rejected == 1
        assert len(result) == 1

    def test_all_future_returns_empty_df(self) -> None:
        df = pd.DataFrame({
            "fecha": [pd.Timestamp("2027-01-01"), pd.Timestamp("2028-06-01")]
        })
        result, rejected = apply_date_cutoff(df, "fecha", CUTOFF)
        assert rejected == 2
        assert len(result) == 0

    def test_all_past_returns_full_df(self) -> None:
        df = pd.DataFrame({
            "fecha": [pd.Timestamp("2020-01-01"), pd.Timestamp("2025-12-31")]
        })
        result, rejected = apply_date_cutoff(df, "fecha", CUTOFF)
        assert rejected == 0
        assert len(result) == 2

    def test_output_index_is_reset(self) -> None:
        df = pd.DataFrame({
            "fecha": [pd.Timestamp("2025-01-01"), pd.Timestamp("2027-01-01")]
        })
        result, _ = apply_date_cutoff(df, "fecha", CUTOFF)
        assert list(result.index) == [0]


class TestApplyDateCutoffTransferenciasPattern:
    """Simulate Phase 2 synthetic transfer data (P7 + P8 patterns)."""

    def _make_transfers(self) -> pd.DataFrame:
        return pd.DataFrame({
            "id_transaccion": [f"TX-{i:03d}" for i in range(1, 18)],
            "fecha_hora": [
                pd.Timestamp("2026-03-10"),
                pd.Timestamp("2026-03-12"),
                pd.Timestamp("2026-03-15"),
                pd.Timestamp("2026-03-18"),
                pd.Timestamp("2026-03-20"),
                pd.Timestamp("2026-03-25"),
                pd.Timestamp("2026-04-02"),
                pd.Timestamp("2026-04-05"),
                pd.Timestamp("2026-04-08"),
                pd.Timestamp("2026-05-01"),
                pd.Timestamp("2026-05-03"),
                pd.Timestamp("2026-06-01"),
                pd.Timestamp("2026-06-10"),
                pd.Timestamp("2026-06-20"),
                pd.Timestamp("2026-04-15"),   # ANULADA — still within cutoff
                pd.Timestamp("2026-05-20"),   # REVERTIDA — within cutoff
                pd.Timestamp("2026-07-15"),   # POST-CUTOFF (P8)
            ],
        })

    def test_only_post_cutoff_is_rejected(self) -> None:
        df = self._make_transfers()
        result, rejected = apply_date_cutoff(df, "fecha_hora", CUTOFF)
        assert rejected == 1   # only TX-017 (P8)
        assert len(result) == 16
