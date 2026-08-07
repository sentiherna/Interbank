"""Pruebas de contrato para esquemas de variables estructurales y auditoría (T031)."""

from __future__ import annotations

from datetime import date

import pytest

from graph_plaft.audit.audit_schema import AuditRecord
from graph_plaft.features.variable_schema import VariableEstructural
from graph_plaft.observability.errors import GraphBuildError
from graph_plaft.observability.run_manifest import RunManifest

# ---------------------------------------------------------------------------
# VariableEstructural
# ---------------------------------------------------------------------------


class TestVariableEstructural:
    def _valid(self, **kwargs) -> VariableEstructural:
        return VariableEstructural(
            cliente_id="CLI-001",
            variable_nombre="pagerank",
            categoria="centralidad",
            valor=0.042,
            graph_version="v-test",
            run_id="run-test",
            **kwargs,
        )

    def test_variable_valida_con_valor(self):
        var = self._valid()
        assert var.valor == pytest.approx(0.042)

    def test_variable_valida_con_nulo_documentado(self):
        var = VariableEstructural(
            cliente_id="CLI-001",
            variable_nombre="distancia_min_ros",
            categoria="riesgo_propagado",
            valor=None,
            valor_nulo_razon="no_alcanzable",
            graph_version="v-test",
            run_id="run-test",
        )
        assert var.valor is None
        assert var.valor_nulo_razon == "no_alcanzable"

    def test_valor_y_razon_ambos_vacios_lanza_error(self):
        with pytest.raises(GraphBuildError, match="valor_nulo_razon"):
            VariableEstructural(
                cliente_id="CLI-001",
                variable_nombre="pagerank",
                categoria="centralidad",
                valor=None,
                valor_nulo_razon="",  # ambos vacíos
                graph_version="v-test",
                run_id="run-test",
            )

    def test_categoria_invalida_lanza_error(self):
        with pytest.raises(GraphBuildError, match="categor"):
            VariableEstructural(
                cliente_id="CLI-001",
                variable_nombre="test_var",
                categoria="inventada",  # type: ignore[arg-type]
                valor=1.0,
                graph_version="v-test",
                run_id="run-test",
            )

    def test_ocho_categorias_validas(self):
        from graph_plaft.config.schemas import VARIABLE_CATEGORIES
        for cat in VARIABLE_CATEGORIES:
            var = VariableEstructural(
                cliente_id="CLI-001",
                variable_nombre=f"var_{cat}",
                categoria=cat,  # type: ignore[arg-type]
                valor=0.0,
                graph_version="v-test",
                run_id="run-test",
            )
            assert var.categoria == cat

    def test_to_dict_contiene_campos_obligatorios(self):
        var = self._valid(
            ventana_inicio=date(2026, 1, 1),
            ventana_fin=date(2026, 7, 31),
        )
        d = var.to_dict()
        assert d["cliente_id"] == "CLI-001"
        assert d["ventana_inicio"] == "2026-01-01"
        assert d["ventana_fin"] == "2026-07-31"

    def test_nulos_documentados_tienen_razon(self):
        """Clientes sin actividad deben tener valor=0 o valor_nulo_razon documentado."""
        var = VariableEstructural(
            cliente_id="CLI-AISLADO",
            variable_nombre="monto_enviado_total",
            categoria="flujo_dinero",
            valor=0.0,  # 0 es valor válido, no null
            graph_version="v-test",
            run_id="run-test",
        )
        assert var.valor == 0.0


# ---------------------------------------------------------------------------
# AuditRecord
# ---------------------------------------------------------------------------


class TestAuditRecord:
    def _valid(self, resultado: str = "ok", **kwargs) -> AuditRecord:
        return AuditRecord(
            audit_id="AUD-001",
            timestamp="2026-08-06T10:00:00Z",
            usuario_id="analista-01",
            accion="search",
            resultado=resultado,
            **kwargs,
        )

    def test_registro_valido(self):
        rec = self._valid()
        assert rec.audit_id == "AUD-001"

    def test_registro_denegado(self):
        rec = self._valid(resultado="denied", cliente_id="CLI-999")
        assert rec.resultado == "denied"

    def test_audit_id_obligatorio(self):
        with pytest.raises(GraphBuildError, match="audit_id"):
            AuditRecord(
                audit_id="",
                timestamp="2026-08-06T10:00:00Z",
                usuario_id="analista-01",
                accion="search",
                resultado="ok",
            )

    def test_resultado_invalido(self):
        with pytest.raises(GraphBuildError, match="resultado"):
            AuditRecord(
                audit_id="AUD-001",
                timestamp="2026-08-06T10:00:00Z",
                usuario_id="analista-01",
                accion="search",
                resultado="maybe",  # inválido
            )

    def test_to_dict_contiene_todos_los_campos(self):
        rec = self._valid(
            cliente_id="CLI-001",
            documentos_consultados=["DOC-001"],
        )
        d = rec.to_dict()
        assert d["audit_id"] == "AUD-001"
        assert "documentos_consultados" in d
        assert "DOC-001" in d["documentos_consultados"]


# ---------------------------------------------------------------------------
# RunManifest
# ---------------------------------------------------------------------------


class TestRunManifest:
    def _valid(self) -> RunManifest:
        return RunManifest(
            run_id="run-001",
            created_at="2026-08-06T10:00:00Z",
            status="completed",
            code_version="1.0.0",
            date_cutoff="2026-07-31",
        )

    def test_manifest_valido(self):
        m = self._valid()
        missing = m.validate_complete()
        assert missing == [], f"Campos faltantes: {missing}"

    def test_manifest_incompleto_detecta_faltantes(self):
        m = RunManifest(
            run_id="run-002",
            created_at="",  # vacío
            status="running",
        )
        missing = m.validate_complete()
        assert "created_at" in missing

    def test_serializa_y_deserializa(self, tmp_path):
        m = self._valid()
        path = tmp_path / "run_manifest.json"
        m.save(path)
        loaded = RunManifest.load(path)
        assert loaded.run_id == "run-001"
        assert loaded.status == "completed"
        assert loaded.code_version == "1.0.0"

    def test_to_json_es_json_valido(self):
        import json
        m = self._valid()
        j = m.to_json()
        parsed = json.loads(j)
        assert parsed["run_id"] == "run-001"
