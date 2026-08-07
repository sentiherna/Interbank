"""Pruebas de contrato para esquemas de nodos del subgrafo (T029)."""

from __future__ import annotations

import pytest

from graph_plaft.graph.node_schemas import (
    AlertaPLAFTNode,
    ClienteNode,
    CuentaNode,
    DocumentoNode,
)
from graph_plaft.observability.errors import GraphBuildError

_TRACEABILITY = {
    "dataset_origen": "clientes",
    "registro_fuente": "CLI-001",
    "graph_version": "v-test",
    "run_id": "run-test",
}


class TestClienteNode:
    def _base(
        self, es_cliente_objetivo: bool = True, es_contraparte: bool = False, **kwargs
    ) -> ClienteNode:
        return ClienteNode(
            node_id="n-cli-001",
            cliente_id="CLI-001",
            es_cliente_objetivo=es_cliente_objetivo,
            es_contraparte=es_contraparte,
            **_TRACEABILITY,
            **kwargs,
        )

    def test_nodo_valido_objetivo(self):
        node = self._base()
        node.validate()  # no debe lanzar

    def test_nodo_valido_ambos_roles(self):
        node = self._base(es_cliente_objetivo=True, es_contraparte=True)
        node.validate()

    def test_nodo_sin_rol_lanza_error(self):
        node = self._base(es_cliente_objetivo=False, es_contraparte=False)
        with pytest.raises(GraphBuildError, match="rol"):
            node.validate()

    def test_trazabilidad_faltante_lanza_error(self):
        node = ClienteNode(
            node_id="n-cli-002",
            cliente_id="CLI-002",
            es_cliente_objetivo=True,
            dataset_origen="",  # vacío a propósito
            registro_fuente="CLI-002",
            graph_version="v-test",
            run_id="run-test",
        )
        with pytest.raises(GraphBuildError):
            node.validate()

    def test_node_type_es_cliente(self):
        node = self._base()
        assert node.node_type == "cliente"

    def test_to_dict_contiene_campos_obligatorios(self):
        node = self._base()
        d = node.to_dict()
        for col in ("node_id", "node_type", "dataset_origen", "registro_fuente"):
            assert col in d


class TestCuentaNode:
    def test_nodo_valido(self):
        node = CuentaNode(
            node_id="n-cta-001",
            cuenta_id="CTA-001",
            **_TRACEABILITY,
        )
        node.validate()
        assert node.node_type == "cuenta"


class TestDocumentoNode:
    def test_documento_sin_referencia_s3_valido(self):
        """Un documento sin referencia_s3 es válido (referencia puede ser null)."""
        node = DocumentoNode(
            node_id="n-doc-001",
            documento_id="DOC-001",
            cliente_id="CLI-001",
            tipo_documental="DNI",
            sistema_origen="KYC",
            referencia_s3=None,  # null es válido
            **_TRACEABILITY,
        )
        node.validate()
        assert node.node_type == "documento"
        assert node.referencia_s3 is None


class TestAlertaPLAFTNode:
    def test_alerta_valida(self):
        node = AlertaPLAFTNode(
            node_id="n-alt-001",
            alerta_id="ALT-001",
            cliente_id="CLI-001",
            tipo_alerta="LAV-001",
            fecha_alerta="2026-07-01T10:00:00",
            **_TRACEABILITY,
        )
        node.validate()
        assert node.node_type == "alerta_plaft"
