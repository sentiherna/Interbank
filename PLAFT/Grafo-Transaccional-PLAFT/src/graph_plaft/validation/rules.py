"""Business-level validation rules for every source dataset (T049-T053).

Each *rule* is a ``RuleFunction``: a callable that receives a DataFrame and a
``ValidationContext`` and returns zero or more ``ValidationIssue`` objects.
Rules are independent and composable; the ``QualityChecker`` in
``quality.py`` orchestrates them per source.

Rule catalogue
--------------
Schema-level checks (null, type, PK uniqueness, allowed-values) are handled
by ``validate_schema()`` in ``contracts.py``.  The rules here add:

* Temporal cutoff — date column must be ≤ ``date_cutoff``.
* Monto positivo para EJECUTADA — business rule for ``transferencias``.
* Required-field cross-checks not captured by the schema contract.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import pandas as pd

from graph_plaft.validation.contracts import ValidationIssue

# ---------------------------------------------------------------------------
# Context passed to every rule function
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ValidationContext:
    """Execution context for rule evaluation."""

    source_name: str
    execution_id: str
    date_cutoff: pd.Timestamp | None = None


# ---------------------------------------------------------------------------
# Type alias
# ---------------------------------------------------------------------------

RuleFunction = Callable[[pd.DataFrame, ValidationContext], list[ValidationIssue]]


# ---------------------------------------------------------------------------
# Rule factory helpers
# ---------------------------------------------------------------------------


def _required_not_null(*cols: str, severity: str = "CRITICAL") -> RuleFunction:
    """Rule: each named column must have zero null values."""

    def _rule(df: pd.DataFrame, ctx: ValidationContext) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        for col in cols:
            if col not in df.columns:
                continue
            nulls = int(df[col].isna().sum())
            if nulls:
                issues.append(
                    ValidationIssue(
                        rule=f"required_not_null:{col}",
                        column=col,
                        severity=severity,
                        message=(
                            f"[{ctx.source_name}] '{col}' tiene {nulls} "
                            "valores nulos en columna requerida."
                        ),
                        affected_records=nulls,
                    )
                )
        return issues

    return _rule


def _pk_unique(*pk_cols: str) -> RuleFunction:
    """Rule: primary-key combination must be unique across all rows."""

    def _rule(df: pd.DataFrame, ctx: ValidationContext) -> list[ValidationIssue]:
        cols = [c for c in pk_cols if c in df.columns]
        if len(cols) != len(pk_cols):
            return []
        dupes = int(df.duplicated(subset=cols, keep="first").sum())
        if dupes:
            return [
                ValidationIssue(
                    rule=f"pk_unique:{'+'.join(pk_cols)}",
                    column=", ".join(pk_cols),
                    severity="CRITICAL",
                    message=(
                        f"[{ctx.source_name}] Clave primaria {list(pk_cols)} "
                        f"tiene {dupes} registros duplicados."
                    ),
                    affected_records=dupes,
                )
            ]
        return []

    return _rule


def _temporal_not_after_cutoff(
    date_col: str,
    severity: str = "CRITICAL",
) -> RuleFunction:
    """Rule: *date_col* values must be ≤ ``ctx.date_cutoff`` (if set)."""

    def _rule(df: pd.DataFrame, ctx: ValidationContext) -> list[ValidationIssue]:
        if ctx.date_cutoff is None or date_col not in df.columns:
            return []
        dates = pd.to_datetime(df[date_col], errors="coerce", utc=False)
        cutoff = pd.Timestamp(ctx.date_cutoff)
        # Strip timezone from both sides to allow comparison
        if dates.dt.tz is not None:
            dates = dates.dt.tz_localize(None)
        violations = int((dates > cutoff).sum())
        if violations:
            return [
                ValidationIssue(
                    rule=f"temporal_not_after_cutoff:{date_col}",
                    column=date_col,
                    severity=severity,
                    message=(
                        f"[{ctx.source_name}] {violations} registros tienen "
                        f"'{date_col}' posterior a la fecha de corte "
                        f"({ctx.date_cutoff.date()})."
                    ),
                    affected_records=violations,
                )
            ]
        return []

    return _rule


def _monto_positivo_ejecutada() -> RuleFunction:
    """Rule (WARNING): monto must be > 0 for EJECUTADA transactions."""

    def _rule(df: pd.DataFrame, ctx: ValidationContext) -> list[ValidationIssue]:
        if "monto" not in df.columns or "estado" not in df.columns:
            return []
        ejecutadas = df[df["estado"] == "EJECUTADA"]
        invalid = int((ejecutadas["monto"] <= 0).sum())
        if invalid:
            return [
                ValidationIssue(
                    rule="monto_positivo_ejecutada",
                    column="monto",
                    severity="WARNING",
                    message=(
                        f"[{ctx.source_name}] {invalid} transacciones "
                        "EJECUTADA con monto ≤ 0."
                    ),
                    affected_records=invalid,
                )
            ]
        return []

    return _rule


# ---------------------------------------------------------------------------
# Source-level rule sets  (T049-T053)
# ---------------------------------------------------------------------------

_CLIENTES: list[RuleFunction] = [
    _required_not_null("cliente_id"),
    _pk_unique("cliente_id"),
]

_CUENTAS: list[RuleFunction] = [
    _required_not_null("cuenta_id"),
    _pk_unique("cuenta_id"),
]

_TITULARIDADES: list[RuleFunction] = [
    _required_not_null("cliente_id", "cuenta_id"),
    _pk_unique("cliente_id", "cuenta_id", "tipo_titularidad"),
]

_PRODUCTOS: list[RuleFunction] = [
    _required_not_null("producto_id", "cliente_id", "tipo_producto"),
    _pk_unique("producto_id"),
]

_TRANSFERENCIAS: list[RuleFunction] = [
    _required_not_null("id_transaccion", "cuenta_origen", "cuenta_destino"),
    _pk_unique("id_transaccion"),
    _temporal_not_after_cutoff("fecha_hora"),
    _monto_positivo_ejecutada(),
]

_ALERTAS_PLAFT: list[RuleFunction] = [
    _required_not_null("alerta_id", "cliente_id", "tipo_alerta", "fecha_alerta"),
    _pk_unique("alerta_id"),
    _temporal_not_after_cutoff("fecha_alerta"),
]

_ROS: list[RuleFunction] = [
    _required_not_null("ros_id", "cliente_id", "fecha_reporte"),
    _pk_unique("ros_id"),
    _temporal_not_after_cutoff("fecha_reporte"),
]

_PEP: list[RuleFunction] = [
    _required_not_null("pep_id", "cliente_id", "vigente"),
    _pk_unique("pep_id"),
]

_CASOS_INVESTIGADOS: list[RuleFunction] = [
    _required_not_null("caso_id", "cliente_id", "fecha_apertura", "estado"),
    _pk_unique("caso_id"),
    _temporal_not_after_cutoff("fecha_apertura"),
]

_CATALOGO_DOCUMENTAL: list[RuleFunction] = [
    _required_not_null("documento_id", "cliente_id", "tipo_documental", "sistema_origen"),
    _pk_unique("documento_id"),
    # fecha_incorporacion is nullable; post-cutoff is a WARNING here
    _temporal_not_after_cutoff("fecha_incorporacion", severity="WARNING"),
]

_LISTA_OBJETIVO: list[RuleFunction] = [
    _required_not_null("cliente_id", "version_lista", "fecha_inclusion"),
    _pk_unique("cliente_id", "version_lista"),
    _temporal_not_after_cutoff("fecha_inclusion"),
]

_PERMISOS_ANALISTAS: list[RuleFunction] = [
    _required_not_null("usuario_id", "cliente_id", "nivel_acceso", "fecha_inicio"),
    _pk_unique("usuario_id", "cliente_id", "nivel_acceso"),
]

# ---------------------------------------------------------------------------
# Public registry
# ---------------------------------------------------------------------------

SOURCE_RULES: dict[str, list[RuleFunction]] = {
    "clientes": _CLIENTES,
    "cuentas": _CUENTAS,
    "titularidades": _TITULARIDADES,
    "productos": _PRODUCTOS,
    "transferencias": _TRANSFERENCIAS,
    "alertas_plaft": _ALERTAS_PLAFT,
    "ros": _ROS,
    "pep": _PEP,
    "casos_investigados": _CASOS_INVESTIGADOS,
    "catalogo_documental": _CATALOGO_DOCUMENTAL,
    "lista_objetivo": _LISTA_OBJETIVO,
    "permisos_analistas": _PERMISOS_ANALISTAS,
}


def get_rules(source_name: str) -> list[RuleFunction]:
    """Return the business rules for *source_name* (empty list if unknown)."""
    return SOURCE_RULES.get(source_name, [])


# Expose ValidationContext for import convenience
__all__ = [
    "ValidationContext",
    "RuleFunction",
    "SOURCE_RULES",
    "get_rules",
]


def _make_issue(
    rule: str,
    column: str | None,
    severity: str,
    message: str,
    affected: int,
    samples: list[Any] | None = None,
) -> ValidationIssue:
    """Helper: construct a ValidationIssue without repeating keyword names."""
    return ValidationIssue(
        rule=rule,
        column=column,
        severity=severity,
        message=message,
        affected_records=affected,
        sample_values=samples or [],
    )
