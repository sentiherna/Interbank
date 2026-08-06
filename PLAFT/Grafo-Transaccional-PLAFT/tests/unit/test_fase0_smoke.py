"""Tests de smoke para la Fase 0 — verifica que la infraestructura base funciona."""

from __future__ import annotations

import pytest

from graph_plaft.config.schemas import (
    SIGNAL_TYPES,
    TRACEABILITY_COLUMNS,
    VARIABLE_CATEGORIES,
)
from graph_plaft.config.settings import load_settings
from graph_plaft.observability.errors import (
    AccessDeniedError,
    CriticalValidationError,
    VersionNotFoundError,
)
from graph_plaft.observability.run_id import (
    generate_graph_version,
    generate_run_id,
    generate_variables_version,
)


class TestConfigSettings:
    """Verifica que la configuración local carga correctamente."""

    def test_carga_config_local(self, synthetic_config):
        assert synthetic_config.environment == "local"
        assert synthetic_config.data_engine == "pandas"
        assert synthetic_config.graph_engine == "networkx"

    def test_is_local_true_en_entorno_local(self, synthetic_config):
        assert synthetic_config.is_local() is True
        assert synthetic_config.is_aws() is False

    def test_signal_weights_valores_por_defecto(self, synthetic_config):
        w = synthetic_config.run_defaults.signal_weights
        assert w.ros == 1.0
        assert w.alerta == 0.7
        assert w.pep == 0.3
        assert w.caso == 0.9

    def test_config_no_encontrada_lanza_error(self):
        with pytest.raises(FileNotFoundError):
            load_settings("config/no_existe.yaml")


class TestSchemaConstants:
    """Verifica que las constantes del dominio están completas."""

    def test_signal_types_completos(self):
        assert set(SIGNAL_TYPES) == {"alerta", "ros", "pep", "caso"}

    def test_variable_categories_completas(self):
        assert len(VARIABLE_CATEGORIES) == 8
        assert "riesgo_vecinos" in VARIABLE_CATEGORIES
        assert "riesgo_propagado" in VARIABLE_CATEGORIES

    def test_traceability_columns_presentes(self):
        for col in ("dataset_origen", "registro_fuente", "run_id", "graph_version"):
            assert col in TRACEABILITY_COLUMNS


class TestRunId:
    """Verifica la generación de identificadores de ejecución."""

    def test_run_id_sin_semilla_es_unico(self):
        id1 = generate_run_id()
        id2 = generate_run_id()
        assert id1 != id2

    def test_run_id_con_semilla_es_determinista(self):
        id1 = generate_run_id(seed="test")
        id2 = generate_run_id(seed="test")
        assert id1 == id2

    def test_graph_version_determinista(self):
        v1 = generate_graph_version("run-1", "2026-07-31", 1)
        v2 = generate_graph_version("run-1", "2026-07-31", 1)
        assert v1 == v2
        assert v1.startswith("v-")

    def test_graph_version_cambia_con_profundidad(self):
        v1 = generate_graph_version("run-1", "2026-07-31", 1)
        v2 = generate_graph_version("run-1", "2026-07-31", 2)
        assert v1 != v2

    def test_variables_version_determinista(self):
        gv = generate_graph_version("run-1", "2026-07-31", 1)
        vv1 = generate_variables_version(gv, "run-1")
        vv2 = generate_variables_version(gv, "run-1")
        assert vv1 == vv2
        assert vv1.startswith("vars-")


class TestErrors:
    """Verifica que las excepciones del dominio tienen el comportamiento esperado."""

    def test_critical_validation_error_incluye_contexto(self):
        err = CriticalValidationError(
            "campo nulo",
            dataset="clientes",
            rule="cliente_id_not_null",
            affected_records=5,
        )
        msg = str(err)
        assert "clientes" in msg
        assert "cliente_id_not_null" in msg
        assert "5" in msg

    def test_access_denied_error_incluye_contexto(self):
        err = AccessDeniedError(
            user_id="analista-01",
            resource_type="cliente",
            resource_id="CLI-001",
        )
        msg = str(err)
        assert "analista-01" in msg
        assert "CLI-001" in msg

    def test_version_not_found_error(self):
        err = VersionNotFoundError("v-abc123", artifact_type="graph")
        assert "v-abc123" in str(err)
        assert err.version == "v-abc123"
