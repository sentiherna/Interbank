"""Pruebas de contrato para esquemas de relaciones del subgrafo (T030)."""

from __future__ import annotations

import pytest

from graph_plaft.graph.edge_schemas import (
    EsTitularDeEdge,
    TieneAlertaEdge,
    TransfiereAEdge,
)
from graph_plaft.observability.errors import GraphBuildError

_TRACEABILITY = {
    "dataset_origen": "transferencias",
    "registro_fuente": "TX-001",
    "graph_version": "v-test",
    "run_id": "run-test",
}


class TestTransfiereAEdge:
    def _valid(self, **kwargs) -> TransfiereAEdge:
        return TransfiereAEdge(
            edge_id="e-tx-001",
            source_id="n-cta-001",
            target_id="n-cta-002",
            transaction_id="TX-001",
            cuenta_origen="CTA-001",
            cuenta_destino="CTA-002",
            fecha_hora="2026-07-01T10:00:00",
            monto=500.0,
            moneda="PEN",
            estado="EJECUTADA",
            **_TRACEABILITY,
            **kwargs,
        )

    def test_arista_valida(self):
        edge = self._valid()
        edge.validate()
        assert edge.edge_type == "transfiere_a"
        assert edge.directed is True

    def test_sin_transaction_id_lanza_error(self):
        edge = self._valid()
        edge.transaction_id = ""
        with pytest.raises(GraphBuildError, match="transaction_id"):
            edge.validate()

    def test_sin_cuenta_origen_lanza_error(self):
        edge = self._valid()
        edge.cuenta_origen = ""
        with pytest.raises(GraphBuildError, match="cuenta_origen"):
            edge.validate()

    def test_sin_fecha_hora_lanza_error(self):
        edge = self._valid()
        edge.fecha_hora = ""
        with pytest.raises(GraphBuildError, match="fecha_hora"):
            edge.validate()

    def test_sin_moneda_lanza_error(self):
        edge = self._valid()
        edge.moneda = ""
        with pytest.raises(GraphBuildError, match="moneda"):
            edge.validate()

    def test_cliente_origen_puede_ser_null(self):
        """La resolución de cliente_origen puede ser null (ADR-001)."""
        edge = self._valid(cliente_origen=None)
        edge.validate()  # no debe lanzar

    def test_trazabilidad_faltante_lanza_error(self):
        edge = self._valid()
        edge.dataset_origen = ""
        with pytest.raises(GraphBuildError):
            edge.validate()

    def test_to_dict_contiene_transaction_id(self):
        edge = self._valid()
        d = edge.to_dict()
        assert "transaction_id" in d
        assert d["transaction_id"] == "TX-001"


class TestEsTitularDeEdge:
    def test_arista_valida(self):
        edge = EsTitularDeEdge(
            edge_id="e-tit-001",
            source_id="n-cli-001",
            target_id="n-cta-001",
            tipo_titularidad="Principal",
            dataset_origen="titularidades",
            registro_fuente="TIT-001",
            graph_version="v-test",
            run_id="run-test",
        )
        edge.validate()
        assert edge.edge_type == "es_titular_de"
        assert edge.directed is True


class TestTieneAlertaEdge:
    def test_arista_valida(self):
        edge = TieneAlertaEdge(
            edge_id="e-alt-001",
            source_id="n-cli-001",
            target_id="n-alt-001",
            dataset_origen="alertas_plaft",
            registro_fuente="ALT-001",
            graph_version="v-test",
            run_id="run-test",
        )
        edge.validate()
        assert edge.edge_type == "tiene_alerta"
