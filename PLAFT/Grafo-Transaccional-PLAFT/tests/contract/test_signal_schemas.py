"""Pruebas de contrato para fuentes de señales de riesgo y catálogo documental (T028 supl.)."""

from __future__ import annotations

import pandas as pd

from graph_plaft.validation.contracts import validate_schema
from graph_plaft.validation.schemas import (
    ALERTAS_PLAFT_CONTRACT,
    CASOS_INVESTIGADOS_CONTRACT,
    CATALOGO_DOCUMENTAL_CONTRACT,
    LISTA_OBJETIVO_CONTRACT,
    PEP_CONTRACT,
    PERMISOS_ANALISTAS_CONTRACT,
    ROS_CONTRACT,
)


class TestAlertasPlaftContract:
    def _valid(self) -> dict:
        return {
            "alerta_id": "ALT-001",
            "cliente_id": "CLI-001",
            "tipo_alerta": "LAV-001",
            "fecha_alerta": "2026-07-01T10:00:00",
        }

    def test_fila_valida(self):
        df = pd.DataFrame([self._valid()])
        report = validate_schema(df, ALERTAS_PLAFT_CONTRACT)
        assert not report.has_critical_errors()

    def test_falta_alerta_id(self):
        row = {k: v for k, v in self._valid().items() if k != "alerta_id"}
        df = pd.DataFrame([row])
        report = validate_schema(df, ALERTAS_PLAFT_CONTRACT)
        assert report.has_critical_errors()

    def test_nulo_en_tipo_alerta(self):
        row = {**self._valid(), "tipo_alerta": None}
        df = pd.DataFrame([row])
        report = validate_schema(df, ALERTAS_PLAFT_CONTRACT)
        assert report.has_critical_errors()

    def test_duplicado_alerta_id(self):
        row = self._valid()
        df = pd.DataFrame([row, row.copy()])
        report = validate_schema(df, ALERTAS_PLAFT_CONTRACT)
        assert report.has_critical_errors()


class TestROSContract:
    def _valid(self) -> dict:
        return {
            "ros_id": "ROS-001",
            "cliente_id": "CLI-001",
            "fecha_reporte": "2026-06-15",
        }

    def test_fila_valida(self):
        df = pd.DataFrame([self._valid()])
        report = validate_schema(df, ROS_CONTRACT)
        assert not report.has_critical_errors()

    def test_falta_fecha_reporte(self):
        row = {"ros_id": "ROS-001", "cliente_id": "CLI-001"}
        df = pd.DataFrame([row])
        report = validate_schema(df, ROS_CONTRACT)
        assert report.has_critical_errors()


class TestPEPContract:
    def _valid(self) -> dict:
        return {
            "pep_id": "PEP-001",
            "cliente_id": "CLI-001",
            "vigente": True,
        }

    def test_fila_valida(self):
        df = pd.DataFrame([self._valid()])
        report = validate_schema(df, PEP_CONTRACT)
        assert not report.has_critical_errors()

    def test_nulo_en_vigente_es_critico(self):
        row = {**self._valid(), "vigente": None}
        df = pd.DataFrame([row])
        report = validate_schema(df, PEP_CONTRACT)
        assert report.has_critical_errors()


class TestCasosInvestigadosContract:
    def _valid(self) -> dict:
        return {
            "caso_id": "CASO-001",
            "cliente_id": "CLI-001",
            "fecha_apertura": "2026-01-15",
            "estado": "ABIERTO",
        }

    def test_fila_valida(self):
        df = pd.DataFrame([self._valid()])
        report = validate_schema(df, CASOS_INVESTIGADOS_CONTRACT)
        assert not report.has_critical_errors()

    def test_estado_invalido_es_warning(self):
        row = {**self._valid(), "estado": "PENDIENTE"}
        df = pd.DataFrame([row])
        report = validate_schema(df, CASOS_INVESTIGADOS_CONTRACT)
        assert any("allowed_values" in i.rule for i in report.warnings())


class TestCatalogoDocumentalContract:
    def _valid(self) -> dict:
        return {
            "documento_id": "DOC-001",
            "cliente_id": "CLI-001",
            "tipo_documental": "DNI",
            "sistema_origen": "KYC",
        }

    def test_fila_valida_sin_referencia_s3(self):
        """Documento sin referencia_s3 es válido."""
        row = {**self._valid(), "referencia_s3": None}
        df = pd.DataFrame([row])
        report = validate_schema(df, CATALOGO_DOCUMENTAL_CONTRACT)
        assert not report.has_critical_errors()

    def test_falta_sistema_origen(self):
        row = {k: v for k, v in self._valid().items() if k != "sistema_origen"}
        df = pd.DataFrame([row])
        report = validate_schema(df, CATALOGO_DOCUMENTAL_CONTRACT)
        assert report.has_critical_errors()


class TestListaObjetivoContract:
    def _valid(self) -> dict:
        return {
            "cliente_id": "CLI-001",
            "fecha_inclusion": "2026-07-01",
            "version_lista": "v-2026-07",
        }

    def test_fila_valida(self):
        df = pd.DataFrame([self._valid()])
        report = validate_schema(df, LISTA_OBJETIVO_CONTRACT)
        assert not report.has_critical_errors()


class TestPermisosAnalistasContract:
    def _valid(self) -> dict:
        return {
            "usuario_id": "analista-01",
            "cliente_id": "CLI-001",
            "nivel_acceso": "DATOS",
            "fecha_inicio": "2026-01-01",
            "vigente": True,
        }

    def test_fila_valida(self):
        df = pd.DataFrame([self._valid()])
        report = validate_schema(df, PERMISOS_ANALISTAS_CONTRACT)
        assert not report.has_critical_errors()

    def test_nivel_acceso_invalido(self):
        row = {**self._valid(), "nivel_acceso": "SUPERADMIN"}
        df = pd.DataFrame([row])
        report = validate_schema(df, PERMISOS_ANALISTAS_CONTRACT)
        assert any("allowed_values" in i.rule for i in report.warnings())


class TestValidateSchemaFunction:
    """Pruebas directas de validate_schema y ValidationReport."""

    def test_reporte_sin_errores(self):
        df = pd.DataFrame([{"cliente_id": "CLI-001"}])
        from graph_plaft.validation.schemas import CLIENTES_CONTRACT
        report = validate_schema(df, CLIENTES_CONTRACT, execution_id="exec-001")
        assert report.execution_id == "exec-001"
        assert report.total_rows == 1

    def test_no_modifica_dataframe_original(self):
        df = pd.DataFrame([{"cliente_id": "CLI-001", "tipo_persona": "NATURAL"}])
        cols_before = list(df.columns)
        from graph_plaft.validation.schemas import CLIENTES_CONTRACT
        validate_schema(df, CLIENTES_CONTRACT)
        assert list(df.columns) == cols_before
