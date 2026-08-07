"""Unit tests: critical validation errors halt the pipeline (T061).

``QualityChecker.check_and_raise()`` must raise ``CriticalValidationError``
whenever the ``ValidationReport`` contains at least one CRITICAL issue.
``check()`` must never raise (callers inspect the report themselves).
"""

from __future__ import annotations

import pandas as pd
import pytest

from graph_plaft.observability.errors import CriticalValidationError
from graph_plaft.validation.quality import QualityChecker
from graph_plaft.validation.rules import ValidationContext

CUTOFF = pd.Timestamp("2026-06-30")
CTX = ValidationContext(
    source_name="transferencias",
    execution_id="exec-test-001",
    date_cutoff=CUTOFF,
)
CHECKER = QualityChecker()


# ---------------------------------------------------------------------------
# check() — never raises
# ---------------------------------------------------------------------------


class TestCheckNeverRaises:
    def test_missing_required_column_returns_report_not_exception(self) -> None:
        df = pd.DataFrame({"wrong_col": ["v1"]})
        report = CHECKER.check(df, "transferencias", CTX)
        assert report.has_critical_errors()

    def test_duplicate_pk_returns_report_not_exception(self) -> None:
        df = pd.DataFrame({
            "cliente_id": ["C01", "C01"],
            "tipo_persona": ["NATURAL", "NATURAL"],
        })
        report = CHECKER.check(df, "clientes", CTX)
        assert report.has_critical_errors()

    def test_valid_clientes_row_has_no_critical_errors(self) -> None:
        df = pd.DataFrame({
            "cliente_id": ["C01"],
            "tipo_persona": ["NATURAL"],
            "estado_cliente": ["ACTIVO"],
            "fecha_alta": [pd.Timestamp("2020-01-01")],
            "segmento": ["RETAIL"],
        })
        report = CHECKER.check(df, "clientes", CTX)
        assert not report.has_critical_errors()


# ---------------------------------------------------------------------------
# check_and_raise() — raises on CRITICAL
# ---------------------------------------------------------------------------


class TestCheckAndRaise:
    def test_raises_when_pk_null(self) -> None:
        df = pd.DataFrame({"cliente_id": [None], "tipo_persona": ["NATURAL"]})
        with pytest.raises(CriticalValidationError) as exc_info:
            CHECKER.check_and_raise(df, "clientes", CTX)
        assert exc_info.value.dataset == "clientes"

    def test_raises_when_required_column_absent(self) -> None:
        # transferencias missing id_transaccion
        df = pd.DataFrame({
            "cuenta_origen": ["CTA-1"],
            "cuenta_destino": ["CTA-2"],
            "fecha_hora": [pd.Timestamp("2026-01-01")],
            "monto": [1000.0],
            "moneda": ["PEN"],
            "estado": ["EJECUTADA"],
        })
        with pytest.raises(CriticalValidationError):
            CHECKER.check_and_raise(df, "transferencias", CTX)

    def test_raises_with_correct_metadata(self) -> None:
        df = pd.DataFrame({"cliente_id": ["C01", "C01"]})
        with pytest.raises(CriticalValidationError) as exc_info:
            CHECKER.check_and_raise(df, "clientes", CTX)
        err = exc_info.value
        assert err.dataset == "clientes"
        assert err.affected_records >= 1

    def test_no_raise_when_only_warnings(self) -> None:
        # Valid transferencias with monto=0 on EJECUTADA → WARNING only
        df = pd.DataFrame({
            "id_transaccion": ["TX-1"],
            "cuenta_origen": ["CTA-1"],
            "cuenta_destino": ["CTA-2"],
            "fecha_hora": [pd.Timestamp("2026-01-01")],
            "monto": [0.0],
            "moneda": ["PEN"],
            "estado": ["EJECUTADA"],
            "canal": ["APP"],
            "periodo": ["2026-01"],
            "cliente_origen": ["CLI-1"],
            "cliente_destino": ["CLI-2"],
        })
        report = CHECKER.check_and_raise(df, "transferencias", CTX)
        # Should not raise; should have a WARNING for monto
        assert not report.has_critical_errors()
        assert len(report.warnings()) >= 1

    def test_critical_error_message_is_descriptive(self) -> None:
        df = pd.DataFrame({"other": ["x"]})
        with pytest.raises(CriticalValidationError) as exc_info:
            CHECKER.check_and_raise(df, "clientes", CTX)
        msg = str(exc_info.value)
        assert "clientes" in msg


# ---------------------------------------------------------------------------
# validate_all() — stops at first critical source
# ---------------------------------------------------------------------------


class TestValidateAll:
    def test_raises_on_first_bad_source(self) -> None:
        datasets = {
            "clientes": pd.DataFrame({"cliente_id": [None]}),   # CRITICAL
            "cuentas": pd.DataFrame({"cuenta_id": ["CTA-1"]}),  # OK
        }
        ctx = ValidationContext(source_name="", execution_id="e")
        with pytest.raises(CriticalValidationError):
            CHECKER.validate_all(datasets, ctx)

    def test_returns_all_reports_when_no_critical_errors(self) -> None:
        datasets = {
            "clientes": pd.DataFrame({
                "cliente_id": ["C01"],
                "tipo_persona": ["NATURAL"],
                "estado_cliente": ["ACTIVO"],
                "fecha_alta": [pd.Timestamp("2020-01-01")],
                "segmento": ["RETAIL"],
            }),
        }
        ctx = ValidationContext(source_name="", execution_id="e")
        reports = CHECKER.validate_all(datasets, ctx)
        assert "clientes" in reports
        assert not reports["clientes"].has_critical_errors()
