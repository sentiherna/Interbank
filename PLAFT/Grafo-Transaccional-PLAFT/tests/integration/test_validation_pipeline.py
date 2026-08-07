"""Integration tests: full validation pipeline over synthetic datasets (T060).

This test generates the synthetic Parquet files in a temporary directory,
loads each one through ``load_dataset + PandasEngine``, runs ``QualityChecker``
and verifies the expected quality-report outcomes against the known properties
of the Phase 2 synthetic data.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from graph_plaft.config.settings import Settings, StorageConfig, load_settings
from graph_plaft.ingestion.loaders import DatasetMetadata, load_dataset
from graph_plaft.ingestion.pandas_engine import PandasEngine
from graph_plaft.ingestion.registry import DatasetRegistry
from graph_plaft.validation.quality import QualityChecker
from graph_plaft.validation.rules import ValidationContext

ROOT = Path(__file__).parent.parent.parent
GENERATE_SCRIPT = ROOT / "scripts" / "generate_synthetic.py"
CUTOFF = pd.Timestamp("2026-06-30")


@pytest.fixture(scope="module")
def synthetic_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Generate synthetic Parquet files and return the output directory."""
    out = tmp_path_factory.mktemp("synthetic_integration")
    subprocess.run(  # noqa: S603
        [sys.executable, str(GENERATE_SCRIPT), "--seed", "42", "--output-dir", str(out)],
        check=True,
        capture_output=True,
    )
    return out


@pytest.fixture(scope="module")
def engine() -> PandasEngine:
    return PandasEngine()


@pytest.fixture(scope="module")
def settings(synthetic_dir: Path) -> Settings:
    """Load local.yaml but override storage.base_path to the synthetic dir."""
    base_cfg = load_settings(ROOT / "config" / "local.yaml")
    # Rebuild with the synthetic_dir as base_path
    return Settings(
        environment=base_cfg.environment,
        data_engine=base_cfg.data_engine,
        graph_engine=base_cfg.graph_engine,
        log_level=base_cfg.log_level,
        log_format=base_cfg.log_format,
        storage=StorageConfig(
            base_path=str(synthetic_dir),
            format="parquet",
        ),
        mlflow=base_cfg.mlflow,
        feature_store=base_cfg.feature_store,
        glue=base_cfg.glue,
        run_defaults=base_cfg.run_defaults,
    )


# ---------------------------------------------------------------------------
# Dataset loading
# ---------------------------------------------------------------------------


class TestLoadDataset:
    def test_load_clientes_returns_dataframe_and_metadata(
        self,
        engine: PandasEngine,
        settings: Settings,
    ) -> None:
        df, meta = load_dataset("clientes", engine, settings, "exec-intg-001")
        assert isinstance(df, pd.DataFrame)
        assert isinstance(meta, DatasetMetadata)
        assert meta.row_count == 10
        assert meta.source_name == "clientes"
        assert meta.checksum  # non-empty

    def test_registry_accumulates_entries(
        self,
        engine: PandasEngine,
        settings: Settings,
    ) -> None:
        registry = DatasetRegistry()
        for source in ("clientes", "cuentas", "transferencias"):
            _, meta = load_dataset(source, engine, settings, "exec-intg-001")
            registry.register(meta)
        assert len(registry) == 3
        assert "transferencias" in registry.all_sources()

    def test_missing_source_raises_ingestion_error(
        self,
        engine: PandasEngine,
        settings: Settings,
    ) -> None:
        from graph_plaft.observability.errors import IngestionError

        with pytest.raises(IngestionError, match="does_not_exist"):
            load_dataset("does_not_exist", engine, settings, "x")


# ---------------------------------------------------------------------------
# QualityChecker over synthetic datasets
# ---------------------------------------------------------------------------


ALL_SOURCES = [
    "clientes",
    "lista_objetivo",
    "cuentas",
    "titularidades",
    "productos",
    "transferencias",
    "alertas_plaft",
    "ros",
    "pep",
    "casos_investigados",
    "catalogo_documental",
    "permisos_analistas",
]


class TestValidationPipeline:
    @pytest.fixture(scope="class")
    @classmethod
    def loaded_datasets(
        cls,
        engine: PandasEngine,
        settings: Settings,
    ) -> dict[str, pd.DataFrame]:
        return {
            src: load_dataset(src, engine, settings, "exec-intg-001")[0]
            for src in ALL_SOURCES
        }

    def test_clientes_passes_without_critical_errors(
        self,
        loaded_datasets: dict[str, pd.DataFrame],
    ) -> None:
        ctx = ValidationContext("clientes", "exec-intg-001", CUTOFF)
        report = QualityChecker().check(loaded_datasets["clientes"], "clientes", ctx)
        assert not report.has_critical_errors(), report.summary()

    def test_transferencias_has_temporal_violation_warning(
        self,
        loaded_datasets: dict[str, pd.DataFrame],
    ) -> None:
        # TX-017 is post-cutoff → the temporal rule fires as CRITICAL
        ctx = ValidationContext("transferencias", "exec-intg-001", CUTOFF)
        report = QualityChecker().check(
            loaded_datasets["transferencias"], "transferencias", ctx
        )
        temporal_issues = [
            i for i in report.issues if "temporal" in i.rule
        ]
        assert len(temporal_issues) >= 1
        assert temporal_issues[0].affected_records == 1

    def test_transferencias_has_monto_warning_for_zero_monto(
        self,
        loaded_datasets: dict[str, pd.DataFrame],
    ) -> None:
        # All synthetic EJECUTADA transactions have monto > 0 → no warning
        ctx = ValidationContext("transferencias", "exec-intg-001", CUTOFF)
        report = QualityChecker().check(
            loaded_datasets["transferencias"], "transferencias", ctx
        )
        monto_issues = [i for i in report.issues if "monto" in i.rule]
        assert monto_issues == []  # all positive in synthetic data

    def test_no_source_has_pk_duplicates(
        self,
        loaded_datasets: dict[str, pd.DataFrame],
    ) -> None:
        checker = QualityChecker()
        for source_name, df in loaded_datasets.items():
            ctx = ValidationContext(source_name, "exec-intg-001")
            report = checker.check(df, source_name, ctx)
            pk_issues = [i for i in report.issues if "pk_unique" in i.rule]
            assert pk_issues == [], (
                f"{source_name}: unexpected PK duplicates: "
                + ", ".join(str(i) for i in pk_issues)
            )

    def test_registry_to_dataframe_is_serialisable(
        self,
        engine: PandasEngine,
        settings: Settings,
    ) -> None:
        registry = DatasetRegistry()
        for source in ("clientes", "cuentas"):
            _, meta = load_dataset(source, engine, settings, "exec-intg-002")
            registry.register(meta)
        df = registry.to_dataframe()
        assert set(df.columns) >= {"source_name", "row_count", "checksum"}
        assert len(df) == 2
