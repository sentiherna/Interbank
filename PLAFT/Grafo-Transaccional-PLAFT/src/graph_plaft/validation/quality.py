"""QualityChecker — validation orchestrator for every source (T054, T057).

``QualityChecker`` combines:
1. Schema validation via ``validate_schema()`` (contracts.py).
2. Business rules via ``get_rules()`` (rules.py).

It exposes two entry-points:
* ``check()``            — returns the ``ValidationReport`` (never raises).
* ``check_and_raise()``  — raises ``CriticalValidationError`` on any CRITICAL issue.
* ``validate_all()``     — checks every source in a dict; raises on first critical.
"""

from __future__ import annotations

import logging

import pandas as pd

from graph_plaft.observability.errors import CriticalValidationError
from graph_plaft.validation.contracts import ValidationReport, validate_schema
from graph_plaft.validation.rules import ValidationContext, get_rules
from graph_plaft.validation.schemas import get_contract

_LOG = logging.getLogger(__name__)


class QualityChecker:
    """Orchestrates schema and business-rule validation for one DataFrame."""

    def check(
        self,
        df: pd.DataFrame,
        source_name: str,
        context: ValidationContext,
    ) -> ValidationReport:
        """Validate *df* against the registered contract and business rules.

        Always returns a ``ValidationReport``; never raises.
        Callers inspect ``report.has_critical_errors()`` to decide next steps.
        """
        # --- 1. Schema-level validation (type, nulls, PK uniqueness) --------
        try:
            contract = get_contract(source_name)
            report = validate_schema(
                df, contract, source_name, context.execution_id
            )
        except KeyError:
            # No contract registered; create a minimal report and continue.
            _LOG.warning("No contract defined for source '%s'. Skipping schema check.", source_name)
            report = ValidationReport(
                source_name=source_name,
                execution_id=context.execution_id,
                total_rows=len(df),
            )

        # --- 2. Business rules -----------------------------------------------
        for rule_fn in get_rules(source_name):
            report.issues.extend(rule_fn(df, context))

        n_crit = len(report.critical_issues())
        n_warn = len(report.warnings())
        _LOG.info(
            "Validation complete: source=%s rows=%d critical=%d warnings=%d",
            source_name,
            len(df),
            n_crit,
            n_warn,
        )
        return report

    def check_and_raise(
        self,
        df: pd.DataFrame,
        source_name: str,
        context: ValidationContext,
    ) -> ValidationReport:
        """Like ``check()`` but raises ``CriticalValidationError`` on any CRITICAL issue.

        This is the entry-point used by pipeline jobs that must stop
        immediately when data quality is unacceptable (T057).
        """
        report = self.check(df, source_name, context)
        if report.has_critical_errors():
            first = report.critical_issues()[0]
            _LOG.error(
                "Critical validation error halts pipeline: %s", report.summary()
            )
            raise CriticalValidationError(
                message=(
                    f"Critical data-quality error in '{source_name}'. "
                    f"{report.summary()}"
                ),
                dataset=source_name,
                rule=first.rule,
                affected_records=first.affected_records,
            )
        return report

    def validate_all(
        self,
        datasets: dict[str, pd.DataFrame],
        context: ValidationContext,
    ) -> dict[str, ValidationReport]:
        """Validate every dataset in *datasets*, raising on the first critical error.

        Args:
            datasets: Mapping of ``source_name → DataFrame``.
            context: Shared execution context (``execution_id``, ``date_cutoff``).

        Returns:
            Mapping of ``source_name → ValidationReport`` for all sources.

        Raises:
            CriticalValidationError: On the first source that has a CRITICAL issue.
        """
        reports: dict[str, ValidationReport] = {}
        for source_name, df in datasets.items():
            src_ctx = ValidationContext(
                source_name=source_name,
                execution_id=context.execution_id,
                date_cutoff=context.date_cutoff,
            )
            reports[source_name] = self.check_and_raise(df, source_name, src_ctx)
        return reports
