"""Validación de DataFrames contra contratos de datos.

La función ``validate_schema`` valida un DataFrame pandas contra un
``SourceContract`` y retorna un ``ValidationReport`` con todos los
errores y advertencias encontrados. No modifica el DataFrame de entrada.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from graph_plaft.validation.schemas import ColumnDtype, SourceContract

# ---------------------------------------------------------------------------
# Modelos de reporte
# ---------------------------------------------------------------------------


@dataclass
class ValidationIssue:
    """Problema de validación encontrado en el DataFrame."""

    rule: str
    column: str | None
    severity: str              # "CRITICAL" | "WARNING"
    message: str
    affected_records: int = 0
    sample_values: list[Any] = field(default_factory=list)

    def is_critical(self) -> bool:
        return self.severity == "CRITICAL"


@dataclass
class ValidationReport:
    """Resultado completo de la validación de un DataFrame."""

    source_name: str
    execution_id: str
    total_rows: int
    issues: list[ValidationIssue] = field(default_factory=list)

    def critical_issues(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.is_critical()]

    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if not i.is_critical()]

    def has_critical_errors(self) -> bool:
        return any(i.is_critical() for i in self.issues)

    def summary(self) -> str:
        n_crit = len(self.critical_issues())
        n_warn = len(self.warnings())
        return (
            f"[{self.source_name}] rows={self.total_rows} "
            f"critical={n_crit} warnings={n_warn}"
        )


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

_DTYPE_PANDAS_MAP: dict[ColumnDtype, list[str]] = {
    ColumnDtype.STRING: ["object", "string"],
    ColumnDtype.INTEGER: ["int32", "int64", "Int32", "Int64"],
    ColumnDtype.FLOAT: ["float32", "float64", "Float32", "Float64"],
    ColumnDtype.BOOLEAN: ["bool", "boolean"],
    ColumnDtype.DATE: ["object", "datetime64[ns]", "datetime64[us]", "date"],
    ColumnDtype.TIMESTAMP: ["object", "datetime64[ns]", "datetime64[us]", "datetime64[ns, UTC]"],
    ColumnDtype.ARRAY_STRING: ["object"],
}


def _dtype_ok(series: pd.Series, expected: ColumnDtype) -> bool:
    """Retorna True si el dtype de la serie es compatible con el esperado."""
    dtype_str = str(series.dtype)
    allowed = _DTYPE_PANDAS_MAP.get(expected, [])
    if any(dtype_str.startswith(a) for a in allowed):
        return True
    # Intentar conversión silenciosa para tipos numéricos
    if expected in (ColumnDtype.INTEGER, ColumnDtype.FLOAT):
        try:
            pd.to_numeric(series.dropna(), errors="raise")
            return True
        except (ValueError, TypeError):
            return False
    return False


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------


def validate_schema(
    df: pd.DataFrame,
    contract: SourceContract,
    source_name: str = "",
    execution_id: str = "",
) -> ValidationReport:
    """Valida un DataFrame pandas contra un contrato de datos.

    La función NO modifica el DataFrame de entrada. Retorna siempre un
    ``ValidationReport``. Si hay errores críticos, el caller debe decidir
    si detener el pipeline llamando a ``report.has_critical_errors()``.

    Validaciones realizadas:
    1. Columnas obligatorias presentes.
    2. Tipos de dato compatibles.
    3. Nulos en columnas no nulables.
    4. Duplicados en columnas clave primaria.
    5. Valores fuera de dominio (allowed_values).

    Args:
        df: DataFrame a validar (no se modifica).
        contract: Contrato de datos a aplicar.
        source_name: Nombre de la fuente (para mensajes de error).
        execution_id: Identificador de la ejecución para correlación.

    Returns:
        ``ValidationReport`` con todos los problemas encontrados.

    Raises:
        CriticalValidationError: Si hay errores críticos de esquema (columnas faltantes).
    """
    name = source_name or contract.source_name
    report = ValidationReport(
        source_name=name,
        execution_id=execution_id,
        total_rows=len(df),
    )

    present_cols = set(df.columns)
    required_cols = {c.name for c in contract.columns if c.required}

    # --- 1. Columnas obligatorias -------------------------------------------
    missing_required = required_cols - present_cols
    if missing_required:
        issue = ValidationIssue(
            rule="required_columns_present",
            column=None,
            severity="CRITICAL",
            message=(
                f"[{name}] Columnas obligatorias faltantes: {sorted(missing_required)}. "
                f"Columnas presentes: {sorted(present_cols)}."
            ),
            affected_records=len(df),
        )
        report.issues.append(issue)
        # Detener validación adicional: sin columnas no podemos continuar
        return report

    # Procesar solo las columnas del contrato que están presentes
    for col_contract in contract.columns:
        col = col_contract.name
        if col not in present_cols:
            # Columna opcional ausente: no es error
            continue

        series = df[col]

        # --- 2. Tipos de dato -----------------------------------------------
        if not _dtype_ok(series, col_contract.dtype):
            report.issues.append(
                ValidationIssue(
                    rule="dtype_compatible",
                    column=col,
                    severity="WARNING",
                    message=(
                        f"[{name}] Columna '{col}' tiene dtype '{series.dtype}', "
                        f"se esperaba compatible con '{col_contract.dtype.value}'."
                    ),
                    affected_records=len(series),
                    sample_values=list(series.head(3)),
                )
            )

        # --- 3. Nulos en columnas no nulables --------------------------------
        if not col_contract.nullable:
            null_count = int(series.isna().sum())
            if null_count > 0:
                severity = "CRITICAL" if col_contract.required else "WARNING"
                report.issues.append(
                    ValidationIssue(
                        rule="not_nullable",
                        column=col,
                        severity=severity,
                        message=(
                            f"[{name}] Columna '{col}' contiene {null_count} valores nulos "
                            "pero está marcada como no nulable."
                        ),
                        affected_records=null_count,
                        sample_values=list(
                            series[series.isna()].index[:3].tolist()
                        ),
                    )
                )

        # --- 5. Dominio permitido -------------------------------------------
        if col_contract.allowed_values is not None:
            non_null = series.dropna()
            invalid = non_null[~non_null.astype(str).isin(col_contract.allowed_values)]
            if len(invalid) > 0:
                report.issues.append(
                    ValidationIssue(
                        rule="allowed_values",
                        column=col,
                        severity="WARNING",
                        message=(
                            f"[{name}] Columna '{col}' contiene {len(invalid)} valores "
                            f"fuera del dominio permitido: "
                            f"{sorted(col_contract.allowed_values)}."
                        ),
                        affected_records=len(invalid),
                        sample_values=list(invalid.unique()[:5]),
                    )
                )

    # --- 4. Duplicados en claves primarias -----------------------------------
    if contract.primary_keys:
        pk_cols = [k for k in contract.primary_keys if k in present_cols]
        if pk_cols and len(pk_cols) == len(contract.primary_keys):
            dup_mask = df.duplicated(subset=pk_cols, keep="first")
            dup_count = int(dup_mask.sum())
            if dup_count > 0:
                report.issues.append(
                    ValidationIssue(
                        rule="primary_key_unique",
                        column=", ".join(pk_cols),
                        severity="CRITICAL",
                        message=(
                            f"[{name}] Clave primaria {pk_cols} contiene "
                            f"{dup_count} registros duplicados."
                        ),
                        affected_records=dup_count,
                        sample_values=list(
                            df[dup_mask][pk_cols].head(3).to_dict("records")
                        ),
                    )
                )

    return report
