"""Unit tests for business-level validation rules (T058).

Each rule is exercised with a minimal valid DataFrame (should produce 0 issues)
and a deliberately invalid one (should produce the expected issue + severity).
"""

from __future__ import annotations

import pandas as pd
import pytest

from graph_plaft.validation.contracts import ValidationIssue
from graph_plaft.validation.rules import (
    ValidationContext,
    _monto_positivo_ejecutada,
    _pk_unique,
    _required_not_null,
    _temporal_not_after_cutoff,
    get_rules,
)

CUTOFF = pd.Timestamp("2026-06-30")
CTX = ValidationContext(
    source_name="test_source",
    execution_id="exec-test-001",
    date_cutoff=CUTOFF,
)


# ---------------------------------------------------------------------------
# _required_not_null
# ---------------------------------------------------------------------------


class TestRequiredNotNull:
    def test_no_issues_when_column_has_no_nulls(self) -> None:
        df = pd.DataFrame({"cliente_id": ["C01", "C02"]})
        rule = _required_not_null("cliente_id")
        issues = rule(df, CTX)
        assert issues == []

    def test_critical_issue_when_column_is_null(self) -> None:
        df = pd.DataFrame({"cliente_id": [None, "C02"]})
        rule = _required_not_null("cliente_id")
        issues = rule(df, CTX)
        assert len(issues) == 1
        assert issues[0].severity == "CRITICAL"
        assert issues[0].affected_records == 1

    def test_missing_column_is_silently_skipped(self) -> None:
        df = pd.DataFrame({"other": ["x"]})
        rule = _required_not_null("cliente_id")
        issues = rule(df, CTX)
        assert issues == []

    def test_custom_severity_is_respected(self) -> None:
        df = pd.DataFrame({"col": [None]})
        rule = _required_not_null("col", severity="WARNING")
        issues = rule(df, CTX)
        assert issues[0].severity == "WARNING"


# ---------------------------------------------------------------------------
# _pk_unique
# ---------------------------------------------------------------------------


class TestPkUnique:
    def test_no_issues_when_pk_is_unique(self) -> None:
        df = pd.DataFrame({"id": ["A", "B", "C"]})
        rule = _pk_unique("id")
        assert rule(df, CTX) == []

    def test_critical_when_pk_has_duplicates(self) -> None:
        df = pd.DataFrame({"id": ["A", "A", "B"]})
        rule = _pk_unique("id")
        issues = rule(df, CTX)
        assert len(issues) == 1
        assert issues[0].severity == "CRITICAL"
        assert issues[0].affected_records == 1

    def test_composite_pk_uniqueness(self) -> None:
        df = pd.DataFrame({
            "a": ["X", "X", "X"],
            "b": ["1", "1", "2"],
        })
        rule = _pk_unique("a", "b")
        issues = rule(df, CTX)
        assert len(issues) == 1
        assert issues[0].affected_records == 1

    def test_partial_pk_columns_present_skips_rule(self) -> None:
        df = pd.DataFrame({"a": ["X", "X"]})
        rule = _pk_unique("a", "b")  # "b" missing
        assert rule(df, CTX) == []


# ---------------------------------------------------------------------------
# _temporal_not_after_cutoff
# ---------------------------------------------------------------------------


class TestTemporalNotAfterCutoff:
    def test_no_issues_when_all_before_cutoff(self) -> None:
        df = pd.DataFrame({"fecha": [pd.Timestamp("2026-01-01"), pd.Timestamp("2026-06-29")]})
        rule = _temporal_not_after_cutoff("fecha")
        assert rule(df, CTX) == []

    def test_critical_when_date_exceeds_cutoff(self) -> None:
        df = pd.DataFrame({"fecha": [pd.Timestamp("2026-07-01")]})
        rule = _temporal_not_after_cutoff("fecha")
        issues = rule(df, CTX)
        assert len(issues) == 1
        assert issues[0].severity == "CRITICAL"
        assert issues[0].affected_records == 1

    def test_cutoff_date_itself_is_accepted(self) -> None:
        df = pd.DataFrame({"fecha": [pd.Timestamp("2026-06-30")]})
        rule = _temporal_not_after_cutoff("fecha")
        assert rule(df, CTX) == []

    def test_null_date_is_not_flagged(self) -> None:
        df = pd.DataFrame({"fecha": [None, pd.Timestamp("2026-06-01")]})
        rule = _temporal_not_after_cutoff("fecha")
        assert rule(df, CTX) == []

    def test_no_cutoff_in_context_skips_rule(self) -> None:
        ctx_no_cutoff = ValidationContext(
            source_name="x", execution_id="e", date_cutoff=None
        )
        df = pd.DataFrame({"fecha": [pd.Timestamp("2099-01-01")]})
        rule = _temporal_not_after_cutoff("fecha")
        assert rule(df, ctx_no_cutoff) == []

    def test_warning_severity_when_specified(self) -> None:
        df = pd.DataFrame({"fecha": [pd.Timestamp("2026-07-15")]})
        rule = _temporal_not_after_cutoff("fecha", severity="WARNING")
        issues = rule(df, CTX)
        assert issues[0].severity == "WARNING"


# ---------------------------------------------------------------------------
# _monto_positivo_ejecutada
# ---------------------------------------------------------------------------


class TestMontoPositivoEjecutada:
    def _make(self, estado: str, monto: float) -> pd.DataFrame:
        return pd.DataFrame({"estado": [estado], "monto": [monto]})

    def test_no_issues_for_positive_ejecutada(self) -> None:
        rule = _monto_positivo_ejecutada()
        assert rule(self._make("EJECUTADA", 1000.0), CTX) == []

    def test_warning_for_zero_monto_ejecutada(self) -> None:
        rule = _monto_positivo_ejecutada()
        issues = rule(self._make("EJECUTADA", 0.0), CTX)
        assert len(issues) == 1
        assert issues[0].severity == "WARNING"

    def test_no_issue_for_zero_monto_anulada(self) -> None:
        rule = _monto_positivo_ejecutada()
        assert rule(self._make("ANULADA", 0.0), CTX) == []

    def test_no_issue_for_zero_monto_revertida(self) -> None:
        rule = _monto_positivo_ejecutada()
        assert rule(self._make("REVERTIDA", -500.0), CTX) == []

    def test_skips_when_monto_column_absent(self) -> None:
        df = pd.DataFrame({"estado": ["EJECUTADA"]})
        rule = _monto_positivo_ejecutada()
        assert rule(df, CTX) == []


# ---------------------------------------------------------------------------
# get_rules — source registry
# ---------------------------------------------------------------------------


class TestGetRules:
    @pytest.mark.parametrize(
        "source",
        [
            "clientes",
            "cuentas",
            "titularidades",
            "productos",
            "transferencias",
            "alertas_plaft",
            "ros",
            "pep",
            "casos_investigados",
            "catalogo_documental",
            "lista_objetivo",
            "permisos_analistas",
        ],
    )
    def test_all_sources_have_at_least_one_rule(self, source: str) -> None:
        assert len(get_rules(source)) >= 1

    def test_unknown_source_returns_empty_list(self) -> None:
        assert get_rules("nonexistent_source") == []

    def test_transferencias_has_monto_rule(self) -> None:
        rules = get_rules("transferencias")
        # Run all rules on a row that triggers the monto warning
        df = pd.DataFrame({
            "id_transaccion": ["TX-1"],
            "cuenta_origen": ["CTA-1"],
            "cuenta_destino": ["CTA-2"],
            "fecha_hora": [pd.Timestamp("2026-01-01")],
            "monto": [0.0],
            "estado": ["EJECUTADA"],
        })
        all_issues: list[ValidationIssue] = []
        for rule in rules:
            all_issues.extend(rule(df, CTX))
        severities = {i.severity for i in all_issues}
        assert "WARNING" in severities  # monto rule fires
